"""Secrets management module prepared for HashiCorp Vault or AWS Secrets Manager."""
import logging
import os
from typing import Optional, Dict, Any, Protocol
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class SecretsProvider(Protocol):
    """Protocol for secrets management providers."""
    
    async def get_secret(self, key: str) -> Optional[str]:
        """Get a secret value by key."""
        ...
    
    async def set_secret(self, key: str, value: str) -> bool:
        """Set a secret value."""
        ...
    
    async def delete_secret(self, key: str) -> bool:
        """Delete a secret."""
        ...


class EnvironmentSecretsProvider:
    """Environment variables secrets provider (development/fallback)."""
    
    async def get_secret(self, key: str) -> Optional[str]:
        """Get secret from environment variables."""
        value = os.getenv(key)
        if value:
            logger.debug(f"Retrieved secret '{key}' from environment")
        else:
            logger.warning(f"Secret '{key}' not found in environment")
        return value
    
    async def set_secret(self, key: str, value: str) -> bool:
        """Set secret in environment (not persistent)."""
        os.environ[key] = value
        logger.debug(f"Set secret '{key}' in environment")
        return True
    
    async def delete_secret(self, key: str) -> bool:
        """Delete secret from environment."""
        if key in os.environ:
            del os.environ[key]
            logger.debug(f"Deleted secret '{key}' from environment")
            return True
        return False


class VaultSecretsProvider:
    """HashiCorp Vault secrets provider (production)."""
    
    def __init__(self, vault_url: str, vault_token: str, mount_point: str = "secret"):
        self.vault_url = vault_url
        self.vault_token = vault_token
        self.mount_point = mount_point
        self._client = None
    
    async def _get_client(self):
        """Get Vault client (lazy initialization)."""
        if self._client is None:
            try:
                import hvac
                self._client = hvac.Client(
                    url=self.vault_url,
                    token=self.vault_token
                )
                if not self._client.is_authenticated():
                    raise Exception("Vault authentication failed")
                logger.info("Vault client initialized and authenticated")
            except ImportError:
                logger.error("hvac library not installed. Install with: pip install hvac")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize Vault client: {e}")
                raise
        return self._client
    
    async def get_secret(self, key: str) -> Optional[str]:
        """Get secret from HashiCorp Vault."""
        try:
            client = await self._get_client()
            response = client.secrets.kv.v2.read_secret_version(
                path=key,
                mount_point=self.mount_point
            )
            value = response["data"]["data"].get("value")
            if value:
                logger.debug(f"Retrieved secret '{key}' from Vault")
            else:
                logger.warning(f"Secret '{key}' not found in Vault")
            return value
        except Exception as e:
            logger.error(f"Failed to get secret '{key}' from Vault: {e}")
            return None
    
    async def set_secret(self, key: str, value: str) -> bool:
        """Set secret in HashiCorp Vault."""
        try:
            client = await self._get_client()
            client.secrets.kv.v2.create_or_update_secret(
                path=key,
                secret={"value": value},
                mount_point=self.mount_point
            )
            logger.info(f"Set secret '{key}' in Vault")
            return True
        except Exception as e:
            logger.error(f"Failed to set secret '{key}' in Vault: {e}")
            return False
    
    async def delete_secret(self, key: str) -> bool:
        """Delete secret from HashiCorp Vault."""
        try:
            client = await self._get_client()
            client.secrets.kv.v2.delete_latest_version_of_secret(
                path=key,
                mount_point=self.mount_point
            )
            logger.info(f"Deleted secret '{key}' from Vault")
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret '{key}' from Vault: {e}")
            return False


class AWSSecretsProvider:
    """AWS Secrets Manager provider (production)."""
    
    def __init__(self, region_name: str = "us-east-1"):
        self.region_name = region_name
        self._client = None
    
    async def _get_client(self):
        """Get AWS Secrets Manager client (lazy initialization)."""
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client(
                    'secretsmanager',
                    region_name=self.region_name
                )
                logger.info("AWS Secrets Manager client initialized")
            except ImportError:
                logger.error("boto3 library not installed. Install with: pip install boto3")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize AWS Secrets Manager client: {e}")
                raise
        return self._client
    
    async def get_secret(self, key: str) -> Optional[str]:
        """Get secret from AWS Secrets Manager."""
        try:
            client = await self._get_client()
            response = client.get_secret_value(SecretId=key)
            value = response.get('SecretString')
            if value:
                logger.debug(f"Retrieved secret '{key}' from AWS Secrets Manager")
            else:
                logger.warning(f"Secret '{key}' not found in AWS Secrets Manager")
            return value
        except Exception as e:
            logger.error(f"Failed to get secret '{key}' from AWS Secrets Manager: {e}")
            return None
    
    async def set_secret(self, key: str, value: str) -> bool:
        """Set secret in AWS Secrets Manager."""
        try:
            client = await self._get_client()
            try:
                # Try to update first
                client.update_secret(
                    SecretId=key,
                    SecretString=value
                )
            except client.exceptions.ResourceNotFoundException:
                # Create if doesn't exist
                client.create_secret(
                    Name=key,
                    SecretString=value
                )
            logger.info(f"Set secret '{key}' in AWS Secrets Manager")
            return True
        except Exception as e:
            logger.error(f"Failed to set secret '{key}' in AWS Secrets Manager: {e}")
            return False
    
    async def delete_secret(self, key: str) -> bool:
        """Delete secret from AWS Secrets Manager."""
        try:
            client = await self._get_client()
            client.delete_secret(
                SecretId=key,
                ForceDeleteWithoutRecovery=True
            )
            logger.info(f"Deleted secret '{key}' from AWS Secrets Manager")
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret '{key}' from AWS Secrets Manager: {e}")
            return False


class SecretsManager:
    """Main secrets manager with multiple provider support."""
    
    def __init__(self, provider: SecretsProvider):
        self.provider = provider
        self._cache: Dict[str, str] = {}
    
    async def get_secret(self, key: str, use_cache: bool = True) -> Optional[str]:
        """Get secret with optional caching."""
        if use_cache and key in self._cache:
            logger.debug(f"Retrieved secret '{key}' from cache")
            return self._cache[key]
        
        value = await self.provider.get_secret(key)
        if value and use_cache:
            self._cache[key] = value
        
        return value
    
    async def set_secret(self, key: str, value: str) -> bool:
        """Set secret and update cache."""
        success = await self.provider.set_secret(key, value)
        if success:
            self._cache[key] = value
        return success
    
    async def delete_secret(self, key: str) -> bool:
        """Delete secret and remove from cache."""
        success = await self.provider.delete_secret(key)
        if success and key in self._cache:
            del self._cache[key]
        return success
    
    def clear_cache(self):
        """Clear the secrets cache."""
        self._cache.clear()
        logger.debug("Secrets cache cleared")


# Global secrets manager instance
_secrets_manager: Optional[SecretsManager] = None


def init_secrets_manager(provider_type: str = "environment", **kwargs) -> SecretsManager:
    """Initialize the global secrets manager."""
    global _secrets_manager
    
    providers = {
        "environment": EnvironmentSecretsProvider,
        "vault": VaultSecretsProvider,
        "aws": AWSSecretsProvider,
    }
    
    if provider_type not in providers:
        raise ValueError(f"Unknown provider type: {provider_type}")
    
    provider_class = providers[provider_type]
    provider = provider_class(**kwargs)
    
    _secrets_manager = SecretsManager(provider)
    
    logger.info(f"Secrets manager initialized with provider: {provider_type}")
    return _secrets_manager


def get_secrets_manager() -> SecretsManager:
    """Get the global secrets manager instance."""
    if _secrets_manager is None:
        # Fallback to environment provider
        return init_secrets_manager("environment")
    return _secrets_manager


# Convenience functions
async def get_secret(key: str) -> Optional[str]:
    """Get a secret using the global secrets manager."""
    manager = get_secrets_manager()
    return await manager.get_secret(key)


async def set_secret(key: str, value: str) -> bool:
    """Set a secret using the global secrets manager."""
    manager = get_secrets_manager()
    return await manager.set_secret(key, value)
"""Enhanced configuration module with secrets management support."""
import os
from functools import lru_cache
from typing import List, Optional, Union

from dotenv import load_dotenv
from pydantic import BaseSettings, Field, validator
from pydantic.networks import AnyUrl

# Load environment variables from .env file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOTENV_PATH = os.path.join(BASE_DIR, os.pardir, os.pardir, os.pardir, ".env")
load_dotenv(DOTENV_PATH)


class Settings(BaseSettings):
    """Enhanced application settings with comprehensive configuration management."""
    
    # ---------------------
    # General Settings
    # ---------------------
    APP_NAME: str = Field(
        default="psychic_tribble",
        description="Human-friendly name of the application"
    )
    ENV: str = Field(
        default="development",
        description="Environment: development, testing, production"
    )
    DEBUG: bool = Field(
        default=True,
        description="Enable debug mode"
    )
    
    # ---------------------
    # Security Settings
    # ---------------------
    SECRET_KEY: str = Field(
        default="development-secret-key-change-in-production-immediately",
        min_length=32,
        description="Cryptographic key for signing tokens (min 32 chars)"
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="Algorithm used to sign JWT tokens"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,  # Shorter for security
        ge=5,
        le=1440,
        description="Duration before access tokens expire (5-1440 minutes)"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Duration before refresh tokens expire (1-30 days)"
    )
    
    # ---------------------
    # Database Settings
    # ---------------------
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./development.db",
        description="Database connection URL"
    )
    DATABASE_POOL_SIZE: int = Field(
        default=20,
        ge=5,
        le=100,
        description="Database connection pool size"
    )
    DATABASE_MAX_OVERFLOW: int = Field(
        default=30,
        ge=0,
        le=100,
        description="Maximum overflow connections beyond pool size"
    )
    DATABASE_POOL_TIMEOUT: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Timeout when getting connection from pool (seconds)"
    )
    
    # ---------------------
    # CORS Settings
    # ---------------------
    allowed_cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    
    @validator('allowed_cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string if needed."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    # ---------------------
    # Rate Limiting Settings
    # ---------------------
    default_rate_limit: str = Field(
        default="100/minute",
        description="Default rate limit"
    )
    auth_rate_limit: str = Field(
        default="5/minute",
        description="Rate limit for authentication endpoints"
    )
    
    # ---------------------
    # HTTPS/Security Settings
    # ---------------------
    enable_https_redirect: bool = Field(
        default=False,
        description="Enable HTTPS redirect"
    )
    
    # ---------------------
    # Redis Settings
    # ---------------------
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for caching and rate limiting"
    )
    
    # ---------------------
    # Secrets Management Settings
    # ---------------------
    SECRETS_PROVIDER: str = Field(
        default="environment",
        description="Secrets provider: environment, vault, aws"
    )
    VAULT_URL: Optional[str] = Field(
        default=None,
        description="HashiCorp Vault URL"
    )
    VAULT_TOKEN: Optional[str] = Field(
        default=None,
        description="HashiCorp Vault token"
    )
    AWS_REGION: str = Field(
        default="us-east-1",
        description="AWS region for Secrets Manager"
    )
    
    # ---------------------
    # Monitoring Settings
    # ---------------------
    ENABLE_METRICS: bool = Field(
        default=True,
        description="Enable metrics collection"
    )
    METRICS_PATH: str = Field(
        default="/metrics",
        description="Metrics endpoint path"
    )
    
    # ---------------------
    # Email Settings (for notifications)
    # ---------------------
    SMTP_HOST: Optional[str] = Field(
        default=None,
        description="SMTP server host"
    )
    SMTP_PORT: int = Field(
        default=587,
        description="SMTP server port"
    )
    SMTP_USERNAME: Optional[str] = Field(
        default=None,
        description="SMTP username"
    )
    SMTP_PASSWORD: Optional[str] = Field(
        default=None,
        description="SMTP password"
    )
    SMTP_FROM_EMAIL: Optional[str] = Field(
        default=None,
        description="From email address"
    )
    
    # ---------------------
    # Feature Flags
    # ---------------------
    ENABLE_API_DOCS: Optional[bool] = Field(
        default=None,
        description="Enable API documentation (None = auto-detect from ENV)"
    )
    ENABLE_STRUCTURED_LOGGING: bool = Field(
        default=True,
        description="Enable structured JSON logging"
    )
    
    # ---------------------
    # Validation
    # ---------------------
    @validator('ENV')
    def validate_environment(cls, v):
        """Validate environment value."""
        allowed_envs = ['development', 'testing', 'staging', 'production']
        if v not in allowed_envs:
            raise ValueError(f'ENV must be one of: {allowed_envs}')
        return v
    
    @validator('SECRET_KEY')
    def validate_secret_key(cls, v, values):
        """Validate secret key strength."""
        if values.get('ENV') == 'production' and v == 'development-secret-key-change-in-production-immediately':
            raise ValueError('Must set a secure SECRET_KEY in production')
        return v
    
    @validator('DATABASE_URL')
    def validate_database_url(cls, v, values):
        """Validate database URL format."""
        if not v:
            raise ValueError('DATABASE_URL is required')
        
        # Add async support if missing
        if v.startswith('sqlite:///') and '+aiosqlite' not in v:
            v = v.replace('sqlite:///', 'sqlite+aiosqlite:///')
        elif v.startswith('postgresql://') and '+asyncpg' not in v:
            v = v.replace('postgresql://', 'postgresql+asyncpg://')
        
        return v
    
    # ---------------------
    # Property Methods
    # ---------------------
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENV == 'production'
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENV == 'development'
    
    @property
    def should_enable_docs(self) -> bool:
        """Determine if API docs should be enabled."""
        if self.ENABLE_API_DOCS is not None:
            return self.ENABLE_API_DOCS
        return not self.is_production
    
    class Config:
        env_file = DOTENV_PATH
        env_file_encoding = "utf-8"
        case_sensitive = True
        
        # Allow extra fields for future extensibility
        extra = "ignore"


class DevelopmentSettings(Settings):
    """Development environment settings."""
    ENV: str = "development"
    DEBUG: bool = True
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours for dev convenience
    ENABLE_STRUCTURED_LOGGING: bool = False  # Simple logging for dev


class TestingSettings(Settings):
    """Testing environment settings."""
    ENV: str = "testing"
    DEBUG: bool = False
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 5  # Short for testing
    ENABLE_STRUCTURED_LOGGING: bool = False


class StagingSettings(Settings):
    """Staging environment settings."""
    ENV: str = "staging"
    DEBUG: bool = False
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ENABLE_HTTPS_REDIRECT: bool = True
    SECRETS_PROVIDER: str = "vault"  # Use vault in staging


class ProductionSettings(Settings):
    """Production environment settings."""
    ENV: str = "production"
    DEBUG: bool = False
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Very short for production security
    ENABLE_HTTPS_REDIRECT: bool = True
    SECRETS_PROVIDER: str = "vault"  # Use vault in production
    ENABLE_STRUCTURED_LOGGING: bool = True
    
    # Stricter validation for production
    @validator('SECRET_KEY')
    def validate_production_secret_key(cls, v):
        """Ensure strong secret key in production."""
        if len(v) < 64:
            raise ValueError('SECRET_KEY must be at least 64 characters in production')
        if 'development' in v.lower():
            raise ValueError('Cannot use development SECRET_KEY in production')
        return v


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance based on environment."""
    env = os.getenv("ENV", "development").lower()
    
    settings_map = {
        "development": DevelopmentSettings,
        "testing": TestingSettings,
        "staging": StagingSettings,
        "production": ProductionSettings,
    }
    
    settings_class = settings_map.get(env, DevelopmentSettings)
    return settings_class()


# Export settings instance for import convenience
settings = get_settings()
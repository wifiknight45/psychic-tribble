import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseSettings, Field, AnyUrl

# -----------------------------------------------------------------------------
# 1. Load environment variables from a .env file (if present)
# -----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOTENV_PATH = os.path.join(BASE_DIR, os.pardir, ".env")
load_dotenv(DOTENV_PATH)


# -----------------------------------------------------------------------------
# 2. Core Settings class using Pydantic for validation and defaults
# -----------------------------------------------------------------------------
class Settings(BaseSettings):
    # General application settings
    APP_NAME: str = Field(
        default="pyschic_tribble",
        description="Human-friendly name of the application",
        example="pyschic_tribble"
    )
    ENV: str = Field(
        default="development",
        description="One of: development, testing, production",
        example="development"
    )
    DEBUG: bool = Field(
        default=True,
        description="Enable debug mode (should be False in production)"
    )

    # Security settings
    SECRET_KEY: str = Field(
        default=...,
        description="Cryptographic key for signing tokens — must be set in env"
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="Algorithm used to sign JWT tokens"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60 * 24,
        description="Duration (in minutes) before access tokens expire"
    )

    # Database connection
    DATABASE_URL: AnyUrl = Field(
        default=...,
        env="DATABASE_URL",
        description="Connection URL for your database, e.g. postgres://user:pass@host:port/dbname"
    )

    # CORS settings
    BACKEND_CORS_ORIGINS: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8000"
        ],
        description="List of allowed CORS origins; parsed from comma-separated env var"
    )

    class Config:
        # .env file path + encoding
        env_file = DOTENV_PATH
        env_file_encoding = "utf-8"
        case_sensitive = True


# -----------------------------------------------------------------------------
# 3. Environment-specific subclasses (override defaults where needed)
# -----------------------------------------------------------------------------
class DevelopmentSettings(Settings):
    DEBUG: bool = True


class TestingSettings(Settings):
    ENV: str = "testing"
    DEBUG: bool = False


class ProductionSettings(Settings):
    ENV: str = "production"
    DEBUG: bool = False


# -----------------------------------------------------------------------------
# 4. Cached loader for a singleton Settings instance
# -----------------------------------------------------------------------------
@lru_cache()
def get_settings() -> Settings:
    """
    Instantiate and return a Settings object based on ENV.
    Caches the result so settings are only read once.
    """
    env = os.getenv("ENV", "development").lower()
    if env == "production":
        return ProductionSettings()
    if env == "testing":
        return TestingSettings()
    return DevelopmentSettings()


# -----------------------------------------------------------------------------
# 5. Shared settings instance for import throughout the project
# -----------------------------------------------------------------------------
settings = get_settings()

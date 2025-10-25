"""Configuration management for DHub CLI."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    """Configuration class for DHub CLI."""

    # PostgreSQL Configuration
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "mydb")

    # DataHub Configuration
    DATAHUB_GMS_HOST = os.getenv("DATAHUB_GMS_HOST", "localhost")
    DATAHUB_GMS_PORT = os.getenv("DATAHUB_GMS_PORT", "8080")
    DATAHUB_GMS_PROTOCOL = os.getenv("DATAHUB_GMS_PROTOCOL", "http")
    DATAHUB_FRONTEND_URL = os.getenv("DATAHUB_FRONTEND_URL", "http://localhost:9002")
    DATAHUB_TOKEN = os.getenv("DATAHUB_TOKEN", "")

    # CLI Configuration
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    FAKER_LOCALE = os.getenv("FAKER_LOCALE", "en_US")
    OUTPUT_FORMAT = os.getenv("OUTPUT_FORMAT", "table")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def get_datahub_url(cls) -> str:
        """Get DataHub GMS URL."""
        return f"{cls.DATAHUB_GMS_PROTOCOL}://{cls.DATAHUB_GMS_HOST}:{cls.DATAHUB_GMS_PORT}"

    @classmethod
    def get_postgres_connection_string(cls) -> str:
        """Get PostgreSQL connection string."""
        return f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"


# Global config instance
config = Config()

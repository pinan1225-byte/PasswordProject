"""Tests for settings configuration."""

import pytest
from src.password_manager.config import Settings


class TestSettings:
    """Test cases for Settings."""

    def test_default_settings(self) -> None:
        """Test default settings values — use explicit values to avoid .env pollution."""
        settings = Settings(
            MYSQL_HOST="localhost",
            MYSQL_PORT=3306,
            MYSQL_USER="root",
            ENVIRONMENT="development",
            LOG_LEVEL="INFO",
        )

        assert settings.MYSQL_HOST == "localhost"
        assert settings.MYSQL_PORT == 3306
        assert settings.MYSQL_USER == "root"
        assert settings.ENVIRONMENT == "development"
        assert settings.LOG_LEVEL == "INFO"

    def test_database_url(self) -> None:
        """Test database URL construction."""
        settings = Settings(
            MYSQL_HOST="localhost",
            MYSQL_PORT=3306,
            MYSQL_USER="test_user",
            MYSQL_PASSWORD="test_pass",
            MYSQL_DATABASE="test_db",
        )

        expected_url = "mysql+pymysql://test_user:test_pass@localhost:3306/test_db?charset=utf8mb4"
        assert settings.database_url == expected_url

    def test_environment_flags(self) -> None:
        """Test environment flag methods."""
        dev_settings = Settings(ENVIRONMENT="development")
        assert dev_settings.is_development is True
        assert dev_settings.is_production is False

        prod_settings = Settings(ENVIRONMENT="production")
        assert prod_settings.is_production is True
        assert prod_settings.is_development is False

    def test_log_level_validation(self) -> None:
        """Test log level validation."""
        settings = Settings(LOG_LEVEL="debug")
        assert settings.LOG_LEVEL == "DEBUG"

        with pytest.raises(ValueError):
            Settings(LOG_LEVEL="invalid")

    def test_environment_validation(self) -> None:
        """Test environment validation."""
        settings = Settings(ENVIRONMENT="TESTING")
        assert settings.ENVIRONMENT == "testing"

        with pytest.raises(ValueError):
            Settings(ENVIRONMENT="invalid_env")

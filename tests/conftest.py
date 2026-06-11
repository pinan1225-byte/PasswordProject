"""Pytest configuration and fixtures."""

import pytest
from typing import Generator

from src.password_manager.config import Settings, get_settings
from src.password_manager.storage import DatabaseManager
from src.password_manager.storage.models import Base


@pytest.fixture
def test_settings() -> Settings:
    """Provide test settings."""
    return Settings(
        MYSQL_HOST="localhost",
        MYSQL_PORT=3306,
        MYSQL_USER="test_user",
        MYSQL_PASSWORD="test_password",
        MYSQL_DATABASE="password_manager_test",
        ENVIRONMENT="testing",
        LOG_LEVEL="DEBUG",
    )


@pytest.fixture
def test_db() -> Generator[DatabaseManager, None, None]:
    """Provide an in-memory SQLite database for tests — no external MySQL required."""
    db_manager = DatabaseManager(database_url="sqlite:///:memory:")
    db_manager.initialize()

    yield db_manager

    # Drop all tables to ensure clean state between tests
    if db_manager._engine is not None:
        Base.metadata.drop_all(db_manager._engine)
    db_manager.close()


@pytest.fixture
def test_master_password() -> str:
    """Provide test master password."""
    return "TestMasterPassword123!"

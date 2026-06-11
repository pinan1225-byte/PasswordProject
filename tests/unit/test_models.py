"""Tests for database models."""

import pytest
from datetime import datetime, timezone

from src.password_manager.storage.models import PasswordEntry


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TestModels:
    """Test cases for database models."""

    def test_password_entry_creation(self) -> None:
        """Test PasswordEntry model creation."""
        entry = PasswordEntry(
            user_id=1,
            title="Test Entry",
            username="testuser",
            encrypted_password="encrypted_data",
            url="https://example.com",
            notes="Test notes",
            category="Work",
            tags=["tag1", "tag2"],
            created_at=_now(),
            updated_at=_now(),
        )
        
        assert entry.title == "Test Entry"
        assert entry.username == "testuser"
        assert entry.encrypted_password == "encrypted_data"
        assert entry.url == "https://example.com"
        assert entry.notes == "Test notes"
        assert entry.category == "Work"
        assert entry.tags == ["tag1", "tag2"]
        assert entry.id is None

    def test_password_entry_optional_fields(self) -> None:
        """Test PasswordEntry with optional fields."""
        entry = PasswordEntry(
            user_id=1,
            title="Minimal Entry",
            username="user",
            encrypted_password="encrypted",
            created_at=_now(),
            updated_at=_now(),
        )
        
        assert entry.url is None
        assert entry.notes is None
        assert entry.category is None
        assert entry.tags == []

    def test_password_entry_validation(self) -> None:
        """Test PasswordEntry validation — empty title raises ValueError."""
        with pytest.raises(ValueError):
            PasswordEntry(
                user_id=1,
                title="",
                username="user",
                encrypted_password="encrypted",
                created_at=_now(),
                updated_at=_now(),
            )
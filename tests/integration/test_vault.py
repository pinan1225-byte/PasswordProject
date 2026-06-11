"""Integration tests for vault operations."""

import pytest
from datetime import datetime

from src.password_manager.core import CryptoManager, VaultManager
from src.password_manager.storage import DatabaseManager, PasswordEntry

_TEST_USER_ID = 1


@pytest.mark.integration
class TestVaultIntegration:
    """Integration tests for vault operations."""

    def test_add_and_get_entry(
        self, test_db: DatabaseManager, test_master_password: str
    ) -> None:
        """Test adding and retrieving an entry."""
        crypto = CryptoManager(test_master_password)
        vault = VaultManager(crypto, test_db, user_id=_TEST_USER_ID)

        entry = vault.add_entry(
            title="Test Entry",
            username="testuser",
            password="TestPassword123!",
            url="https://example.com",
            category="Test",
            tags=["tag1", "tag2"],
        )

        assert entry.id is not None
        assert entry.title == "Test Entry"

        retrieved = vault.get_entry(entry.id)
        assert retrieved is not None
        assert retrieved.title == "Test Entry"
        assert retrieved.username == "testuser"

        decrypted = vault.get_decrypted_password(entry.id)
        assert decrypted == "TestPassword123!"

        crypto.clear_key()

    def test_list_entries(
        self, test_db: DatabaseManager, test_master_password: str
    ) -> None:
        """Test listing entries."""
        crypto = CryptoManager(test_master_password)
        vault = VaultManager(crypto, test_db, user_id=_TEST_USER_ID)

        vault.add_entry(
            title="Entry 1",
            username="user1",
            password="pass1",
            category="Work",
        )

        vault.add_entry(
            title="Entry 2",
            username="user2",
            password="pass2",
            category="Personal",
        )

        entries = vault.list_entries()
        assert len(entries) >= 2

        work_entries = vault.list_entries(category="Work")
        assert len(work_entries) >= 1
        assert all(e.category == "Work" for e in work_entries)

        crypto.clear_key()

    def test_update_entry(
        self, test_db: DatabaseManager, test_master_password: str
    ) -> None:
        """Test updating an entry."""
        crypto = CryptoManager(test_master_password)
        vault = VaultManager(crypto, test_db, user_id=_TEST_USER_ID)

        entry = vault.add_entry(
            title="Original Title",
            username="original_user",
            password="original_pass",
        )

        updated = vault.update_entry(
            entry_id=entry.id,
            title="Updated Title",
            username="updated_user",
        )

        assert updated is not None
        assert updated.title == "Updated Title"
        assert updated.username == "updated_user"

        retrieved = vault.get_entry(entry.id)
        assert retrieved.title == "Updated Title"

        crypto.clear_key()

    def test_delete_entry(
        self, test_db: DatabaseManager, test_master_password: str
    ) -> None:
        """Test deleting an entry."""
        crypto = CryptoManager(test_master_password)
        vault = VaultManager(crypto, test_db, user_id=_TEST_USER_ID)

        entry = vault.add_entry(
            title="To Delete",
            username="user",
            password="pass",
        )

        success = vault.delete_entry(entry.id)
        assert success

        retrieved = vault.get_entry(entry.id)
        assert retrieved is None

        crypto.clear_key()

    def test_search_entries(
        self, test_db: DatabaseManager, test_master_password: str
    ) -> None:
        """Test searching entries."""
        crypto = CryptoManager(test_master_password)
        vault = VaultManager(crypto, test_db, user_id=_TEST_USER_ID)

        vault.add_entry(
            title="GitHub Account",
            username="developer",
            password="pass",
            url="https://github.com",
        )

        vault.add_entry(
            title="GitLab Account",
            username="developer",
            password="pass",
            url="https://gitlab.com",
        )

        vault.add_entry(
            title="Email Account",
            username="user@example.com",
            password="pass",
        )

        results = vault.list_entries(search="git")
        assert len(results) >= 2

        results = vault.list_entries(search="developer")
        assert len(results) >= 2

        crypto.clear_key()

    def test_update_password_is_re_encrypted(
        self, test_db: DatabaseManager, test_master_password: str
    ) -> None:
        """Updating a password must store a new ciphertext and decrypt correctly."""
        crypto = CryptoManager(test_master_password)
        vault = VaultManager(crypto, test_db, user_id=_TEST_USER_ID)

        entry = vault.add_entry(
            title="My Site",
            username="alice",
            password="old_password_123",
        )
        old_cipher = vault.get_entry(entry.id).encrypted_password

        vault.update_entry(entry_id=entry.id, password="new_password_456")

        new_cipher = vault.get_entry(entry.id).encrypted_password
        # Ciphertext must change (AES-GCM uses a random nonce each time)
        assert new_cipher != old_cipher

        # Decrypted value must reflect the new password
        decrypted = vault.get_decrypted_password(entry.id)
        assert decrypted == "new_password_456"

        crypto.clear_key()

    def test_update_entry_fields(
        self, test_db: DatabaseManager, test_master_password: str
    ) -> None:
        """Updating title, username, url, category, notes works independently."""
        crypto = CryptoManager(test_master_password)
        vault = VaultManager(crypto, test_db, user_id=_TEST_USER_ID)

        entry = vault.add_entry(
            title="Old Title",
            username="old_user",
            password="pass",
            url="https://old.example.com",
            category="Work",
            notes="old notes",
        )

        updated = vault.update_entry(
            entry_id=entry.id,
            title="New Title",
            username="new_user",
            url="https://new.example.com",
            category="Personal",
            notes="new notes",
        )

        assert updated is not None
        assert updated.title == "New Title"
        assert updated.username == "new_user"
        assert updated.url == "https://new.example.com"
        assert updated.category == "Personal"
        assert updated.notes == "new notes"
        # Password unchanged
        assert vault.get_decrypted_password(entry.id) == "pass"

        crypto.clear_key()

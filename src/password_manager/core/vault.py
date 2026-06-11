"""Password vault management."""

from datetime import datetime, timezone
from typing import List, Optional

from src.password_manager.core.crypto import CryptoManager
from src.password_manager.storage.database import DatabaseManager
from src.password_manager.storage.models import PasswordEntry


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class VaultManager:
    """Manage password vault operations."""

    def __init__(self, crypto_manager: CryptoManager, db_manager: DatabaseManager, user_id: int):
        """
        Initialize vault manager.

        Args:
            crypto_manager: CryptoManager instance for encryption
            db_manager: DatabaseManager instance for storage
            user_id: User ID for this vault
        """
        self._crypto = crypto_manager
        self._db = db_manager
        self._user_id = user_id

    def add_entry(
        self,
        title: str,
        username: str,
        password: str,
        url: Optional[str] = None,
        notes: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> PasswordEntry:
        """
        Add a new password entry.

        Args:
            title: Entry title
            username: Username
            password: Password (will be encrypted)
            url: Optional URL
            notes: Optional notes
            category: Optional category
            tags: Optional list of tags

        Returns:
            Created PasswordEntry
        """
        encrypted_password = self._crypto.encrypt(password)

        entry = PasswordEntry(
            user_id=self._user_id,
            title=title,
            username=username,
            encrypted_password=encrypted_password,
            url=url,
            notes=notes,
            category=category,
            tags=tags or [],
            created_at=_utcnow(),
            updated_at=_utcnow(),
        )

        return self._db.add_entry(entry)

    def get_entry(self, entry_id: int) -> Optional[PasswordEntry]:
        """
        Get password entry by ID.

        Args:
            entry_id: Entry ID

        Returns:
            PasswordEntry if found, None otherwise
        """
        return self._db.get_entry(entry_id, user_id=self._user_id)

    def get_decrypted_password(self, entry_id: int) -> Optional[str]:
        """
        Get decrypted password for entry.

        Args:
            entry_id: Entry ID

        Returns:
            Decrypted password if entry exists, None otherwise
        """
        entry = self.get_entry(entry_id)
        if entry is None:
            return None

        return self._crypto.decrypt(entry.encrypted_password)

    def list_entries(
        self,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[PasswordEntry]:
        """
        List password entries with optional filters.

        Args:
            category: Filter by category
            tag: Filter by tag
            search: Search in title, username, or URL

        Returns:
            List of matching entries
        """
        return self._db.list_entries(
            user_id=self._user_id,
            category=category,
            tag=tag,
            search=search
        )

    def update_entry(
        self,
        entry_id: int,
        title: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        url: Optional[str] = None,
        notes: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[PasswordEntry]:
        """
        Update password entry.

        Args:
            entry_id: Entry ID
            title: New title
            username: New username
            password: New password (will be encrypted)
            url: New URL
            notes: New notes
            category: New category
            tags: New tags

        Returns:
            Updated PasswordEntry if found, None otherwise
        """
        entry = self.get_entry(entry_id)
        if entry is None:
            return None

        if title is not None:
            entry.title = title
        if username is not None:
            entry.username = username
        if password is not None:
            entry.encrypted_password = self._crypto.encrypt(password)
        if url is not None:
            entry.url = url
        if notes is not None:
            entry.notes = notes
        if category is not None:
            entry.category = category
        if tags is not None:
            entry.tags = tags

        entry.updated_at = _utcnow()

        return self._db.update_entry(entry)

    def delete_entry(self, entry_id: int) -> bool:
        """
        Delete password entry.

        Args:
            entry_id: Entry ID

        Returns:
            True if deleted, False if not found
        """
        return self._db.delete_entry(entry_id, user_id=self._user_id)

    def get_categories(self) -> List[str]:
        """Get all unique categories for current user."""
        return self._db.get_categories(user_id=self._user_id)

    def get_tags(self) -> List[str]:
        """Get all unique tags for current user."""
        return self._db.get_tags(user_id=self._user_id)
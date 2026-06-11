"""Database connection and operations management."""

import json
from contextlib import contextmanager
from typing import List, Optional

from sqlalchemy import and_, create_engine, or_
from sqlalchemy.orm import Session, sessionmaker

from src.password_manager.config import get_settings
from src.password_manager.storage.models import (
    Base,
    MasterKeyModel,
    PasswordEntry,
    PasswordEntryModel,
)


class DatabaseManager:
    """Manage database connections and operations."""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database manager.

        Args:
            database_url: Optional database URL (uses settings if not provided)
        """
        self.settings = get_settings()
        self._database_url = database_url or self.settings.database_url
        self._engine = None
        self._session_factory = None

    def initialize(self) -> None:
        """Initialize database connection and create tables."""
        try:
            self._engine = create_engine(
                self._database_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=self.settings.is_development,
            )
            self._session_factory = sessionmaker(self._engine)
            
            # Verify the connection works
            with self._engine.connect() as conn:
                pass
                
            Base.metadata.create_all(self._engine)
            self.is_sqlite_fallback = False
        except Exception as e:
            # Fall back to SQLite if the configured DB URL is a MySQL database
            if "mysql" in self._database_url:
                import os
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"MySQL connection failed: {e}. Falling back to local SQLite database.")
                
                # Use home directory ~/.password_manager/password_vault.db
                home_dir = os.path.expanduser("~")
                db_dir = os.path.join(home_dir, ".password_manager")
                os.makedirs(db_dir, exist_ok=True)
                sqlite_path = os.path.abspath(os.path.join(db_dir, "password_vault.db")).replace("\\", "/")
                self._database_url = f"sqlite:///{sqlite_path}"
                
                # Rebuild engine for SQLite
                self._engine = create_engine(
                    self._database_url,
                    echo=self.settings.is_development,
                )
                self._session_factory = sessionmaker(self._engine)
                Base.metadata.create_all(self._engine)
                self.is_sqlite_fallback = True
            else:
                raise

    @contextmanager
    def get_session(self) -> Session:
        """
        Get database session context manager.

        Yields:
            SQLAlchemy Session

        Raises:
            RuntimeError: If database has not been initialized via initialize()
        """
        if self._session_factory is None:
            raise RuntimeError(
                "DatabaseManager not initialized. Call initialize() before use."
            )
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def add_entry(self, entry: PasswordEntry) -> PasswordEntry:
        """
        Add password entry to database.

        Args:
            entry: PasswordEntry to add

        Returns:
            Created PasswordEntry with ID
        """
        with self.get_session() as session:
            model = PasswordEntryModel(
                user_id=entry.user_id,
                title=entry.title,
                username=entry.username,
                encrypted_password=entry.encrypted_password,
                url=entry.url,
                notes=entry.notes,
                category=entry.category,
                tags=json.dumps(entry.tags) if entry.tags else json.dumps([]),
                created_at=entry.created_at,
                updated_at=entry.updated_at,
            )
            session.add(model)
            session.flush()
            entry.id = model.id
            return entry

    def get_entry(self, entry_id: int, user_id: Optional[int] = None) -> Optional[PasswordEntry]:
        """
        Get password entry by ID.

        Args:
            entry_id: Entry ID
            user_id: Optional user ID filter

        Returns:
            PasswordEntry if found, None otherwise
        """
        with self.get_session() as session:
            filters = [PasswordEntryModel.id == entry_id, PasswordEntryModel.is_deleted == False]
            
            if user_id is not None:
                filters.append(PasswordEntryModel.user_id == user_id)
            
            model = session.query(PasswordEntryModel).filter(and_(*filters)).first()

            if model is None:
                return None

            return PasswordEntry(
                id=model.id,
                user_id=model.user_id,
                title=model.title,
                username=model.username,
                encrypted_password=model.encrypted_password,
                url=model.url,
                notes=model.notes,
                category=model.category,
                tags=json.loads(model.tags) if model.tags else [],
                created_at=model.created_at,
                updated_at=model.updated_at,
            )

    def list_entries(
        self,
        user_id: Optional[int] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[PasswordEntry]:
        """
        List password entries with optional filters.

        Args:
            user_id: Filter by user ID
            category: Filter by category
            tag: Filter by tag
            search: Search in title, username, or URL

        Returns:
            List of matching entries
        """
        with self.get_session() as session:
            filters = [PasswordEntryModel.is_deleted == False]
            
            if user_id is not None:
                filters.append(PasswordEntryModel.user_id == user_id)
            
            query = session.query(PasswordEntryModel).filter(and_(*filters))

            if category:
                query = query.filter(PasswordEntryModel.category == category)

            if tag:
                query = query.filter(PasswordEntryModel.tags.contains(f'"{tag}"'))

            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    or_(
                        PasswordEntryModel.title.like(search_pattern),
                        PasswordEntryModel.username.like(search_pattern),
                        PasswordEntryModel.url.like(search_pattern),
                    )
                )

            models = query.order_by(PasswordEntryModel.updated_at.desc()).all()

            entries = []
            for model in models:
                entries.append(
                    PasswordEntry(
                        id=model.id,
                        user_id=model.user_id,
                        title=model.title,
                        username=model.username,
                        encrypted_password=model.encrypted_password,
                        url=model.url,
                        notes=model.notes,
                        category=model.category,
                        tags=json.loads(model.tags) if model.tags else [],
                        created_at=model.created_at,
                        updated_at=model.updated_at,
                    )
                )

            return entries

    def update_entry(self, entry: PasswordEntry) -> PasswordEntry:
        """
        Update password entry.

        Args:
            entry: PasswordEntry to update

        Returns:
            Updated PasswordEntry
        """
        with self.get_session() as session:
            model = (
                session.query(PasswordEntryModel)
                .filter(
                    and_(
                        PasswordEntryModel.id == entry.id,
                        PasswordEntryModel.user_id == entry.user_id,
                        PasswordEntryModel.is_deleted == False
                    )
                )
                .first()
            )

            if model is None:
                raise ValueError(f"Entry with ID {entry.id} not found")

            model.title = entry.title
            model.username = entry.username
            model.encrypted_password = entry.encrypted_password
            model.url = entry.url
            model.notes = entry.notes
            model.category = entry.category
            model.tags = json.dumps(entry.tags) if entry.tags else json.dumps([])
            model.updated_at = entry.updated_at

            return entry

    def delete_entry(self, entry_id: int, user_id: Optional[int] = None) -> bool:
        """
        Soft delete password entry.

        Args:
            entry_id: Entry ID
            user_id: Optional user ID filter

        Returns:
            True if deleted, False if not found
        """
        with self.get_session() as session:
            filters = [PasswordEntryModel.id == entry_id, PasswordEntryModel.is_deleted == False]
            
            if user_id is not None:
                filters.append(PasswordEntryModel.user_id == user_id)
            
            model = session.query(PasswordEntryModel).filter(and_(*filters)).first()

            if model is None:
                return False

            model.is_deleted = True
            return True

    def get_categories(self, user_id: Optional[int] = None) -> List[str]:
        """
        Get all unique categories.

        Args:
            user_id: Optional user ID filter

        Returns:
            List of categories
        """
        with self.get_session() as session:
            filters = [
                PasswordEntryModel.category.isnot(None),
                PasswordEntryModel.is_deleted == False,
            ]
            
            if user_id is not None:
                filters.append(PasswordEntryModel.user_id == user_id)
            
            results = (
                session.query(PasswordEntryModel.category)
                .filter(and_(*filters))
                .distinct()
                .all()
            )
            return [r[0] for r in results if r[0]]

    def get_tags(self, user_id: Optional[int] = None) -> List[str]:
        """
        Get all unique tags.

        Args:
            user_id: Optional user ID filter

        Returns:
            List of tags
        """
        with self.get_session() as session:
            filters = [PasswordEntryModel.tags.isnot(None), PasswordEntryModel.is_deleted == False]
            
            if user_id is not None:
                filters.append(PasswordEntryModel.user_id == user_id)
            
            results = (
                session.query(PasswordEntryModel.tags)
                .filter(and_(*filters))
                .all()
            )

            all_tags = set()
            for result in results:
                if result[0]:
                    tags = json.loads(result[0])
                    all_tags.update(tags)

            return sorted(list(all_tags))

    def save_master_key(self, hashed_key: str, salt: str, user_id: Optional[int] = None) -> None:
        """
        Save master key hash and salt.

        Args:
            hashed_key: Hashed master key
            salt: Salt used for hashing
            user_id: Optional user ID
        """
        with self.get_session() as session:
            if user_id is not None:
                session.query(MasterKeyModel).filter(MasterKeyModel.user_id == user_id).delete()
            else:
                session.query(MasterKeyModel).filter(MasterKeyModel.user_id.is_(None)).delete()

            model = MasterKeyModel(user_id=user_id, hashed_key=hashed_key, salt=salt)
            session.add(model)

    def get_master_key(self, user_id: Optional[int] = None) -> Optional[tuple[str, str]]:
        """
        Get master key hash and salt.

        Args:
            user_id: Optional user ID filter

        Returns:
            Tuple of (hashed_key, salt) if exists, None otherwise
        """
        with self.get_session() as session:
            if user_id is not None:
                model = session.query(MasterKeyModel).filter(MasterKeyModel.user_id == user_id).first()
            else:
                model = session.query(MasterKeyModel).filter(MasterKeyModel.user_id.is_(None)).first()

            if model is None:
                return None

            return model.hashed_key, model.salt

    def close(self) -> None:
        """Close database connection."""
        if self._engine:
            self._engine.dispose()
"""User management functionality."""

from datetime import datetime, timezone
from typing import Optional, List

from src.password_manager.core.crypto import CryptoManager
from src.password_manager.storage.database import DatabaseManager
from src.password_manager.storage.models import User, UserModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class UserManager:
    """Manage user operations."""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize user manager.

        Args:
            db_manager: DatabaseManager instance
        """
        self._db = db_manager

    @staticmethod
    def _model_to_user(user: UserModel) -> User:
        """Convert a UserModel ORM instance to a User Pydantic model."""
        return User(
            id=user.id,
            username=user.username,
            hashed_password=user.hashed_password,
            salt=user.salt,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at,
            is_active=bool(user.is_active),
        )

    def create_user(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
    ) -> User:
        """
        Create a new user.

        Args:
            username: Username
            password: User password
            email: Optional email

        Returns:
            Created User
        """
        hashed_password, _ = CryptoManager.hash_password(password)

        with self._db.get_session() as session:
            user = UserModel(
                username=username,
                hashed_password=hashed_password,
                salt="",  # Argon2 embeds salt in hashed_password; column kept for schema compat
                email=email,
                created_at=_utcnow(),
                updated_at=_utcnow(),
                is_active=1,
            )
            session.add(user)
            session.flush()

            return self._model_to_user(user)

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user.

        Args:
            username: Username
            password: Password

        Returns:
            User if authentication successful, None otherwise
        """
        with self._db.get_session() as session:
            user = session.query(UserModel).filter(
                UserModel.username == username,
                UserModel.is_active == 1
            ).first()
            
            if user is None:
                return None
            
            if CryptoManager.verify_password(password, user.hashed_password, bytes.fromhex(user.salt)):
                return self._model_to_user(user)

            return None

    def get_user(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User if found, None otherwise
        """
        with self._db.get_session() as session:
            user = session.query(UserModel).filter(
                UserModel.id == user_id,
                UserModel.is_active == 1
            ).first()

            if user is None:
                return None

            return self._model_to_user(user)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.

        Args:
            username: Username

        Returns:
            User if found, None otherwise
        """
        with self._db.get_session() as session:
            user = session.query(UserModel).filter(
                UserModel.username == username,
                UserModel.is_active == 1
            ).first()

            if user is None:
                return None

            return self._model_to_user(user)

    def list_users(self) -> List[User]:
        """
        List all active users.

        Returns:
            List of users
        """
        with self._db.get_session() as session:
            users = session.query(UserModel).filter(
                UserModel.is_active == 1
            ).all()
            
            return [self._model_to_user(user) for user in users]

    def update_user(
        self,
        user_id: int,
        email: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Optional[User]:
        """
        Update user information.

        Args:
            user_id: User ID
            email: New email
            password: New password

        Returns:
            Updated User if found, None otherwise
        """
        with self._db.get_session() as session:
            user = session.query(UserModel).filter(
                UserModel.id == user_id,
                UserModel.is_active == 1
            ).first()
            
            if user is None:
                return None
            
            if email is not None:
                user.email = email
            
            if password is not None:
                hashed_password, salt = CryptoManager.hash_password(password)
                user.hashed_password = hashed_password
                user.salt = salt.hex()
            
            user.updated_at = _utcnow()

            return self._model_to_user(user)

    def delete_user(self, user_id: int) -> bool:
        """
        Soft delete user.

        Args:
            user_id: User ID

        Returns:
            True if deleted, False if not found
        """
        with self._db.get_session() as session:
            user = session.query(UserModel).filter(
                UserModel.id == user_id,
                UserModel.is_active == 1
            ).first()
            
            if user is None:
                return False
            
            user.is_active = 0
            return True
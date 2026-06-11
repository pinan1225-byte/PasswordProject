"""Database models for password storage."""

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    """SQLAlchemy model for users."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    # salt is kept for schema compatibility; Argon2 embeds its own salt in hashed_password
    salt = Column(String(255), nullable=False, default="")
    email = Column(String(255), nullable=True, unique=True)
    created_at = Column(DateTime, nullable=False, default=_utcnow)
    updated_at = Column(DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)
    is_active = Column(Boolean, default=True, index=True)

    password_entries = relationship("PasswordEntryModel", back_populates="user")


class PasswordEntryModel(Base):
    """SQLAlchemy model for password entries."""

    __tablename__ = "password_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    username = Column(String(255), nullable=False)
    encrypted_password = Column(Text, nullable=False)
    url = Column(String(2048), nullable=True)
    notes = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    tags = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=_utcnow)
    updated_at = Column(DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)
    is_deleted = Column(Boolean, default=False, index=True)

    user = relationship("UserModel", back_populates="password_entries")


class User(BaseModel):
    """Pydantic model for user."""

    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    username: str = Field(..., min_length=3, max_length=255)
    hashed_password: str
    salt: str
    email: Optional[str] = Field(None, max_length=255)
    created_at: datetime
    updated_at: datetime
    is_active: bool = True


class PasswordEntry(BaseModel):
    """Pydantic model for password entry."""

    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    user_id: int
    title: str = Field(..., min_length=1, max_length=255)
    username: str = Field(...)
    encrypted_password: str
    url: Optional[str] = Field(None, max_length=2048)
    notes: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class MasterKeyModel(Base):
    """SQLAlchemy model for master key storage."""

    __tablename__ = "master_key"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    hashed_key = Column(String(255), nullable=False)
    salt = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=_utcnow)

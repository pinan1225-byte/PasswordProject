"""Unit tests for validators."""

import pytest
from src.password_manager.utils.validators import (
    validate_email,
    validate_password_policy,
    validate_url,
    validate_username,
)


class TestValidators:
    """Test cases for validation utilities."""

    def test_validate_url_valid(self) -> None:
        """Test valid URL validation."""
        assert validate_url("https://example.com")
        assert validate_url("http://example.com")
        assert validate_url("https://www.example.com/path")

    def test_validate_url_invalid(self) -> None:
        """Test invalid URL validation."""
        assert not validate_url("not_a_url")
        assert not validate_url("example.com")
        assert not validate_url("://no-scheme")

    def test_validate_password_policy_valid(self) -> None:
        """Test valid password policy."""
        is_valid, errors = validate_password_policy(
            "StrongPass123!",
            min_length=8,
            require_uppercase=True,
            require_lowercase=True,
            require_digits=True,
            require_special=True,
        )
        
        assert is_valid
        assert len(errors) == 0

    def test_validate_password_policy_too_short(self) -> None:
        """Test password too short."""
        is_valid, errors = validate_password_policy(
            "Short1!",
            min_length=8,
        )
        
        assert not is_valid
        assert "Password must be at least 8 characters long" in errors

    def test_validate_password_policy_no_uppercase(self) -> None:
        """Test password without uppercase."""
        is_valid, errors = validate_password_policy(
            "lowercase123!",
            require_uppercase=True,
        )
        
        assert not is_valid
        assert "Password must contain at least one uppercase letter" in errors

    def test_validate_password_policy_no_lowercase(self) -> None:
        """Test password without lowercase."""
        is_valid, errors = validate_password_policy(
            "UPPERCASE123!",
            require_lowercase=True,
        )
        
        assert not is_valid
        assert "Password must contain at least one lowercase letter" in errors

    def test_validate_password_policy_no_digits(self) -> None:
        """Test password without digits."""
        is_valid, errors = validate_password_policy(
            "NoDigits!",
            require_digits=True,
        )
        
        assert not is_valid
        assert "Password must contain at least one digit" in errors

    def test_validate_password_policy_no_special(self) -> None:
        """Test password without special characters."""
        is_valid, errors = validate_password_policy(
            "NoSpecial123",
            require_special=True,
        )
        
        assert not is_valid
        assert "Password must contain at least one special character" in errors

    def test_validate_email_valid(self) -> None:
        """Test valid email validation."""
        assert validate_email("user@example.com")
        assert validate_email("user.name@example.com")
        assert validate_email("user+tag@example.org")

    def test_validate_email_invalid(self) -> None:
        """Test invalid email validation."""
        assert not validate_email("not_an_email")
        assert not validate_email("user@")
        assert not validate_email("@example.com")

    def test_validate_username_valid(self) -> None:
        """Test valid username validation."""
        is_valid, error = validate_username("valid_user")
        assert is_valid
        assert error is None
        
        is_valid, error = validate_username("user123")
        assert is_valid
        
        is_valid, error = validate_username("user.name")
        assert is_valid

    def test_validate_username_empty(self) -> None:
        """Test empty username."""
        is_valid, error = validate_username("")
        assert not is_valid
        assert "cannot be empty" in error

    def test_validate_username_too_short(self) -> None:
        """Test username too short."""
        is_valid, error = validate_username("ab")
        assert not is_valid
        assert "at least 3 characters" in error

    def test_validate_username_too_long(self) -> None:
        """Test username too long."""
        is_valid, error = validate_username("a" * 65)
        assert not is_valid
        assert "cannot exceed 64 characters" in error

    def test_validate_username_invalid_chars(self) -> None:
        """Test username with invalid characters."""
        is_valid, error = validate_username("user@name")
        assert not is_valid
        assert "can only contain" in error
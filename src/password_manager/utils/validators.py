"""Validation utilities."""

import re
from typing import List, Optional
from urllib.parse import urlparse


def validate_url(url: str) -> bool:
    """
    Validate URL format.

    Args:
        url: URL to validate

    Returns:
        True if valid URL
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_password_policy(
    password: str,
    min_length: int = 1,
    require_uppercase: bool = False,
    require_lowercase: bool = False,
    require_digits: bool = False,
    require_special: bool = False,
) -> tuple[bool, List[str]]:
    """
    Validate password against policy.

    Args:
        password: Password to validate
        min_length: Minimum length
        require_uppercase: Require uppercase letters
        require_lowercase: Require lowercase letters
        require_digits: Require digits
        require_special: Require special characters

    Returns:
        Tuple of (is_valid, list of errors)
    """
    errors: List[str] = []

    if len(password) < min_length:
        errors.append(f"Password must be at least {min_length} characters long")

    if require_uppercase and not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")

    if require_lowercase and not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")

    if require_digits and not re.search(r"\d", password):
        errors.append("Password must contain at least one digit")

    if require_special and not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", password):
        errors.append("Password must contain at least one special character")

    return len(errors) == 0, errors


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email to validate

    Returns:
        True if valid email
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_username(username: str) -> tuple[bool, Optional[str]]:
    """
    Validate username.

    Args:
        username: Username to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username:
        return False, "Username cannot be empty"

    if len(username) < 3:
        return False, "Username must be at least 3 characters long"

    if len(username) > 64:
        return False, "Username cannot exceed 64 characters"

    if not re.match(r"^[a-zA-Z0-9_\-\.]+$", username):
        return False, "Username can only contain letters, numbers, underscores, hyphens, and dots"

    return True, None
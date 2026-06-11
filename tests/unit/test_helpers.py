"""Tests for helper utilities."""

from src.password_manager.utils.helpers import clear_screen, mask_string


class TestHelpers:
    """Test cases for helper functions."""

    def test_mask_string_short(self) -> None:
        """Test masking short string."""
        result = mask_string("abc", visible_chars=2)
        assert result == "***"

    def test_mask_string_long(self) -> None:
        """Test masking long string."""
        result = mask_string("password123", visible_chars=2)
        assert result == "pa*******23"
        assert len(result) == len("password123")

    def test_mask_string_custom_visible(self) -> None:
        """Test masking with custom visible chars."""
        result = mask_string("mypassword", visible_chars=3)
        assert result == "myp****ord"

    def test_mask_string_exact_length(self) -> None:
        """Test masking string with exact visible length."""
        result = mask_string("abcd", visible_chars=2)
        assert result == "****"
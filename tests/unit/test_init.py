"""Tests for __init__.py modules."""

from password_manager import __version__


def test_version():
    """Test that version is defined."""
    assert __version__ == "0.1.0"
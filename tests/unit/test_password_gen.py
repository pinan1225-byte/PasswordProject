"""Unit tests for PasswordGenerator."""

import pytest
from src.password_manager.core.password_gen import PasswordGenerator, PasswordStrength


class TestPasswordGenerator:
    """Test cases for PasswordGenerator."""

    def test_generate_default_password(self) -> None:
        """Test default password generation."""
        generator = PasswordGenerator()
        password = generator.generate()
        
        assert len(password) == 16
        assert any(c.isupper() for c in password)
        assert any(c.islower() for c in password)
        assert any(c.isdigit() for c in password)
        assert any(c in PasswordGenerator.SPECIAL for c in password)

    def test_generate_custom_length(self) -> None:
        """Test password generation with custom length."""
        generator = PasswordGenerator(length=24)
        password = generator.generate()
        
        assert len(password) == 24

    def test_generate_no_special(self) -> None:
        """Test password generation without special characters."""
        generator = PasswordGenerator(use_special=False)
        password = generator.generate()
        
        assert not any(c in PasswordGenerator.SPECIAL for c in password)

    def test_generate_no_digits(self) -> None:
        """Test password generation without digits."""
        generator = PasswordGenerator(use_digits=False)
        password = generator.generate()
        
        assert not any(c.isdigit() for c in password)

    def test_exclude_ambiguous(self) -> None:
        """Test excluding ambiguous characters."""
        generator = PasswordGenerator(exclude_ambiguous=True)
        password = generator.generate()
        
        ambiguous = set("0O1lI")
        assert not any(c in ambiguous for c in password)

    def test_minimum_requirements(self) -> None:
        """Test minimum character requirements."""
        generator = PasswordGenerator(
            length=20,
            min_uppercase=3,
            min_lowercase=3,
            min_digits=3,
            min_special=3,
        )
        password = generator.generate()
        
        assert sum(1 for c in password if c.isupper()) >= 3
        assert sum(1 for c in password if c.islower()) >= 3
        assert sum(1 for c in password if c.isdigit()) >= 3
        assert sum(1 for c in password if c in PasswordGenerator.SPECIAL) >= 3

    def test_calculate_strength_very_weak(self) -> None:
        """Test password strength calculation - very weak."""
        strength = PasswordGenerator.calculate_strength("123")
        assert strength == PasswordStrength.VERY_WEAK

    def test_calculate_strength_weak(self) -> None:
        """Test password strength calculation - weak."""
        strength = PasswordGenerator.calculate_strength("password")
        assert strength == PasswordStrength.WEAK

    def test_calculate_strength_fair(self) -> None:
        """Test password strength calculation - fair."""
        strength = PasswordGenerator.calculate_strength("Password123")
        assert strength in [PasswordStrength.FAIR, PasswordStrength.STRONG]

    def test_calculate_strength_strong(self) -> None:
        """Test password strength calculation - strong."""
        strength = PasswordGenerator.calculate_strength("Str0ng!Pass#2024")
        assert strength in [PasswordStrength.STRONG, PasswordStrength.VERY_STRONG]

    def test_calculate_strength_very_strong(self) -> None:
        """Test password strength calculation - very strong."""
        strength = PasswordGenerator.calculate_strength("V3ry$tr0ng!P@ssw0rd#2024")
        assert strength == PasswordStrength.VERY_STRONG

    def test_generate_passphrase(self) -> None:
        """Test passphrase generation."""
        passphrase = PasswordGenerator.generate_passphrase(word_count=4)
        
        words = passphrase.split("-")
        assert len(words) == 4
        assert all(word.isalpha() for word in words)

    def test_generate_passphrase_custom_separator(self) -> None:
        """Test passphrase generation with custom separator."""
        passphrase = PasswordGenerator.generate_passphrase(
            word_count=3, separator="_"
        )
        
        words = passphrase.split("_")
        assert len(words) == 3

    def test_generate_passphrase_no_capitalize(self) -> None:
        """Test passphrase generation without capitalization."""
        passphrase = PasswordGenerator.generate_passphrase(
            word_count=4, capitalize=False
        )
        
        assert passphrase.islower() or passphrase.replace("-", "").islower()
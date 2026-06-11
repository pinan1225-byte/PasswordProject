"""Password generation and strength validation."""

import secrets
import string
from enum import Enum
from typing import List, Optional


_PASSPHRASE_WORDS = [
    "correct", "horse", "battery", "staple", "apple", "banana", "orange", "purple",
    "green", "blue", "happy", "sunny", "cloud", "river", "mountain", "forest", "ocean",
    "desert", "valley", "meadow", "silver", "golden", "thunder", "winter", "summer",
    "autumn", "spring", "falcon", "dragon", "castle", "bridge", "garden", "lantern",
    "marble", "crystal", "shadow", "breeze", "candle", "anchor", "compass", "mirror",
    "puzzle", "rocket", "jungle", "planet", "comet", "island", "harbor", "temple",
    "tiger", "eagle", "wolf", "panda", "koala", "parrot", "dolphin",
    "penguin", "jaguar", "leopard", "sparrow", "raven", "condor", "heron",
    "cobalt", "amber", "indigo", "scarlet", "violet", "crimson", "teal", "ivory",
    "onyx", "jade", "ruby", "sapphire", "topaz", "opal", "garnet", "quartz",
    "maple", "cedar", "willow", "birch", "aspen", "spruce", "laurel", "cypress",
    "pepper", "ginger", "clover", "thistle", "fern", "lotus", "cactus", "bamboo",
    "lightning", "tornado", "blizzard", "monsoon", "solstice", "eclipse",
    "horizon", "zenith", "aurora", "nebula", "galaxy", "cosmos", "stellar", "lunar",
]


class PasswordStrength(Enum):
    """Password strength levels."""

    VERY_WEAK = 1
    WEAK = 2
    FAIR = 3
    STRONG = 4
    VERY_STRONG = 5


class PasswordGenerator:
    """Generate secure passwords with configurable policies."""

    LOWERCASE = string.ascii_lowercase
    UPPERCASE = string.ascii_uppercase
    DIGITS = string.digits
    SPECIAL = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    AMBIGUOUS = "0O1lI"

    def __init__(
        self,
        length: int = 16,
        use_uppercase: bool = True,
        use_lowercase: bool = True,
        use_digits: bool = True,
        use_special: bool = True,
        exclude_ambiguous: bool = True,
        min_uppercase: int = 1,
        min_lowercase: int = 1,
        min_digits: int = 1,
        min_special: int = 1,
    ):
        """
        Initialize password generator with policy.

        Args:
            length: Password length
            use_uppercase: Include uppercase letters
            use_lowercase: Include lowercase letters
            use_digits: Include digits
            use_special: Include special characters
            exclude_ambiguous: Exclude ambiguous characters (0O1lI)
            min_uppercase: Minimum uppercase letters
            min_lowercase: Minimum lowercase letters
            min_digits: Minimum digits
            min_special: Minimum special characters
        """
        self.length = max(length, 8)
        self.use_uppercase = use_uppercase
        self.use_lowercase = use_lowercase
        self.use_digits = use_digits
        self.use_special = use_special
        self.exclude_ambiguous = exclude_ambiguous
        self.min_uppercase = min_uppercase if use_uppercase else 0
        self.min_lowercase = min_lowercase if use_lowercase else 0
        self.min_digits = min_digits if use_digits else 0
        self.min_special = min_special if use_special else 0

    def _get_character_set(self, char_type: str) -> str:
        """
        Get character set for given type, excluding ambiguous if needed.

        Args:
            char_type: Type of characters ('upper', 'lower', 'digits', 'special')

        Returns:
            Character set string
        """
        char_sets = {
            "upper": self.UPPERCASE,
            "lower": self.LOWERCASE,
            "digits": self.DIGITS,
            "special": self.SPECIAL,
        }

        chars = char_sets.get(char_type, "")

        if self.exclude_ambiguous:
            chars = "".join(c for c in chars if c not in self.AMBIGUOUS)

        return chars

    def generate(self) -> str:
        """
        Generate a secure random password.

        Returns:
            Generated password
        """
        password_chars: List[str] = []
        available_chars = ""

        if self.use_uppercase:
            upper_chars = self._get_character_set("upper")
            if upper_chars:
                for _ in range(self.min_uppercase):
                    password_chars.append(secrets.choice(upper_chars))
                available_chars += upper_chars

        if self.use_lowercase:
            lower_chars = self._get_character_set("lower")
            if lower_chars:
                for _ in range(self.min_lowercase):
                    password_chars.append(secrets.choice(lower_chars))
                available_chars += lower_chars

        if self.use_digits:
            digit_chars = self._get_character_set("digits")
            if digit_chars:
                for _ in range(self.min_digits):
                    password_chars.append(secrets.choice(digit_chars))
                available_chars += digit_chars

        if self.use_special:
            special_chars = self._get_character_set("special")
            if special_chars:
                for _ in range(self.min_special):
                    password_chars.append(secrets.choice(special_chars))
                available_chars += special_chars

        remaining_length = self.length - len(password_chars)
        for _ in range(remaining_length):
            password_chars.append(secrets.choice(available_chars))

        secrets.SystemRandom().shuffle(password_chars)

        return "".join(password_chars)

    @staticmethod
    def calculate_strength(password: str) -> PasswordStrength:
        """
        Calculate password strength.

        Args:
            password: Password to evaluate

        Returns:
            PasswordStrength enum value
        """
        score = 0

        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if len(password) >= 16:
            score += 1

        if any(c.islower() for c in password):
            score += 1
        if any(c.isupper() for c in password):
            score += 1
        if any(c.isdigit() for c in password):
            score += 1
        if any(c in PasswordGenerator.SPECIAL for c in password):
            score += 1

        if len(set(password)) / len(password) > 0.7:
            score += 1

        if score <= 2:
            return PasswordStrength.VERY_WEAK
        elif score <= 3:
            return PasswordStrength.WEAK
        elif score <= 5:
            return PasswordStrength.FAIR
        elif score <= 7:
            return PasswordStrength.STRONG
        else:
            return PasswordStrength.VERY_STRONG

    @staticmethod
    def generate_passphrase(
        word_count: int = 4, separator: str = "-", capitalize: bool = True
    ) -> str:
        """
        Generate a memorable passphrase.

        Args:
            word_count: Number of words
            separator: Word separator
            capitalize: Capitalize each word

        Returns:
            Generated passphrase
        """
        words = [secrets.choice(_PASSPHRASE_WORDS) for _ in range(word_count)]

        if capitalize:
            words = [w.capitalize() for w in words]

        return separator.join(words)
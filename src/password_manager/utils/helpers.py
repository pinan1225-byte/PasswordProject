"""Helper utility functions."""

import os


def clear_screen() -> None:
    """Clear the terminal screen."""
    os.system("clear" if os.name == "posix" else "cls")


def mask_string(text: str, visible_chars: int = 4) -> str:
    """
    Mask a string, showing only first and last few characters.

    Args:
        text: String to mask
        visible_chars: Number of visible characters at start and end

    Returns:
        Masked string
    """
    if len(text) <= visible_chars * 2:
        return "*" * len(text)

    return f"{text[:visible_chars]}{'*' * (len(text) - visible_chars * 2)}{text[-visible_chars:]}"
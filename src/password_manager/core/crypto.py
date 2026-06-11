"""Cryptographic operations for password encryption and decryption."""

import base64
import secrets
from typing import Optional, Tuple

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from src.password_manager.config import get_settings

_ph = PasswordHasher()


class CryptoManager:
    """Manage encryption and decryption operations using AES-256-GCM."""

    def __init__(self, master_password: str, salt: Optional[bytes] = None):
        """
        Initialize the crypto manager.

        Args:
            master_password: Master password for encryption
            salt: Optional salt for key derivation (will be generated if not provided)
        """
        self.settings = get_settings()
        self._master_password: Optional[bytearray] = bytearray(master_password.encode("utf-8"))
        self._salt = salt or self._generate_salt()
        self._key: Optional[bytes] = None

    @property
    def salt(self) -> bytes:
        """Get the salt used for key derivation."""
        return self._salt

    @staticmethod
    def _generate_salt() -> bytes:
        """Generate a cryptographically secure random salt."""
        return secrets.token_bytes(16)

    def _derive_key(self) -> bytes:
        """
        Derive encryption key from master password using PBKDF2.

        Returns:
            Derived 256-bit key
        """
        if self._key is None:
            if self._master_password is None:
                raise ValueError("Master password has been cleared")
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=self.settings.AES_KEY_SIZE,
                salt=self._salt,
                iterations=self.settings.ENCRYPTION_ITERATIONS,
                backend=default_backend(),
            )
            self._key = kdf.derive(bytes(self._master_password))
        return self._key

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext using AES-256-GCM.

        Args:
            plaintext: Text to encrypt

        Returns:
            Base64 encoded ciphertext (nonce + tag + ciphertext)
        """
        key = self._derive_key()
        nonce = secrets.token_bytes(12)

        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
        encryptor = cipher.encryptor()

        ciphertext = encryptor.update(plaintext.encode("utf-8")) + encryptor.finalize()

        encrypted_data = nonce + encryptor.tag + ciphertext
        return base64.b64encode(encrypted_data).decode("utf-8")

    def decrypt(self, encrypted_text: str) -> str:
        """
        Decrypt ciphertext using AES-256-GCM.

        Args:
            encrypted_text: Base64 encoded ciphertext

        Returns:
            Decrypted plaintext

        Raises:
            ValueError: If decryption fails
        """
        key = self._derive_key()

        try:
            encrypted_data = base64.b64decode(encrypted_text.encode("utf-8"))

            nonce = encrypted_data[:12]
            tag = encrypted_data[12:28]
            ciphertext = encrypted_data[28:]

            cipher = Cipher(
                algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend()
            )
            decryptor = cipher.decryptor()

            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            return plaintext.decode("utf-8")

        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}") from e

    @staticmethod
    def hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[str, bytes]:
        """
        Hash password using Argon2id.

        Args:
            password: Password to hash
            salt: Ignored (Argon2 manages its own salt internally); kept for API compatibility

        Returns:
            Tuple of (argon2_hash_string, empty_bytes) — the hash string embeds the salt
        """
        hashed = _ph.hash(password)
        return hashed, b""

    @staticmethod
    def verify_password(password: str, hashed_password: str, salt: bytes) -> bool:
        """
        Verify password against Argon2 hash.

        Args:
            password: Password to verify
            hashed_password: Stored Argon2 hash string
            salt: Unused (Argon2 embeds salt in hash string); kept for API compatibility

        Returns:
            True if password matches
        """
        try:
            return _ph.verify(hashed_password, password)
        except VerifyMismatchError:
            return False

    def clear_key(self) -> None:
        """Clear the encryption key and master password from memory."""
        if self._key is not None:
            self._key = b"\x00" * len(self._key)
            self._key = None
        if self._master_password is not None:
            for i in range(len(self._master_password)):
                self._master_password[i] = 0
            self._master_password = None
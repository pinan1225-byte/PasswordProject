"""Unit tests for CryptoManager."""

import pytest
from src.password_manager.core.crypto import CryptoManager


class TestCryptoManager:
    """Test cases for CryptoManager."""

    def test_encrypt_decrypt(self, test_master_password: str) -> None:
        """Test encryption and decryption."""
        crypto = CryptoManager(test_master_password)
        
        plaintext = "MySecretPassword123!"
        encrypted = crypto.encrypt(plaintext)
        
        assert encrypted != plaintext
        assert encrypted != ""
        
        decrypted = crypto.decrypt(encrypted)
        assert decrypted == plaintext
        
        crypto.clear_key()

    def test_encrypt_different_ciphertexts(self, test_master_password: str) -> None:
        """Test that same plaintext produces different ciphertexts."""
        crypto = CryptoManager(test_master_password)
        
        plaintext = "SamePassword"
        encrypted1 = crypto.encrypt(plaintext)
        encrypted2 = crypto.encrypt(plaintext)
        
        assert encrypted1 != encrypted2
        
        assert crypto.decrypt(encrypted1) == plaintext
        assert crypto.decrypt(encrypted2) == plaintext
        
        crypto.clear_key()

    def test_decrypt_invalid_data(self, test_master_password: str) -> None:
        """Test decryption with invalid data."""
        crypto = CryptoManager(test_master_password)
        
        with pytest.raises(ValueError):
            crypto.decrypt("invalid_base64_data")
        
        crypto.clear_key()

    def test_hash_password(self) -> None:
        """Test password hashing with Argon2."""
        password = "TestPassword123"

        hashed1, _ = CryptoManager.hash_password(password)
        hashed2, _ = CryptoManager.hash_password(password)

        # Argon2 uses a random salt internally — same password produces different hashes
        assert hashed1 != hashed2

        hashed, salt = CryptoManager.hash_password(password)
        assert CryptoManager.verify_password(password, hashed, salt)

    def test_verify_password(self) -> None:
        """Test password verification."""
        password = "TestPassword123"
        wrong_password = "WrongPassword456"
        
        hashed, salt = CryptoManager.hash_password(password)
        
        assert CryptoManager.verify_password(password, hashed, salt)
        assert not CryptoManager.verify_password(wrong_password, hashed, salt)

    def test_clear_key(self, test_master_password: str) -> None:
        """Test key and master password clearing."""
        crypto = CryptoManager(test_master_password)

        crypto.encrypt("test")

        crypto.clear_key()

        # After clear_key, both key and master password are wiped
        assert crypto._key is None
        assert crypto._master_password is None

        # Attempting to encrypt after clearing should raise
        with pytest.raises(ValueError, match="Master password has been cleared"):
            crypto.encrypt("test")
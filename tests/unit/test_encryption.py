"""Unit tests for token encryption utilities."""

import pytest
from app.auth.encryption import (
    encrypt_token,
    decrypt_token,
    get_encryption_key,
    is_encrypted,
    EncryptionError
)


@pytest.mark.unit
class TestEncryptionKey:
    """Test encryption key derivation."""
    
    def test_get_encryption_key_returns_bytes(self):
        """Test that get_encryption_key returns bytes."""
        key = get_encryption_key("test-secret-key")
        assert isinstance(key, bytes)
        assert len(key) == 44  # Fernet keys are 32 bytes base64-encoded (44 chars)
    
    def test_get_encryption_key_consistent(self):
        """Test that same secret key produces same encryption key."""
        secret = "test-secret-key-123"
        key1 = get_encryption_key(secret)
        key2 = get_encryption_key(secret)
        assert key1 == key2
    
    def test_get_encryption_key_different_secrets(self):
        """Test that different secrets produce different keys."""
        key1 = get_encryption_key("secret1")
        key2 = get_encryption_key("secret2")
        assert key1 != key2


@pytest.mark.unit
class TestEncryptToken:
    """Test token encryption."""
    
    def test_encrypt_token_returns_string(self):
        """Test that encrypt_token returns a string."""
        encrypted = encrypt_token("test-token", "test-secret")
        assert isinstance(encrypted, str)
        assert len(encrypted) > 0
    
    def test_encrypt_token_different_tokens(self):
        """Test that different tokens produce different encrypted values."""
        secret = "test-secret"
        encrypted1 = encrypt_token("token1", secret)
        encrypted2 = encrypt_token("token2", secret)
        assert encrypted1 != encrypted2
    
    def test_encrypt_token_same_token_different_iv(self):
        """Test that same token encrypted twice produces different ciphertext (due to IV)."""
        secret = "test-secret"
        token = "same-token"
        encrypted1 = encrypt_token(token, secret)
        encrypted2 = encrypt_token(token, secret)
        # Should be different due to random IV, but both should decrypt to same value
        assert encrypted1 != encrypted2
        assert decrypt_token(encrypted1, secret) == decrypt_token(encrypted2, secret)
    
    def test_encrypt_token_raises_on_none(self):
        """Test that encrypt_token raises ValueError for None token."""
        with pytest.raises(ValueError, match="Cannot encrypt None token"):
            encrypt_token(None, "test-secret")
    
    def test_encrypt_token_handles_special_characters(self):
        """Test that encryption handles special characters in tokens."""
        token = "token-with-special-chars: !@#$%^&*()_+-=[]{}|;':\",./<>?"
        encrypted = encrypt_token(token, "test-secret")
        decrypted = decrypt_token(encrypted, "test-secret")
        assert decrypted == token
    
    def test_encrypt_token_handles_unicode(self):
        """Test that encryption handles unicode characters."""
        token = "token-with-unicode: 测试 🚀 émoji"
        encrypted = encrypt_token(token, "test-secret")
        decrypted = decrypt_token(encrypted, "test-secret")
        assert decrypted == token


@pytest.mark.unit
class TestDecryptToken:
    """Test token decryption."""
    
    def test_decrypt_token_roundtrip(self):
        """Test that encrypt/decrypt roundtrip works."""
        secret = "test-secret-key"
        original_token = "my-secret-token-123"
        encrypted = encrypt_token(original_token, secret)
        decrypted = decrypt_token(encrypted, secret)
        assert decrypted == original_token
    
    def test_decrypt_token_returns_none_for_none(self):
        """Test that decrypt_token returns None for None input."""
        result = decrypt_token(None, "test-secret")
        assert result is None
    
    def test_decrypt_token_wrong_key(self):
        """Test that decrypt_token raises EncryptionError with wrong key."""
        token = "test-token"
        encrypted = encrypt_token(token, "correct-secret")
        
        with pytest.raises(EncryptionError, match="Invalid encrypted token format or wrong key"):
            decrypt_token(encrypted, "wrong-secret")
    
    def test_decrypt_token_invalid_format(self):
        """Test that decrypt_token raises EncryptionError for invalid format."""
        with pytest.raises(EncryptionError):
            decrypt_token("not-a-valid-encrypted-token", "test-secret")
    
    def test_decrypt_token_corrupted_data(self):
        """Test that decrypt_token handles corrupted encrypted data."""
        # Create something that looks like base64 but isn't valid Fernet
        corrupted = "gAAAAABinvalid_base64_data_here"
        
        with pytest.raises(EncryptionError):
            decrypt_token(corrupted, "test-secret")
    
    def test_decrypt_token_empty_string(self):
        """Test that decrypt_token handles empty string."""
        with pytest.raises(EncryptionError):
            decrypt_token("", "test-secret")


@pytest.mark.unit
class TestIsEncrypted:
    """Test is_encrypted detection function."""
    
    def test_is_encrypted_returns_true_for_encrypted_token(self):
        """Test that is_encrypted returns True for encrypted tokens."""
        encrypted = encrypt_token("test-token", "test-secret")
        assert is_encrypted(encrypted) is True
    
    def test_is_encrypted_returns_false_for_plain_text(self):
        """Test that is_encrypted returns False for plain text."""
        assert is_encrypted("plain-text-token") is False
        assert is_encrypted("simple-token-123") is False
    
    def test_is_encrypted_returns_false_for_none(self):
        """Test that is_encrypted returns False for None."""
        assert is_encrypted(None) is False
    
    def test_is_encrypted_returns_false_for_empty_string(self):
        """Test that is_encrypted returns False for empty string."""
        assert is_encrypted("") is False
    
    def test_is_encrypted_returns_false_for_short_strings(self):
        """Test that is_encrypted returns False for strings that are too short."""
        assert is_encrypted("short") is False
        assert is_encrypted("a" * 20) is False
    
    def test_is_encrypted_returns_false_for_invalid_base64(self):
        """Test that is_encrypted returns False for invalid base64."""
        assert is_encrypted("not-valid-base64!!!") is False
    
    def test_is_encrypted_handles_fernet_prefix(self):
        """Test that is_encrypted detects Fernet tokens by prefix."""
        # Fernet tokens typically start with 'gAAAAA' when base64 encoded
        encrypted = encrypt_token("test", "secret")
        # Should start with gAAAAA
        assert encrypted.startswith("gAAAAA")
        assert is_encrypted(encrypted) is True


@pytest.mark.unit
class TestEncryptionIntegration:
    """Integration tests for encryption/decryption."""
    
    def test_multiple_encryptions_same_secret(self):
        """Test encrypting multiple tokens with same secret."""
        secret = "shared-secret"
        tokens = ["token1", "token2", "token3", "token4"]
        encrypted_tokens = [encrypt_token(t, secret) for t in tokens]
        decrypted_tokens = [decrypt_token(e, secret) for e in encrypted_tokens]
        
        assert decrypted_tokens == tokens
    
    def test_encryption_with_different_secrets(self):
        """Test that tokens encrypted with different secrets can't be decrypted cross-secret."""
        token = "secret-token"
        secret1 = "secret1"
        secret2 = "secret2"
        
        encrypted1 = encrypt_token(token, secret1)
        encrypted2 = encrypt_token(token, secret2)
        
        # Should decrypt correctly with matching secret
        assert decrypt_token(encrypted1, secret1) == token
        assert decrypt_token(encrypted2, secret2) == token
        
        # Should fail with wrong secret
        with pytest.raises(EncryptionError):
            decrypt_token(encrypted1, secret2)
        with pytest.raises(EncryptionError):
            decrypt_token(encrypted2, secret1)
    
    def test_long_token_encryption(self):
        """Test encryption of very long tokens."""
        long_token = "a" * 10000  # 10KB token
        encrypted = encrypt_token(long_token, "test-secret")
        decrypted = decrypt_token(encrypted, "test-secret")
        assert decrypted == long_token
    
    def test_encryption_preserves_token_format(self):
        """Test that encryption/decryption preserves token format."""
        tokens = [
            "Bearer abc123",
            "token-with-dashes",
            "token_with_underscores",
            "token.with.dots",
            "token123",
            "UPPERCASE-TOKEN",
            "mixedCaseToken"
        ]
        
        for token in tokens:
            encrypted = encrypt_token(token, "test-secret")
            decrypted = decrypt_token(encrypted, "test-secret")
            assert decrypted == token

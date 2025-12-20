"""Token encryption utilities for service authentication tokens."""

import hashlib
import base64
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionError(Exception):
    """Raised when encryption/decryption fails."""
    pass


def get_encryption_key(secret_key: str) -> bytes:
    """
    Derive a Fernet encryption key from the application secret key.
    
    Uses PBKDF2 with SHA-256 to derive a 32-byte key suitable for Fernet.
    
    Args:
        secret_key: Application secret key string
        
    Returns:
        32-byte key suitable for Fernet encryption
    """
    # Use PBKDF2 to derive a key from the secret
    # Salt is derived from the secret key itself for consistency
    salt = hashlib.sha256(secret_key.encode()).digest()[:16]
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
    return key


def encrypt_token(token: str, secret_key: str) -> str:
    """
    Encrypt a token using Fernet symmetric encryption.
    
    Args:
        token: Plain text token to encrypt
        secret_key: Application secret key for key derivation
        
    Returns:
        Base64-encoded encrypted token string
        
    Raises:
        EncryptionError: If encryption fails
    """
    if token is None:
        raise ValueError("Cannot encrypt None token")
    
    try:
        key = get_encryption_key(secret_key)
        fernet = Fernet(key)
        encrypted = fernet.encrypt(token.encode())
        return encrypted.decode('utf-8')
    except Exception as e:
        raise EncryptionError(f"Failed to encrypt token: {str(e)}") from e


def decrypt_token(encrypted_token: str, secret_key: str) -> Optional[str]:
    """
    Decrypt an encrypted token.
    
    Args:
        encrypted_token: Base64-encoded encrypted token string
        secret_key: Application secret key for key derivation
        
    Returns:
        Decrypted plain text token, or None if decryption fails
        
    Raises:
        EncryptionError: If decryption fails due to invalid format or key
    """
    if encrypted_token is None:
        return None
    
    try:
        key = get_encryption_key(secret_key)
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_token.encode())
        return decrypted.decode('utf-8')
    except InvalidToken:
        raise EncryptionError("Invalid encrypted token format or wrong key")
    except Exception as e:
        raise EncryptionError(f"Failed to decrypt token: {str(e)}") from e


def is_encrypted(value: str) -> bool:
    """
    Check if a value appears to be an encrypted token.
    
    Fernet tokens are base64-encoded strings with specific format.
    This checks for the basic structure but doesn't validate the key.
    
    Args:
        value: String value to check
        
    Returns:
        True if value appears to be encrypted, False otherwise
    """
    if not value or not isinstance(value, str):
        return False
    
    # Fernet tokens are base64-encoded and have a specific length
    # They typically start with 'gAAAAA' (base64 for Fernet header)
    # and are URL-safe base64 encoded
    try:
        # Check if it's valid base64
        decoded = base64.urlsafe_b64decode(value)
        # Fernet tokens are at least 57 bytes (32 bytes key + 16 bytes IV + overhead)
        if len(decoded) < 50:
            return False
        # Check for Fernet magic bytes (first byte is 0x80)
        if len(decoded) > 0 and decoded[0] == 0x80:
            return True
        # Also check if it starts with the typical Fernet prefix when base64 encoded
        if value.startswith('gAAAAA'):
            return True
        return False
    except Exception:
        # Not valid base64, definitely not encrypted
        return False


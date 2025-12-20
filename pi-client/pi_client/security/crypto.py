"""Encryption for communications and local data storage."""

import logging
import os
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64

from ..config import Config

logger = logging.getLogger(__name__)


class CryptoManager:
    """Manages encryption for data at rest and in transit."""
    
    def __init__(self, config: Config):
        """Initialize crypto manager."""
        self.config = config
        self.encryption_enabled = config.security.encryption_enabled
        self._cipher: Optional[Fernet] = None
        
        if self.encryption_enabled:
            self._initialize_cipher()
    
    def _initialize_cipher(self):
        """Initialize encryption cipher."""
        try:
            # Get or generate encryption key
            key_file = Path(self.config.security.cert_path).parent / "encryption.key"
            
            if key_file.exists():
                with open(key_file, "rb") as f:
                    key = f.read()
            else:
                # Generate new key
                key = Fernet.generate_key()
                key_file.parent.mkdir(parents=True, exist_ok=True)
                with open(key_file, "wb") as f:
                    f.write(key)
                key_file.chmod(0o600)
            
            self._cipher = Fernet(key)
            logger.info("Encryption cipher initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}", exc_info=True)
            self.encryption_enabled = False
    
    def encrypt_data(self, data: bytes) -> bytes:
        """Encrypt data.
        
        Args:
            data: Data to encrypt
        
        Returns:
            Encrypted data
        """
        if not self.encryption_enabled or not self._cipher:
            return data
        
        try:
            return self._cipher.encrypt(data)
        except Exception as e:
            logger.error(f"Encryption failed: {e}", exc_info=True)
            return data
    
    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """Decrypt data.
        
        Args:
            encrypted_data: Encrypted data
        
        Returns:
            Decrypted data
        """
        if not self.encryption_enabled or not self._cipher:
            return encrypted_data
        
        try:
            return self._cipher.decrypt(encrypted_data)
        except Exception as e:
            logger.error(f"Decryption failed: {e}", exc_info=True)
            return encrypted_data
    
    def encrypt_file(self, file_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """Encrypt a file.
        
        Args:
            file_path: Path to file to encrypt
            output_path: Optional output path. If None, adds .encrypted extension
        
        Returns:
            Path to encrypted file or None if failed
        """
        try:
            input_file = Path(file_path)
            if not input_file.exists():
                logger.error(f"File not found: {file_path}")
                return None
            
            if output_path is None:
                output_file = input_file.with_suffix(input_file.suffix + ".encrypted")
            else:
                output_file = Path(output_path)
            
            # Read and encrypt
            with open(input_file, "rb") as f:
                data = f.read()
            
            encrypted = self.encrypt_data(data)
            
            # Write encrypted file
            with open(output_file, "wb") as f:
                f.write(encrypted)
            
            logger.info(f"File encrypted: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Failed to encrypt file: {e}", exc_info=True)
            return None
    
    def decrypt_file(self, encrypted_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """Decrypt a file.
        
        Args:
            encrypted_path: Path to encrypted file
            output_path: Optional output path. If None, removes .encrypted extension
        
        Returns:
            Path to decrypted file or None if failed
        """
        try:
            input_file = Path(encrypted_path)
            if not input_file.exists():
                logger.error(f"File not found: {encrypted_path}")
                return None
            
            if output_path is None:
                if input_file.suffix == ".encrypted":
                    output_file = input_file.with_suffix("")
                else:
                    output_file = input_file.with_suffix(input_file.suffix + ".decrypted")
            else:
                output_file = Path(output_path)
            
            # Read and decrypt
            with open(input_file, "rb") as f:
                encrypted_data = f.read()
            
            decrypted = self.decrypt_data(encrypted_data)
            
            # Write decrypted file
            with open(output_file, "wb") as f:
                f.write(decrypted)
            
            logger.info(f"File decrypted: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Failed to decrypt file: {e}", exc_info=True)
            return None



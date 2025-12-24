"""Certificate management for device certificates."""

import logging
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime, timedelta, timezone
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

from ..config import Config

logger = logging.getLogger(__name__)


class CertificateManager:
    """Manages device certificates for authentication."""
    
    def __init__(self, config: Config):
        """Initialize certificate manager."""
        self.config = config
        self.cert_path = Path(config.security.cert_path)
        self.key_path = self.cert_path.parent / "device_key.pem"
        self.cert: Optional[x509.Certificate] = None
        self.private_key: Optional[rsa.RSAPrivateKey] = None
    
    def generate_certificate(
        self,
        device_id: str,
        organization: str = "Educational Platform",
        validity_days: int = 365
    ) -> Tuple[bytes, bytes]:
        """Generate a new device certificate.
        
        Args:
            device_id: Device identifier
            organization: Organization name
            validity_days: Certificate validity in days
        
        Returns:
            Tuple of (certificate_bytes, private_key_bytes)
        """
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
            x509.NameAttribute(NameOID.COMMON_NAME, device_id),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.now(timezone.utc)
        ).not_valid_after(
            datetime.now(timezone.utc) + timedelta(days=validity_days)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(device_id),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256(), default_backend())
        
        # Serialize
        cert_bytes = cert.public_bytes(serialization.Encoding.PEM)
        key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        logger.info(f"Generated certificate for device {device_id}")
        return cert_bytes, key_bytes
    
    def save_certificate(self, cert_bytes: bytes, key_bytes: bytes) -> bool:
        """Save certificate and key to files."""
        try:
            self.cert_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.cert_path, "wb") as f:
                f.write(cert_bytes)
            
            with open(self.key_path, "wb") as f:
                f.write(key_bytes)
            
            # Set restrictive permissions
            self.cert_path.chmod(0o644)
            self.key_path.chmod(0o600)
            
            logger.info(f"Certificate saved to {self.cert_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save certificate: {e}", exc_info=True)
            return False
    
    def load_certificate(self) -> bool:
        """Load certificate and key from files."""
        try:
            if not self.cert_path.exists() or not self.key_path.exists():
                return False
            
            with open(self.cert_path, "rb") as f:
                cert_data = f.read()
                self.cert = x509.load_pem_x509_certificate(cert_data, default_backend())
            
            with open(self.key_path, "rb") as f:
                key_data = f.read()
                self.private_key = serialization.load_pem_private_key(
                    key_data,
                    password=None,
                    backend=default_backend()
                )
            
            logger.info("Certificate loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load certificate: {e}", exc_info=True)
            return False
    
    def get_certificate_fingerprint(self) -> Optional[str]:
        """Get certificate fingerprint."""
        if not self.cert:
            if not self.load_certificate():
                return None
        
        fingerprint = self.cert.fingerprint(hashes.SHA256())
        return fingerprint.hex()
    
    def is_certificate_valid(self) -> bool:
        """Check if certificate is valid and not expired."""
        if not self.cert:
            if not self.load_certificate():
                return False
        
        now = datetime.now(timezone.utc)
        return self.cert.not_valid_before <= now <= self.cert.not_valid_after
    
    def needs_renewal(self, days_before_expiry: int = 30) -> bool:
        """Check if certificate needs renewal."""
        if not self.cert:
            if not self.load_certificate():
                return True  # Need to generate
        
        expiry = self.cert.not_valid_after
        renewal_date = expiry - timedelta(days=days_before_expiry)
        return datetime.now(timezone.utc) >= renewal_date








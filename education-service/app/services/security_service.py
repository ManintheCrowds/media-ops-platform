"""Security service for certificate management and remote wipe."""

from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.pi_device import PiDevice, DeviceCertificate, SecurityStatus
from cryptography import x509
from cryptography.hazmat.backends import default_backend


class SecurityService:
    """Service for device security operations."""
    
    @staticmethod
    def register_certificate(
        db: Session,
        device_id: int,
        certificate_data: str,
        fingerprint: str
    ) -> DeviceCertificate:
        """Register a device certificate."""
        # Check if certificate already exists
        existing = db.query(DeviceCertificate).filter(
            DeviceCertificate.fingerprint == fingerprint
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Certificate with this fingerprint already exists"
            )
        
        # Parse certificate to get expiration
        try:
            cert = x509.load_pem_x509_certificate(
                certificate_data.encode(),
                default_backend()
            )
            expires_at = cert.not_valid_after
        except Exception as e:
            # Default to 1 year if parsing fails
            expires_at = datetime.utcnow() + timedelta(days=365)
        
        # Create certificate record
        device_cert = DeviceCertificate(
            device_id=device_id,
            certificate_data=certificate_data,
            fingerprint=fingerprint,
            expires_at=expires_at,
            revoked=False
        )
        
        db.add(device_cert)
        
        # Update device
        device = db.query(PiDevice).filter(PiDevice.id == device_id).first()
        if device:
            device.certificate_fingerprint = fingerprint
            device.security_status = SecurityStatus.ACTIVE
            device.last_seen = datetime.utcnow()
        
        db.commit()
        db.refresh(device_cert)
        
        return device_cert
    
    @staticmethod
    def renew_certificate(
        db: Session,
        device_id: int,
        certificate_data: str,
        fingerprint: str
    ) -> DeviceCertificate:
        """Renew a device certificate."""
        # Revoke old certificate
        old_cert = db.query(DeviceCertificate).filter(
            DeviceCertificate.device_id == device_id,
            DeviceCertificate.revoked == False
        ).first()
        
        if old_cert:
            old_cert.revoked = True
        
        # Register new certificate
        return SecurityService.register_certificate(
            db,
            device_id,
            certificate_data,
            fingerprint
        )
    
    @staticmethod
    def validate_certificate(
        db: Session,
        fingerprint: str
    ) -> bool:
        """Validate device certificate."""
        cert = db.query(DeviceCertificate).filter(
            DeviceCertificate.fingerprint == fingerprint,
            DeviceCertificate.revoked == False
        ).first()
        
        if not cert:
            return False
        
        # Check expiration
        if cert.expires_at < datetime.utcnow():
            return False
        
        # Check device status
        device = db.query(PiDevice).filter(PiDevice.id == cert.device_id).first()
        if not device or device.security_status != SecurityStatus.ACTIVE:
            return False
        
        return True
    
    @staticmethod
    def initiate_wipe(
        db: Session,
        device_id: int
    ):
        """Initiate remote wipe for device."""
        device = db.query(PiDevice).filter(PiDevice.id == device_id).first()
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Set security status to wiped
        device.security_status = SecurityStatus.WIPED
        
        # Revoke all certificates
        certificates = db.query(DeviceCertificate).filter(
            DeviceCertificate.device_id == device_id
        ).all()
        
        for cert in certificates:
            cert.revoked = True
        
        db.commit()
    
    @staticmethod
    def revoke_certificate(
        db: Session,
        fingerprint: str
    ):
        """Revoke a certificate."""
        cert = db.query(DeviceCertificate).filter(
            DeviceCertificate.fingerprint == fingerprint
        ).first()
        
        if not cert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certificate not found"
            )
        
        cert.revoked = True
        
        # Update device security status
        device = db.query(PiDevice).filter(PiDevice.id == cert.device_id).first()
        if device:
            device.security_status = SecurityStatus.REVOKED
        
        db.commit()

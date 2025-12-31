"""Video encoder service for recording camera feeds."""

from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from app.models.encoder.encoder_models import VideoEncoder
from app.models.encoder.enums import EncoderStatus, EncoderDeviceType
from app.exceptions import (
    EncoderError,
    EncoderConnectionError,
    EncoderRecordingError
)
from .aja_client import AJAHELOClient
from .config import EncoderConfig

logger = logging.getLogger(__name__)


class VideoEncoderService:
    """Service for recording camera feeds using video encoders."""

    def __init__(self, config: Optional[EncoderConfig] = None):
        """Initialize video encoder service."""
        self.config = config or EncoderConfig()
        self._clients = {}  # Cache of encoder clients
        
        # Storage path for recordings
        self.storage_path = self.config.storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _get_encoder_client(self, encoder: VideoEncoder) -> AJAHELOClient:
        """Get or create encoder client for device."""
        cache_key = f"{encoder.ip_address}:{encoder.port}"
        if cache_key not in self._clients:
            try:
                self._clients[cache_key] = AJAHELOClient(
                    encoder.ip_address,
                    encoder.port,
                    self.config.encoder_timeout
                )
                logger.info(f"Encoder client initialized: {encoder.ip_address}")
            except Exception as e:
                raise EncoderConnectionError(f"Failed to initialize encoder client: {str(e)}")
        
        return self._clients[cache_key]

    async def discover_encoders(self, db: Session, network_range: Optional[str] = None) -> List[Dict]:
        """Discover encoders on the network."""
        import ipaddress
        import aiohttp
        import asyncio
        
        network = network_range or self.config.encoder_network_scan_range
        logger.info(f"Scanning network for encoders: {network}")
        
        network_obj = ipaddress.ip_network(network, strict=False)
        discovered = []
        
        async def probe_ip(ip: str) -> Optional[Dict]:
            """Probe a single IP for encoder."""
            timeout = aiohttp.ClientTimeout(total=2)
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    url = f"http://{ip}/api/v1/status/system"
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            return {
                                'ip_address': ip,
                                'port': 80,
                                'device_type': EncoderDeviceType.AJA_HELO.value,
                                'status': EncoderStatus.ONLINE.value,
                                'device_info': data
                            }
            except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, KeyError) as e:
                logger.debug(f"Failed to probe encoder at {ip}: {e}")
                pass
            return None
        
        tasks = [probe_ip(str(ip)) for ip in network_obj.hosts()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, dict) and result:
                discovered.append(result)
        
        logger.info(f"Discovered {len(discovered)} encoders")
        return discovered

    async def register_encoder(self, db: Session, encoder_data: Dict) -> Dict:
        """Register encoder in database."""
        required_fields = ['ip_address', 'name']
        for field in required_fields:
            if field not in encoder_data:
                raise EncoderError(f"Missing required field: {field}")
        
        # Check if encoder already exists
        existing = db.query(VideoEncoder).filter_by(ip_address=encoder_data['ip_address']).first()
        if existing:
            # Update existing encoder
            existing.name = encoder_data.get('name', existing.name)
            existing.port = encoder_data.get('port', 80)
            existing.device_type = EncoderDeviceType[encoder_data.get('device_type', 'AJA_HELO').upper()]
            db.commit()
            return existing.to_dict()
        
        # Create new encoder
        encoder = VideoEncoder(
            name=encoder_data['name'],
            ip_address=encoder_data['ip_address'],
            port=encoder_data.get('port', 80),
            device_type=EncoderDeviceType[encoder_data.get('device_type', 'AJA_HELO').upper()],
            status=EncoderStatus.UNKNOWN
        )
        
        db.add(encoder)
        db.commit()
        db.refresh(encoder)
        
        logger.info(f"Encoder registered: {encoder.id}, ip: {encoder.ip_address}")
        return encoder.to_dict()

    async def list_encoders(self, db: Session) -> List[Dict]:
        """List all registered encoders."""
        encoders = db.query(VideoEncoder).all()
        return [encoder.to_dict() for encoder in encoders]

    async def get_encoder(self, db: Session, encoder_id: int) -> Dict:
        """Get encoder details by ID."""
        encoder = db.query(VideoEncoder).filter_by(id=encoder_id).first()
        if not encoder:
            raise EncoderError(f"Encoder not found: {encoder_id}", encoder_id=str(encoder_id))
        return encoder.to_dict()

    async def record_stream(
        self,
        db: Session,
        encoder_id: int,
        source_url: str,
        output_path: Optional[str] = None,
        duration: Optional[int] = None
    ) -> Dict:
        """Record a stream to local storage."""
        encoder = db.query(VideoEncoder).filter_by(id=encoder_id).first()
        if not encoder:
            raise EncoderError(f"Encoder not found: {encoder_id}", encoder_id=str(encoder_id))
        
        if encoder.is_recording:
            raise EncoderRecordingError(
                f"Encoder {encoder_id} is already recording",
                encoder_id=str(encoder_id)
            )
        
        try:
            client = self._get_encoder_client(encoder)
            
            # Configure recording
            output = output_path or str(self.storage_path / f"recording_{encoder_id}_{datetime.utcnow().timestamp()}.mp4")
            recording_config = {
                'source_url': source_url,
                'output_path': output,
                'duration': duration
            }
            
            await client.configure_recording(recording_config)
            await client.start_recording()
            
            # Update encoder status
            encoder.is_recording = True
            encoder.current_recording_path = output
            encoder.status = EncoderStatus.RECORDING
            db.commit()
            
            logger.info(f"Recording started on encoder {encoder_id}: {output}")
            return {
                'status': 'recording',
                'encoder_id': encoder_id,
                'output_path': output,
                'source_url': source_url
            }
            
        except Exception as e:
            encoder.status = EncoderStatus.ERROR
            db.commit()
            raise EncoderRecordingError(
                f"Failed to start recording: {str(e)}",
                encoder_id=str(encoder_id)
            )

    async def stop_recording(self, db: Session, encoder_id: int) -> Dict:
        """Stop recording on encoder."""
        encoder = db.query(VideoEncoder).filter_by(id=encoder_id).first()
        if not encoder:
            raise EncoderError(f"Encoder not found: {encoder_id}", encoder_id=str(encoder_id))
        
        if not encoder.is_recording:
            raise EncoderRecordingError(
                f"Encoder {encoder_id} is not recording",
                encoder_id=str(encoder_id)
            )
        
        try:
            client = self._get_encoder_client(encoder)
            await client.stop_recording()
            
            # Update encoder status
            encoder.is_recording = False
            encoder.status = EncoderStatus.ONLINE
            recording_path = encoder.current_recording_path
            encoder.current_recording_path = None
            db.commit()
            
            logger.info(f"Recording stopped on encoder {encoder_id}")
            return {
                'status': 'stopped',
                'encoder_id': encoder_id,
                'recording_path': recording_path
            }
            
        except Exception as e:
            raise EncoderRecordingError(
                f"Failed to stop recording: {str(e)}",
                encoder_id=str(encoder_id)
            )

    async def get_encoder_status(self, db: Session, encoder_id: int) -> Dict:
        """Get encoder health/status."""
        encoder = db.query(VideoEncoder).filter_by(id=encoder_id).first()
        if not encoder:
            raise EncoderError(f"Encoder not found: {encoder_id}", encoder_id=str(encoder_id))
        
        try:
            client = self._get_encoder_client(encoder)
            status_info = await client.get_full_status()
            
            # Update encoder status
            if status_info.get('recording'):
                encoder.is_recording = True
                encoder.status = EncoderStatus.RECORDING
            elif status_info.get('streaming'):
                encoder.is_streaming = True
                encoder.status = EncoderStatus.STREAMING
            else:
                encoder.is_recording = False
                encoder.is_streaming = False
                encoder.status = EncoderStatus.ONLINE
            
            db.commit()
            
            return {
                'encoder_id': encoder_id,
                'status': encoder.status.value,
                'is_recording': encoder.is_recording,
                'is_streaming': encoder.is_streaming,
                'device_status': status_info
            }
            
        except Exception as e:
            encoder.status = EncoderStatus.ERROR
            db.commit()
            raise EncoderConnectionError(f"Failed to get encoder status: {str(e)}")


"""Arlo camera service for FastAPI."""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import logging
import ipaddress
import socket
import asyncio
import aiohttp
from sqlalchemy.orm import Session

from app.models.camera.arlo_models import (
    ArloBaseStation,
    ArloCamera,
    ArloRecording,
    ArloEvent
)
from app.models.camera.enums import ArloStatus, ArloEventType
from app.exceptions import (
    ArloError,
    ArloConnectionError,
    ArloCameraError,
    ArloRecordingError
)
from .config import CameraConfig

try:
    from Arlo import Arlo
except ImportError:
    try:
        # Fallback: try local copy if pip install failed
        import sys
        from pathlib import Path
        arlo_module_path = Path(__file__).parent / 'arlo_module.py'
        if arlo_module_path.exists():
            import importlib.util
            spec = importlib.util.spec_from_file_location("Arlo", arlo_module_path)
            arlo_module = importlib.util.module_from_spec(spec)
            sys.modules["Arlo"] = arlo_module
            spec.loader.exec_module(arlo_module)
            Arlo = arlo_module.Arlo
        else:
            Arlo = None
    except Exception:
        Arlo = None

logger = logging.getLogger(__name__)


class ArloService:
    """Arlo camera management service (FastAPI version)."""

    def __init__(self, config: Optional[CameraConfig] = None):
        """Initialize Arlo service."""
        self.config = config or CameraConfig()
        self._clients = {}  # Cache of Arlo clients per base station
        
        # Storage path for recordings
        self.storage_path = self.config.path
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _get_arlo_client(self, username: Optional[str] = None, password: Optional[str] = None) -> 'Arlo':
        """Get or create Arlo client instance."""
        if Arlo is None:
            raise ArloConnectionError(
                "Arlo library not installed. Install with: pip install git+https://github.com/jeffreydwalter/arlo.git"
            )
        
        # Use provided credentials or get from config
        username = username or self.config.arlo_username
        password = password or self.config.arlo_password
        
        if not username or not password:
            raise ArloConnectionError(
                "Arlo credentials not configured. Set ARLO_USERNAME and ARLO_PASSWORD environment variables."
            )
        
        # Cache client by username
        cache_key = username
        if cache_key not in self._clients:
            try:
                self._clients[cache_key] = Arlo(username, password)
                logger.info("Arlo client initialized", extra={"username": username})
            except Exception as e:
                raise ArloConnectionError(f"Failed to initialize Arlo client: {str(e)}")
        
        return self._clients[cache_key]

    async def discover_cameras(self, db: Session) -> List[Dict]:
        """Discover cameras from Arlo base station."""
        try:
            arlo = self._get_arlo_client()
            
            # Get devices from Arlo
            devices = arlo.GetDevices()
            
            cameras = []
            for device in devices:
                if device.get('deviceType') in ['arloq', 'arlopro', 'arloqs', 'arlobaby', 'arlo']:
                    cameras.append({
                        'device_id': device.get('deviceId'),
                        'device_type': device.get('deviceType'),
                        'name': device.get('deviceName', f"Camera {device.get('deviceId')}"),
                        'status': ArloStatus.ONLINE.value if device.get('state') == 'provisioned' else ArloStatus.OFFLINE.value,
                        'is_armed': device.get('properties', {}).get('armed', False),
                        'battery_level': device.get('properties', {}).get('batteryLevel', None),
                        'signal_strength': device.get('properties', {}).get('signalStrength', None)
                    })
            
            logger.info(f"Discovered {len(cameras)} cameras")
            return cameras
            
        except Exception as e:
            logger.error(f"Failed to discover cameras: {str(e)}")
            raise ArloConnectionError(f"Failed to discover cameras: {str(e)}")

    async def register_camera(self, db: Session, camera_data: Dict) -> Dict:
        """Register discovered camera in database."""
        required_fields = ['device_id', 'device_type', 'name']
        for field in required_fields:
            if field not in camera_data:
                raise ArloError(f"Missing required field: {field}")
        
        # Check if camera already exists
        existing = db.query(ArloCamera).filter_by(device_id=camera_data['device_id']).first()
        if existing:
            # Update existing camera
            existing.name = camera_data.get('name', existing.name)
            existing.device_type = camera_data.get('device_type', existing.device_type)
            status_str = camera_data.get('status', 'UNKNOWN').upper()
            existing.status = ArloStatus[status_str] if hasattr(ArloStatus, status_str) else ArloStatus.UNKNOWN
            existing.is_armed = camera_data.get('is_armed', existing.is_armed)
            existing.battery_level = camera_data.get('battery_level')
            existing.signal_strength = camera_data.get('signal_strength')
            db.commit()
            return existing.to_dict()
        
        # Get or create base station
        base_station = db.query(ArloBaseStation).first()
        if not base_station:
            # Create default base station
            base_station = ArloBaseStation(
                name="Default Arlo Base Station",
                serial_number="default",
                status=ArloStatus.ONLINE
            )
            db.add(base_station)
            db.flush()
        
        # Create new camera
        status_str = camera_data.get('status', 'UNKNOWN').upper()
        status = ArloStatus[status_str] if hasattr(ArloStatus, status_str) else ArloStatus.UNKNOWN
        
        camera = ArloCamera(
            base_station_id=base_station.id,
            name=camera_data['name'],
            device_id=camera_data['device_id'],
            device_type=camera_data['device_type'],
            status=status,
            is_armed=camera_data.get('is_armed', False),
            battery_level=camera_data.get('battery_level'),
            signal_strength=camera_data.get('signal_strength')
        )
        
        db.add(camera)
        db.commit()
        db.refresh(camera)
        
        logger.info(f"Camera registered: {camera.id}, device_id: {camera.device_id}")
        return camera.to_dict()

    async def list_cameras(self, db: Session) -> List[Dict]:
        """List all registered cameras with status."""
        cameras = db.query(ArloCamera).all()
        return [camera.to_dict() for camera in cameras]

    async def get_camera(self, db: Session, camera_id: int) -> Dict:
        """Get camera details by ID."""
        camera = db.query(ArloCamera).filter_by(id=camera_id).first()
        if not camera:
            raise ArloCameraError(f"Camera not found: {camera_id}", camera_id=str(camera_id))
        return camera.to_dict()

    async def arm_camera(self, db: Session, camera_id: int) -> Dict:
        """Enable motion detection on camera."""
        camera = db.query(ArloCamera).filter_by(id=camera_id).first()
        if not camera:
            raise ArloCameraError(f"Camera not found: {camera_id}", camera_id=str(camera_id))
        
        try:
            arlo = self._get_arlo_client()
            
            # Arm the camera
            arlo.Arm(camera.device_id)
            
            camera.is_armed = True
            db.commit()
            
            logger.info(f"Camera armed: {camera_id}")
            return camera.to_dict()
            
        except Exception as e:
            raise ArloCameraError(f"Failed to arm camera: {str(e)}", camera_id=str(camera_id))

    async def disarm_camera(self, db: Session, camera_id: int) -> Dict:
        """Disable motion detection on camera."""
        camera = db.query(ArloCamera).filter_by(id=camera_id).first()
        if not camera:
            raise ArloCameraError(f"Camera not found: {camera_id}", camera_id=str(camera_id))
        
        try:
            arlo = self._get_arlo_client()
            
            # Disarm the camera
            arlo.Disarm(camera.device_id)
            
            camera.is_armed = False
            db.commit()
            
            logger.info(f"Camera disarmed: {camera_id}")
            return camera.to_dict()
            
        except Exception as e:
            raise ArloCameraError(f"Failed to disarm camera: {str(e)}", camera_id=str(camera_id))

    async def capture_snapshot(self, db: Session, camera_id: int) -> Dict:
        """Take snapshot from camera."""
        camera = db.query(ArloCamera).filter_by(id=camera_id).first()
        if not camera:
            raise ArloCameraError(f"Camera not found: {camera_id}", camera_id=str(camera_id))
        
        try:
            arlo = self._get_arlo_client()
            
            # Capture snapshot
            snapshot_url = arlo.TriggerFullFrameSnapshot(camera.device_id)
            
            logger.info(f"Snapshot captured: {camera_id}, url: {snapshot_url}")
            return {
                'camera_id': camera_id,
                'snapshot_url': snapshot_url,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise ArloCameraError(f"Failed to capture snapshot: {str(e)}", camera_id=str(camera_id))

    async def get_library(
        self,
        db: Session,
        camera_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get recordings for date range."""
        camera = db.query(ArloCamera).filter_by(id=camera_id).first()
        if not camera:
            raise ArloCameraError(f"Camera not found: {camera_id}", camera_id=str(camera_id))
        
        try:
            arlo = self._get_arlo_client()
            
            # Parse dates
            start = datetime.fromisoformat(start_date) if start_date else datetime.utcnow() - timedelta(days=7)
            end = datetime.fromisoformat(end_date) if end_date else datetime.utcnow()
            
            # Get library from Arlo
            library = arlo.GetLibrary(camera.device_id, dateFrom=start, dateTo=end)
            
            recordings = []
            for recording in library[:limit]:
                # Check if recording exists in database
                existing = db.query(ArloRecording).filter_by(
                    recording_id=recording.get('name')
                ).first()
                
                if not existing:
                    # Create new recording record
                    recording_obj = ArloRecording(
                        camera_id=camera.id,
                        recording_id=recording.get('name'),
                        presigned_url=recording.get('presignedContentUrl'),
                        created_date=datetime.fromtimestamp(recording.get('utcCreatedDate', 0) / 1000),
                        duration=recording.get('mediaDurationSecond', 0),
                        file_size=recording.get('contentSize', 0),
                        downloaded=False
                    )
                    db.add(recording_obj)
                    recordings.append(recording_obj.to_dict())
                else:
                    recordings.append(existing.to_dict())
            
            db.commit()
            return recordings
            
        except Exception as e:
            raise ArloRecordingError(f"Failed to get library: {str(e)}", camera_id=str(camera_id))

    async def download_recording(self, db: Session, camera_id: int, recording_id: int) -> Dict:
        """Get recording download URL."""
        camera = db.query(ArloCamera).filter_by(id=camera_id).first()
        if not camera:
            raise ArloCameraError(f"Camera not found: {camera_id}", camera_id=str(camera_id))
        
        recording = db.query(ArloRecording).filter_by(
            camera_id=camera.id,
            id=recording_id
        ).first()
        
        if not recording:
            raise ArloRecordingError(
                f"Recording not found: {recording_id}",
                camera_id=str(camera_id)
            )
        
        # Return presigned URL for streaming
        return {
            'recording_id': recording.recording_id,
            'presigned_url': recording.presigned_url,
            'file_size': recording.file_size,
            'duration': recording.duration
        }

    async def delete_recording(self, db: Session, camera_id: int, recording_id: int) -> Dict:
        """Delete recording from Arlo cloud."""
        camera = db.query(ArloCamera).filter_by(id=camera_id).first()
        if not camera:
            raise ArloCameraError(f"Camera not found: {camera_id}", camera_id=str(camera_id))
        
        recording = db.query(ArloRecording).filter_by(
            camera_id=camera.id,
            id=recording_id
        ).first()
        
        if not recording:
            raise ArloRecordingError(
                f"Recording not found: {recording_id}",
                camera_id=str(camera_id)
            )
        
        try:
            arlo = self._get_arlo_client()
            
            # Delete from Arlo
            arlo.DeleteRecording(recording.recording_id)
            
            # Delete from database
            db.delete(recording)
            db.commit()
            
            logger.info(f"Recording deleted: {recording.recording_id}")
            return {'status': 'deleted', 'recording_id': recording.recording_id}
            
        except Exception as e:
            raise ArloRecordingError(
                f"Failed to delete recording: {str(e)}",
                camera_id=str(camera_id)
            )

    async def get_camera_status(self, db: Session, camera_id: int) -> Dict:
        """Get camera health/status."""
        camera = db.query(ArloCamera).filter_by(id=camera_id).first()
        if not camera:
            raise ArloCameraError(f"Camera not found: {camera_id}", camera_id=str(camera_id))
        
        try:
            arlo = self._get_arlo_client()
            
            # Get device status from Arlo
            devices = arlo.GetDevices()
            device = next((d for d in devices if d.get('deviceId') == camera.device_id), None)
            
            if device:
                # Update camera status
                camera.status = ArloStatus.ONLINE if device.get('state') == 'provisioned' else ArloStatus.OFFLINE
                camera.battery_level = device.get('properties', {}).get('batteryLevel')
                camera.signal_strength = device.get('properties', {}).get('signalStrength')
                db.commit()
            
            return {
                'camera_id': camera_id,
                'status': camera.status.value,
                'is_armed': camera.is_armed,
                'battery_level': camera.battery_level,
                'signal_strength': camera.signal_strength,
                'last_checked': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise ArloCameraError(f"Failed to get camera status: {str(e)}", camera_id=str(camera_id))

    async def get_base_station(self, db: Session) -> Dict:
        """Get base station info."""
        base_station = db.query(ArloBaseStation).first()
        if not base_station:
            raise ArloConnectionError("Base station not registered")
        
        return base_station.to_dict()

    async def start_live_stream(self, db: Session, camera_id: int) -> Dict:
        """Start live streaming if RTSP available."""
        camera = db.query(ArloCamera).filter_by(id=camera_id).first()
        if not camera:
            raise ArloCameraError(f"Camera not found: {camera_id}", camera_id=str(camera_id))
        
        try:
            arlo = self._get_arlo_client()
            
            # Start live stream
            stream_url = arlo.StartStream(camera.device_id)
            
            logger.info(f"Live stream started: {camera_id}, stream_url: {stream_url}")
            return {
                'camera_id': camera_id,
                'stream_url': stream_url,
                'status': 'streaming'
            }
            
        except Exception as e:
            raise ArloCameraError(f"Failed to start live stream: {str(e)}", camera_id=str(camera_id))

    async def scan_network(self, network: Optional[str] = None) -> List[Dict]:
        """Scan local network for Arlo base stations."""
        import socket
        
        # Get local network range if not provided
        if not network:
            # Try to detect local network
            try:
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                # Assume /24 subnet
                network = f"{'.'.join(local_ip.split('.')[:-1])}.0/24"
            except (socket.gaierror, OSError, ValueError) as e:
                logger.warning(f"Failed to determine local network, using default: {e}")
                network = "192.168.1.0/24"  # Default fallback
        
        logger.info(f"Scanning network for Arlo base stations: {network}")
        
        network_obj = ipaddress.ip_network(network, strict=False)
        discovered_devices = []
        
        # Arlo base stations typically use port 80 and may respond to HTTP requests
        tasks = []
        for ip in network_obj.hosts():
            tasks.append(self._probe_arlo_device(str(ip)))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, dict) and result:
                discovered_devices.append(result)
        
        logger.info(f"Network scan complete, found {len(discovered_devices)} devices")
        return discovered_devices

    async def _probe_arlo_device(self, ip: str) -> Optional[Dict]:
        """Probe a single IP address for Arlo base station."""
        timeout = aiohttp.ClientTimeout(total=2)
        
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Try HTTP endpoint (Arlo base stations may have web interface)
                urls_to_try = [
                    f"http://{ip}/",
                    f"http://{ip}/api",
                    f"http://{ip}/status",
                ]
                
                for url in urls_to_try:
                    try:
                        async with session.get(url, allow_redirects=False) as response:
                            # Check for Arlo-specific headers or response
                            server_header = response.headers.get('Server', '').lower()
                            if 'arlo' in server_header or response.status in [200, 401, 403]:
                                # Found potential Arlo device
                                device_info = {
                                    'ip_address': ip,
                                    'status': 'discovered',
                                    'http_status': response.status,
                                    'server': server_header,
                                    'timestamp': datetime.utcnow().isoformat()
                                }
                                
                                # Try to get more info
                                try:
                                    if response.status == 200:
                                        text = await response.text()
                                        if 'arlo' in text.lower() or 'netgear' in text.lower():
                                            device_info['confirmed'] = True
                                except (aiohttp.ClientError, asyncio.TimeoutError, UnicodeDecodeError) as e:
                                    logger.debug(f"Could not read response text for {ip}: {e}")
                                    pass
                                
                                return device_info
                    except asyncio.TimeoutError:
                        continue
                    except (aiohttp.ClientError, OSError, socket.error) as e:
                        logger.debug(f"Network error probing {ip}: {e}")
                        continue
                    except Exception as e:
                        logger.warning(f"Unexpected error probing {ip}: {e}", exc_info=True)
                        continue
        
        except Exception as e:
            logger.debug(f"Probe failed for {ip}: {str(e)}")
        
        return None


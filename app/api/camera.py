"""Camera API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from app.database import get_db

logger = logging.getLogger(__name__)
from app.auth.oauth2 import get_current_user
from app.models import User
from services.camera.arlo_service import ArloService
from app.exceptions import (
    ArloError,
    ArloConnectionError,
    ArloCameraError,
    ArloRecordingError
)

router = APIRouter(prefix="/api/camera", tags=["camera"])


# Pydantic models for request/response
class CameraResponse(BaseModel):
    """Camera response model."""
    id: int
    base_station_id: int
    name: str
    device_id: str
    device_type: Optional[str]
    status: Optional[str]
    is_armed: bool
    battery_level: Optional[int]
    signal_strength: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]
    
    class Config:
        from_attributes = True


class BaseStationResponse(BaseModel):
    """Base station response model."""
    id: int
    name: str
    serial_number: str
    ip_address: Optional[str]
    status: Optional[str]
    last_sync: Optional[str]
    camera_count: int
    created_at: Optional[str]
    updated_at: Optional[str]
    
    class Config:
        from_attributes = True


class RecordingResponse(BaseModel):
    """Recording response model."""
    id: int
    camera_id: int
    recording_id: str
    presigned_url: Optional[str]
    created_date: Optional[str]
    duration: Optional[int]
    file_size: Optional[int]
    downloaded: bool
    created_at: Optional[str]
    updated_at: Optional[str]
    
    class Config:
        from_attributes = True


class SnapshotResponse(BaseModel):
    """Snapshot response model."""
    camera_id: int
    snapshot_url: str
    timestamp: str


class StreamResponse(BaseModel):
    """Stream response model."""
    camera_id: int
    stream_url: str
    status: str


class DiscoverRequest(BaseModel):
    """Request model for camera discovery."""
    network_range: Optional[str] = None


@router.get("/cameras", response_model=List[CameraResponse])
async def list_cameras(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all registered cameras."""
    try:
        service = ArloService()
        cameras = await service.list_cameras(db)
        return cameras
    except ArloError as e:
        raise HTTPException(status_code=500, detail=str(e.message))


@router.get("/cameras/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get camera details by ID."""
    try:
        service = ArloService()
        camera = await service.get_camera(db, camera_id)
        return camera
    except ArloCameraError as e:
        raise HTTPException(status_code=404, detail=str(e.message))
    except ArloError as e:
        raise HTTPException(status_code=500, detail=str(e.message))


@router.post("/cameras/discover", response_model=List[CameraResponse])
async def discover_cameras(
    request: Optional[DiscoverRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Discover and register cameras from base station."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        service = ArloService()
        
        # Discover cameras
        discovered = await service.discover_cameras(db)
        
        # Register each camera
        registered = []
        for camera_data in discovered:
            try:
                registered_camera = await service.register_camera(db, camera_data)
                registered.append(registered_camera)
            except Exception as e:
                # Log error but continue with other cameras
                logger.error(f"Failed to register camera {camera_data.get('device_id')}: {str(e)}")
        
        return registered
    except ArloConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e.message))
    except ArloError as e:
        raise HTTPException(status_code=500, detail=str(e.message))


@router.post("/cameras/{camera_id}/arm", response_model=CameraResponse)
async def arm_camera(
    camera_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Arm camera (enable motion detection)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        service = ArloService()
        camera = await service.arm_camera(db, camera_id)
        return camera
    except ArloCameraError as e:
        raise HTTPException(status_code=404, detail=str(e.message))
    except ArloError as e:
        raise HTTPException(status_code=500, detail=str(e.message))


@router.post("/cameras/{camera_id}/disarm", response_model=CameraResponse)
async def disarm_camera(
    camera_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disarm camera (disable motion detection)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        service = ArloService()
        camera = await service.disarm_camera(db, camera_id)
        return camera
    except ArloCameraError as e:
        raise HTTPException(status_code=404, detail=str(e.message))
    except ArloError as e:
        raise HTTPException(status_code=500, detail=str(e.message))


@router.post("/cameras/{camera_id}/snapshot", response_model=SnapshotResponse)
async def capture_snapshot(
    camera_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Capture a snapshot from camera."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        service = ArloService()
        snapshot = await service.capture_snapshot(db, camera_id)
        return snapshot
    except ArloCameraError as e:
        raise HTTPException(status_code=404, detail=str(e.message))
    except ArloError as e:
        raise HTTPException(status_code=500, detail=str(e.message))


@router.get("/cameras/{camera_id}/status")
async def get_camera_status(
    camera_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get camera health/status."""
    try:
        service = ArloService()
        status_info = await service.get_camera_status(db, camera_id)
        return status_info
    except ArloCameraError as e:
        raise HTTPException(status_code=404, detail=str(e.message))
    except ArloError as e:
        raise HTTPException(status_code=500, detail=str(e.message))


@router.get("/cameras/{camera_id}/recordings", response_model=List[RecordingResponse])
async def get_recordings(
    camera_id: int,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of recordings"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List recordings for a specific camera."""
    try:
        service = ArloService()
        recordings = await service.get_library(db, camera_id, start_date, end_date, limit)
        return recordings
    except ArloCameraError as e:
        raise HTTPException(status_code=404, detail=str(e.message))
    except ArloError as e:
        raise HTTPException(status_code=500, detail=str(e.message))


@router.get("/cameras/{camera_id}/recordings/{recording_id}/download")
async def download_recording(
    camera_id: int,
    recording_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get download URL for a recording."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        service = ArloService()
        recording = await service.download_recording(db, camera_id, recording_id)
        return recording
    except (ArloCameraError, ArloRecordingError) as e:
        raise HTTPException(status_code=404, detail=str(e.message))
    except ArloError as e:
        raise HTTPException(status_code=500, detail=str(e.message))


@router.delete("/cameras/{camera_id}/recordings/{recording_id}")
async def delete_recording(
    camera_id: int,
    recording_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a recording from Arlo cloud."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        service = ArloService()
        result = await service.delete_recording(db, camera_id, recording_id)
        return result
    except (ArloCameraError, ArloRecordingError) as e:
        raise HTTPException(status_code=404, detail=str(e.message))
    except ArloError as e:
        raise HTTPException(status_code=500, detail=str(e.message))


@router.get("/base-station", response_model=BaseStationResponse)
async def get_base_station(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get information about the Arlo base station."""
    try:
        service = ArloService()
        base_station = await service.get_base_station(db)
        return base_station
    except ArloConnectionError as e:
        raise HTTPException(status_code=404, detail=str(e.message))
    except ArloError as e:
        raise HTTPException(status_code=500, detail=str(e.message))


@router.post("/cameras/{camera_id}/live-stream", response_model=StreamResponse)
async def start_live_stream(
    camera_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a live stream from an Arlo camera."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        service = ArloService()
        stream = await service.start_live_stream(db, camera_id)
        return stream
    except ArloCameraError as e:
        raise HTTPException(status_code=404, detail=str(e.message))
    except ArloError as e:
        raise HTTPException(status_code=500, detail=str(e.message))


@router.post("/scan-network")
async def scan_network(
    network_range: Optional[str] = Query(None, description="Network range (e.g., 192.168.1.0/24)"),
    current_user: User = Depends(get_current_user)
):
    """Scan local network for potential Arlo base stations."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        service = ArloService()
        discovered_devices = await service.scan_network(network_range)
        return {
            "message": "Network scan completed",
            "discovered_devices": discovered_devices
        }
    except ArloError as e:
        raise HTTPException(status_code=500, detail=str(e.message))


@router.post("/webhooks")
async def arlo_webhook_event(
    event_data: dict,
    db: Session = Depends(get_db)
):
    """Endpoint for Arlo to send event webhooks."""
    # Note: This would typically not require authentication for webhooks
    # but you may want to add webhook signature verification
    try:
        service = ArloService()
        # Process webhook event (implementation would handle event_data)
        return {"status": "success", "message": "Event processed"}
    except ArloError as e:
        raise HTTPException(status_code=500, detail=str(e.message))


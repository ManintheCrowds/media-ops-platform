"""Video encoder API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.auth.oauth2 import get_current_user
from app.models import User
from services.video_encoder.encoder_service import VideoEncoderService
from services.camera.recording_service import CameraRecordingService
from app.exceptions import EncoderError, EncoderConnectionError, EncoderRecordingError

router = APIRouter(prefix="/api/encoder", tags=["encoder"])


# Pydantic models
class EncoderResponse(BaseModel):
    """Encoder response model."""
    id: int
    name: str
    ip_address: str
    device_type: Optional[str]
    status: Optional[str]
    is_recording: bool
    is_streaming: bool
    current_recording_path: Optional[str]
    current_stream_url: Optional[str]
    storage_available: Optional[int]
    storage_used: Optional[int]
    port: int
    created_at: Optional[str]
    updated_at: Optional[str]
    
    class Config:
        from_attributes = True


class RecordingRequest(BaseModel):
    """Request model for starting recording."""
    source_url: str
    output_path: Optional[str] = None
    duration: Optional[int] = None


@router.get("/encoders", response_model=List[EncoderResponse])
async def list_encoders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all registered encoders."""
    try:
        service = VideoEncoderService()
        encoders = await service.list_encoders(db)
        return encoders
    except EncoderError as e:
        raise HTTPException(status_code=500, detail=str(e.message))


@router.get("/encoders/{encoder_id}", response_model=EncoderResponse)
async def get_encoder(
    encoder_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get encoder details by ID."""
    try:
        service = VideoEncoderService()
        encoder = await service.get_encoder(db, encoder_id)
        return encoder
    except EncoderError as e:
        raise HTTPException(status_code=404, detail=str(e.message))


@router.post("/encoders/discover")
async def discover_encoders(
    network_range: Optional[str] = Query(None, description="Network range (e.g., 192.168.1.0/24)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Discover encoders on the network."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        service = VideoEncoderService()
        discovered = await service.discover_encoders(db, network_range)
        return {
            "message": "Encoder discovery completed",
            "discovered": discovered
        }
    except EncoderError as e:
        raise HTTPException(status_code=500, detail=str(e.message))


@router.post("/encoders", response_model=EncoderResponse)
async def register_encoder(
    encoder_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register an encoder."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        service = VideoEncoderService()
        encoder = await service.register_encoder(db, encoder_data)
        return encoder
    except EncoderError as e:
        raise HTTPException(status_code=400, detail=str(e.message))


@router.post("/encoders/{encoder_id}/record")
async def start_recording(
    encoder_id: int,
    request: RecordingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start recording a stream on encoder."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        service = VideoEncoderService()
        recording = await service.record_stream(
            db=db,
            encoder_id=encoder_id,
            source_url=request.source_url,
            output_path=request.output_path,
            duration=request.duration
        )
        return recording
    except (EncoderError, EncoderRecordingError) as e:
        raise HTTPException(status_code=400, detail=str(e.message))


@router.post("/encoders/{encoder_id}/stop")
async def stop_recording(
    encoder_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stop recording on encoder."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        service = VideoEncoderService()
        result = await service.stop_recording(db, encoder_id)
        return result
    except (EncoderError, EncoderRecordingError) as e:
        raise HTTPException(status_code=400, detail=str(e.message))


@router.get("/encoders/{encoder_id}/status")
async def get_encoder_status(
    encoder_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get encoder health/status."""
    try:
        service = VideoEncoderService()
        status_info = await service.get_encoder_status(db, encoder_id)
        return status_info
    except EncoderError as e:
        raise HTTPException(status_code=404, detail=str(e.message))


@router.post("/cameras/{camera_id}/record")
async def record_camera(
    camera_id: int,
    encoder_id: int = Query(..., description="Encoder ID to use for recording"),
    duration: int = Query(3600, description="Recording duration in seconds"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record a camera feed using an encoder."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        service = CameraRecordingService()
        recording = await service.record_camera(
            db=db,
            camera_id=camera_id,
            encoder_id=encoder_id,
            duration=duration
        )
        return recording
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


"""Raspberry Pi streaming API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user, UserInfo
from app.services.pi_service import PiDeviceService
from app.services.streaming_service import StreamingService

router = APIRouter()


@router.get("/devices/{device_id}/content/{content_id}/stream")
async def stream_content(
    device_id: str,
    content_id: int,
    request: Request,
    range_header: Optional[str] = Header(None, alias="Range"),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Stream media content with HTTP range request support."""
    # Verify device exists
    device = PiDeviceService.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Get stream from streaming service
    stream_info = await StreamingService.get_stream(
        db,
        content_id,
        device_id,
        range_header
    )
    
    if not stream_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found or not available for streaming"
        )
    
    # Create streaming response
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Type": stream_info["content_type"],
    }
    
    if stream_info.get("content_range"):
        headers["Content-Range"] = stream_info["content_range"]
        status_code = 206  # Partial Content
    else:
        status_code = 200
    
    if stream_info.get("content_length"):
        headers["Content-Length"] = str(stream_info["content_length"])
    
    return StreamingResponse(
        stream_info["stream"],
        status_code=status_code,
        headers=headers,
        media_type=stream_info["content_type"]
    )


@router.get("/devices/{device_id}/content/{content_id}/stream/info")
async def get_stream_info(
    device_id: str,
    content_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Get stream metadata."""
    # Verify device exists
    device = PiDeviceService.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Get stream info
    info = await StreamingService.get_stream_info(db, content_id, device_id)
    
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    return info



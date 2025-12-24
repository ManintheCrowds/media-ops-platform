"""Application tracking API endpoints."""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models.application import Application
from app.models.job_listing import JobListing
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
    FollowupRequest
)
from app.services.cover_letter import CoverLetterGenerator
from app.services.skill_matcher import SkillMatcher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/applications", tags=["applications"])


@router.post("", response_model=ApplicationResponse, status_code=201)
async def create_application(
    application: ApplicationCreate,
    generate_cover_letter: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Create a new job application."""
    # Verify job listing exists
    job = db.query(JobListing).filter(JobListing.id == application.job_listing_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job listing not found")
    
    # Create application
    db_application = Application(
        job_listing_id=application.job_listing_id,
        status=application.status,
        notes=application.notes,
        cover_letter=application.cover_letter,
    )
    
    # Generate cover letter if requested
    if generate_cover_letter and not application.cover_letter:
        try:
            generator = CoverLetterGenerator()
            matcher = SkillMatcher(db)
            
            # Get skill profile summary
            skill_profile_summary = matcher.get_skill_profile_summary()
            scores = matcher.calculate_match_score(job.description or "")
            
            skill_profile = {
                "matched_skills": scores.get("matched_skills", []),
                "summary": skill_profile_summary
            }
            
            job_data = {
                "title": job.title,
                "company": job.company,
                "description": job.description or ""
            }
            
            cover_letter = await generator.generate_cover_letter(
                job_listing=job_data,
                skill_profile=skill_profile
            )
            
            if cover_letter:
                db_application.cover_letter = cover_letter
            
            await generator.close()
        except Exception as e:
            logger.warning(f"Failed to generate cover letter: {e}")
    
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    
    # Include job listing in response
    response = ApplicationResponse.from_orm(db_application)
    response.job_listing = {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
    }
    
    return response


@router.get("", response_model=List[ApplicationResponse])
async def list_applications(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List applications with optional filtering."""
    query = db.query(Application)
    
    if status:
        query = query.filter(Application.status == status)
    
    # Order by created date (newest first)
    query = query.order_by(desc(Application.created_at))
    
    applications = query.offset(offset).limit(limit).all()
    
    # Include job listing details
    responses = []
    for app in applications:
        response = ApplicationResponse.from_orm(app)
        job = db.query(JobListing).filter(JobListing.id == app.job_listing_id).first()
        if job:
            response.job_listing = {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
            }
        responses.append(response)
    
    return responses


@router.get("/pending-followups", response_model=List[ApplicationResponse])
async def get_pending_followups(
    db: Session = Depends(get_db)
):
    """Get applications with pending follow-ups."""
    now = datetime.utcnow()
    
    applications = db.query(Application).filter(
        Application.next_followup.isnot(None),
        Application.next_followup <= now,
        Application.status.in_(["pending", "submitted", "interview"])
    ).order_by(Application.next_followup).all()
    
    responses = []
    for app in applications:
        response = ApplicationResponse.from_orm(app)
        job = db.query(JobListing).filter(JobListing.id == app.job_listing_id).first()
        if job:
            response.job_listing = {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
            }
        responses.append(response)
    
    return responses


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific application by ID."""
    application = db.query(Application).filter(Application.id == application_id).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    response = ApplicationResponse.from_orm(application)
    
    # Include job listing details
    job = db.query(JobListing).filter(JobListing.id == application.job_listing_id).first()
    if job:
        response.job_listing = {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "url": job.url,
        }
    
    return response


@router.patch("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: int,
    update: ApplicationUpdate,
    db: Session = Depends(get_db)
):
    """Update an application."""
    application = db.query(Application).filter(Application.id == application_id).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Update fields
    if update.status is not None:
        application.status = update.status
        if update.status == "submitted" and not application.applied_at:
            application.applied_at = datetime.utcnow()
    
    if update.notes is not None:
        application.notes = update.notes
    
    if update.cover_letter is not None:
        application.cover_letter = update.cover_letter
    
    if update.next_followup is not None:
        application.next_followup = update.next_followup
    
    db.commit()
    db.refresh(application)
    
    response = ApplicationResponse.from_orm(application)
    
    # Include job listing details
    job = db.query(JobListing).filter(JobListing.id == application.job_listing_id).first()
    if job:
        response.job_listing = {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
        }
    
    return response


@router.post("/{application_id}/followup", response_model=ApplicationResponse)
async def schedule_followup(
    application_id: int,
    followup: FollowupRequest,
    db: Session = Depends(get_db)
):
    """Schedule a follow-up for an application."""
    application = db.query(Application).filter(Application.id == application_id).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Calculate follow-up date
    next_followup = datetime.utcnow() + timedelta(days=followup.days)
    application.next_followup = next_followup
    application.last_followup = datetime.utcnow()
    application.followup_count = (application.followup_count or 0) + 1
    
    if followup.notes:
        current_notes = application.notes or ""
        application.notes = f"{current_notes}\n\nFollow-up scheduled: {followup.notes}".strip()
    
    db.commit()
    db.refresh(application)
    
    response = ApplicationResponse.from_orm(application)
    
    # Include job listing details
    job = db.query(JobListing).filter(JobListing.id == application.job_listing_id).first()
    if job:
        response.job_listing = {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
        }
    
    return response


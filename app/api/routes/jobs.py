# ===== app/api/routes/jobs.py =====
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database.database import get_database
from app.core.database.models import User, JobDescription
from app.services.job_service import JobService
from app.schemas.job import (
    JobDescriptionCreate, 
    JobDescriptionResponse, 
    JobDescriptionUpdate,
    JobDescriptionListResponse
)
from app.api.routes.auth import get_current_user
from app.core.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=JobDescriptionResponse)
async def create_job_description(
    job_data: JobDescriptionCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Create a new job description."""
    
    service = JobService()
    try:
        job = await service.create_job_description(
            db, job_data.dict(), current_user.id
        )
        return _convert_job_to_response(job)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating job description: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{job_id}", response_model=JobDescriptionResponse)
async def get_job_description(
    job_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Get job description by ID."""
    
    service = JobService()
    try:
        job = await service.get_job_description(db, job_id)
        return _convert_job_to_response(job)
    except HTTPException:
        raise


@router.get("/", response_model=JobDescriptionListResponse)
async def list_job_descriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    title: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    remote_allowed: Optional[bool] = Query(None),
    my_jobs: bool = Query(False, description="Show only jobs created by current user"),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """List job descriptions with optional filtering."""
    
    service = JobService()
    
    # Build filters
    filters = {}
    if title:
        filters['title'] = title
    if company:
        filters['company'] = company
    if location:
        filters['location'] = location
    if status:
        filters['status'] = status
    if job_type:
        filters['job_type'] = job_type
    if remote_allowed is not None:
        filters['remote_allowed'] = remote_allowed
    
    try:
        jobs = await service.list_job_descriptions(
            db, skip, limit, filters, 
            current_user.id if my_jobs else None
        )
        
        # Get total count
        query = db.query(JobDescription)
        if my_jobs:
            query = query.filter(JobDescription.created_by == current_user.id)
        total_count = query.count()
        
        return JobDescriptionListResponse(
            jobs=[_convert_job_to_response(job) for job in jobs],
            total=total_count,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing job descriptions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving job descriptions"
        )


@router.put("/{job_id}", response_model=JobDescriptionResponse)
async def update_job_description(
    job_id: int,
    job_update: JobDescriptionUpdate,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Update a job description."""
    
    service = JobService()
    try:
        job = await service.update_job_description(
            db, job_id, job_update.dict(exclude_unset=True), current_user.id
        )
        return _convert_job_to_response(job)
    except HTTPException:
        raise


@router.delete("/{job_id}")
async def delete_job_description(
    job_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Delete a job description."""
    
    service = JobService()
    try:
        success = await service.delete_job_description(db, job_id, current_user.id)
        return {"message": "Job description deleted successfully", "success": success}
    except HTTPException:
        raise


@router.get("/{job_id}/statistics")
async def get_job_statistics(
    job_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Get statistics for a job description."""
    
    service = JobService()
    try:
        stats = await service.get_job_statistics(db, job_id)
        return stats
    except HTTPException:
        raise


@router.get("/{job_id}/skills")
async def get_job_skills(
    job_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Get required and preferred skills for a job."""
    
    service = JobService()
    try:
        job = await service.get_job_description(db, job_id)
        
        skills_analysis = {
            "required_skills": job.required_skills or [],
            "preferred_skills": job.preferred_skills or [],
            "total_required": len(job.required_skills) if job.required_skills else 0,
            "total_preferred": len(job.preferred_skills) if job.preferred_skills else 0,
            "experience_years_required": job.required_experience_years,
            "education_requirements": job.education_requirements or [],
            "remote_allowed": job.remote_allowed,
            "urgency_level": job.urgency_level
        }
        
        return skills_analysis
        
    except HTTPException:
        raise


@router.post("/{job_id}/activate")
async def activate_job(
    job_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Activate a job description."""
    
    service = JobService()
    try:
        job = await service.update_job_description(
            db, job_id, {"status": "active"}, current_user.id
        )
        return {"message": "Job activated successfully", "status": job.status}
    except HTTPException:
        raise


@router.post("/{job_id}/deactivate")
async def deactivate_job(
    job_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Deactivate a job description."""
    
    service = JobService()
    try:
        job = await service.update_job_description(
            db, job_id, {"status": "closed"}, current_user.id
        )
        return {"message": "Job deactivated successfully", "status": job.status}
    except HTTPException:
        raise


@router.get("/{job_id}/candidates")
async def get_job_candidates(
    job_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    min_score: Optional[float] = Query(None, ge=0, le=100),
    suitability: Optional[str] = Query(None),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Get candidates who applied to this job with their scores."""
    
    from app.services.matching_service import MatchingService
    
    matching_service = MatchingService()
    try:
        # Get evaluations for this job
        evaluations = await matching_service.get_job_evaluations(
            db, job_id, limit, min_score
        )
        
        # Filter by suitability if specified
        if suitability:
            evaluations = [e for e in evaluations if e.suitability.lower() == suitability.lower()]
        
        candidates = []
        for evaluation in evaluations[skip:skip+limit]:
            candidate_data = {
                "evaluation_id": evaluation.id,
                "resume_id": evaluation.resume_id,
                "candidate_name": evaluation.resume.candidate_name if evaluation.resume else "Unknown",
                "candidate_email": evaluation.resume.candidate_email if evaluation.resume else None,
                "overall_score": evaluation.overall_score,
                "suitability": evaluation.suitability,
                "matching_skills": evaluation.matching_skills or [],
                "missing_skills": evaluation.missing_skills or [],
                "created_at": evaluation.created_at
            }
            candidates.append(candidate_data)
        
        return {
            "candidates": candidates,
            "total": len(evaluations),
            "showing": len(candidates),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error getting job candidates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving job candidates"
        )


@router.get("/{job_id}/preview")
async def get_job_preview(
    job_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Get job preview with key information."""
    
    service = JobService()
    try:
        job = await service.get_job_description(db, job_id)
        
        preview = {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "job_type": job.job_type,
            "required_skills": (job.required_skills or [])[:8],  # First 8 skills
            "experience_required": job.experience_required,
            "remote_allowed": job.remote_allowed,
            "status": job.status,
            "urgency_level": job.urgency_level,
            "created_at": job.created_at
        }
        
        return preview
        
    except HTTPException:
        raise


def _convert_job_to_response(job: JobDescription) -> JobDescriptionResponse:
    """Convert JobDescription model to JobDescriptionResponse schema."""
    return JobDescriptionResponse(
        id=job.id,
        title=job.title,
        company=job.company,
        department=job.department,
        location=job.location,
        experience_required=job.experience_required,
        salary_range=job.salary_range,
        job_type=job.job_type,
        raw_content=job.raw_content,
        required_skills=job.required_skills or [],
        preferred_skills=job.preferred_skills or [],
        required_experience_years=job.required_experience_years,
        education_requirements=job.education_requirements or [],
        remote_allowed=job.remote_allowed,
        urgency_level=job.urgency_level,
        status=job.status,
        created_by=job.created_by,
        created_at=job.created_at,
        updated_at=job.updated_at
    )
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.core.database.database import get_database
from app.core.database.models import User, Resume
from app.services.resume_service import ResumeService
from app.schemas.resume import ResumeResponse, ResumeListResponse, ResumeUpload
from app.api.routes.auth import get_current_user
from app.core.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/upload", response_model=ResumeResponse)
async def upload_resume(
    file: UploadFile = File(...),
    candidate_name: Optional[str] = None,
    candidate_email: Optional[str] = None,
    candidate_phone: Optional[str] = None,
    source: str = "manual",
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Upload and process a resume file."""
    
    service = ResumeService()
    
    # Prepare metadata
    metadata = {
        "upload_source": source,
        "candidate_name": candidate_name or "Unknown",
        "candidate_email": candidate_email,
        "candidate_phone": candidate_phone
    }
    
    try:
        resume = await service.upload_resume(db, file, metadata)
        return _convert_resume_to_response(resume)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error uploading resume: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Get resume by ID."""
    
    service = ResumeService()
    try:
        resume = await service.get_resume(db, resume_id)
        return _convert_resume_to_response(resume)
    except HTTPException:
        raise


@router.get("/", response_model=ResumeListResponse)
async def list_resumes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    candidate_name: Optional[str] = Query(None),
    skills: Optional[str] = Query(None),
    experience_min: Optional[float] = Query(None, ge=0),
    experience_max: Optional[float] = Query(None, ge=0),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """List resumes with optional filtering."""
    
    service = ResumeService()
    
    # Build filters
    filters = {}
    if candidate_name:
        filters['candidate_name'] = candidate_name
    if skills:
        filters['skills'] = skills
    if experience_min is not None:
        filters['experience_min'] = experience_min
    if experience_max is not None:
        filters['experience_max'] = experience_max
    
    try:
        resumes = await service.list_resumes(db, skip, limit, filters)
        
        # Get total count for pagination
        total_count = db.query(Resume).count()
        
        return ResumeListResponse(
            resumes=[_convert_resume_to_response(resume) for resume in resumes],
            total=total_count,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing resumes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving resumes"
        )


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Delete resume."""
    
    # Check if user has permission (admin or owner)
    if current_user.role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    service = ResumeService()
    try:
        success = await service.delete_resume(db, resume_id)
        return {"message": "Resume deleted successfully", "success": success}
    except HTTPException:
        raise


@router.post("/{resume_id}/reprocess", response_model=ResumeResponse)
async def reprocess_resume(
    resume_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Reprocess an existing resume."""
    
    service = ResumeService()
    try:
        resume = await service.reprocess_resume(db, resume_id)
        return _convert_resume_to_response(resume)
    except HTTPException:
        raise


@router.post("/bulk-upload")
async def bulk_upload_resumes(
    files: List[UploadFile] = File(...),
    source: str = "bulk",
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Upload multiple resume files."""
    
    if len(files) > 50:  # Limit bulk uploads
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 files allowed per bulk upload"
        )
    
    service = ResumeService()
    results = []
    errors = []
    
    for file in files:
        try:
            metadata = {
                "upload_source": source,
                "candidate_name": file.filename.split('.')[0].replace('_', ' ').title()
            }
            
            resume = await service.upload_resume(db, file, metadata)
            results.append({
                "filename": file.filename,
                "resume_id": resume.id,
                "status": "success"
            })
            
        except Exception as e:
            logger.error(f"Error processing {file.filename}: {str(e)}")
            errors.append({
                "filename": file.filename,
                "error": str(e),
                "status": "failed"
            })
    
    return {
        "processed": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }


@router.get("/{resume_id}/skills")
async def get_resume_skills(
    resume_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Get detailed skill analysis for a resume."""
    
    service = ResumeService()
    try:
        resume = await service.get_resume(db, resume_id)
        
        # Extract skill analysis from parsed content
        skill_analysis = {
            "technical_skills": resume.skills or [],
            "total_skills": len(resume.skills) if resume.skills else 0,
            "experience_years": resume.experience_years,
            "skill_categories": resume.skill_categories if hasattr(resume, 'skill_categories') else {},
            "certifications": resume.certifications or []
        }
        
        return skill_analysis
        
    except HTTPException:
        raise


@router.get("/{resume_id}/preview")
async def get_resume_preview(
    resume_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Get resume preview with key information."""
    
    service = ResumeService()
    try:
        resume = await service.get_resume(db, resume_id)
        
        # Extract preview information
        preview = {
            "id": resume.id,
            "candidate_name": resume.candidate_name,
            "candidate_email": resume.candidate_email,
            "skills": (resume.skills or [])[:10],  # First 10 skills
            "experience_years": resume.experience_years,
            "education": resume.education[:2] if resume.education else [],  # First 2 education entries
            "top_projects": resume.projects[:3] if resume.projects else [],  # First 3 projects
            "processing_status": resume.processing_status,
            "created_at": resume.created_at
        }
        
        return preview
        
    except HTTPException:
        raise


def _convert_resume_to_response(resume: Resume) -> ResumeResponse:
    """Convert Resume model to ResumeResponse schema."""
    return ResumeResponse(
        id=resume.id,
        candidate_name=resume.candidate_name,
        candidate_email=resume.candidate_email,
        candidate_phone=resume.candidate_phone,
        candidate_location=resume.candidate_location,
        filename=resume.filename,
        file_type=resume.file_type,
        file_size=resume.file_size,
        skills=resume.skills or [],
        experience_years=resume.experience_years,
        experience_level=resume.experience_level,
        education=resume.education or [],
        work_experience=resume.work_experience or [],
        projects=resume.projects or [],
        certifications=resume.certifications or [],
        processing_status=resume.processing_status,
        created_at=resume.created_at,
        updated_at=resume.updated_at
    )
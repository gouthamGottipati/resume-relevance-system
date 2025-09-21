# ===== app/api/routes/matching.py =====
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database.database import get_database
from app.core.database.models import User
from app.services.matching_service import MatchingService
from app.schemas.matching import (
    EvaluationRequest,
    EvaluationResponse,
    BatchEvaluationRequest,
    EvaluationListResponse
)
from app.api.routes.auth import get_current_user
from app.core.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_resume(
    evaluation_request: EvaluationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Evaluate a resume against a job description."""
    
    service = MatchingService()
    try:
        evaluation = await service.evaluate_resume_against_job(
            db,
            evaluation_request.resume_id,
            evaluation_request.job_id,
            current_user.id,
            evaluation_request.custom_weights
        )
        
        return _convert_evaluation_to_response(evaluation)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in evaluation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during evaluation"
        )


@router.post("/batch-evaluate")
async def batch_evaluate_resumes(
    batch_request: BatchEvaluationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Evaluate multiple resumes against a job description."""
    
    if len(batch_request.resume_ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 resumes allowed per batch evaluation"
        )
    
    service = MatchingService()
    try:
        evaluations = await service.batch_evaluate_resumes(
            db,
            batch_request.resume_ids,
            batch_request.job_id,
            current_user.id
        )
        
        return {
            "job_id": batch_request.job_id,
            "total_processed": len(evaluations),
            "evaluations": [_convert_evaluation_to_response(e) for e in evaluations]
        }
        
    except Exception as e:
        logger.error(f"Error in batch evaluation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in batch evaluation"
        )


@router.get("/evaluations/{evaluation_id}", response_model=EvaluationResponse)
async def get_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Get evaluation by ID."""
    
    service = MatchingService()
    try:
        evaluation = await service.get_evaluation(db, evaluation_id)
        return _convert_evaluation_to_response(evaluation)
    except HTTPException:
        raise


@router.get("/resumes/{resume_id}/evaluations", response_model=EvaluationListResponse)
async def get_resume_evaluations(
    resume_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Get all evaluations for a specific resume."""
    
    service = MatchingService()
    try:
        evaluations = await service.get_resume_evaluations(db, resume_id, limit)
        
        return EvaluationListResponse(
            evaluations=[_convert_evaluation_to_response(e) for e in evaluations],
            total=len(evaluations),
            resume_id=resume_id
        )
        
    except Exception as e:
        logger.error(f"Error getting resume evaluations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving evaluations"
        )


@router.get("/jobs/{job_id}/evaluations")
async def get_job_evaluations(
    job_id: int,
    limit: int = Query(100, ge=1, le=500),
    min_score: Optional[float] = Query(None, ge=0, le=100),
    suitability: Optional[str] = Query(None),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Get all evaluations for a specific job."""
    
    service = MatchingService()
    try:
        evaluations = await service.get_job_evaluations(db, job_id, limit, min_score)
        
        # Filter by suitability if specified
        if suitability:
            evaluations = [e for e in evaluations if e.suitability.lower() == suitability.lower()]
        
        return {
            "job_id": job_id,
            "evaluations": [_convert_evaluation_to_response(e) for e in evaluations],
            "total": len(evaluations),
            "filters": {
                "min_score": min_score,
                "suitability": suitability
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting job evaluations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving job evaluations"
        )


@router.get("/leaderboard/{job_id}")
async def get_job_leaderboard(
    job_id: int,
    limit: int = Query(20, ge=5, le=100),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """Get top candidates for a job (leaderboard)."""
    
    service = MatchingService()
    try:
        evaluations = await service.get_job_evaluations(db, job_id, limit)
        
        leaderboard = []
        for rank, evaluation in enumerate(evaluations, 1):
            candidate_data = {
                "rank": rank,
                "evaluation_id": evaluation.id,
                "resume_id": evaluation.resume_id,
                "candidate_name": evaluation.resume.candidate_name if evaluation.resume else "Unknown",
                "overall_score": evaluation.overall_score,
                "suitability": evaluation.suitability,
                "key_strengths": evaluation.strengths[:3] if evaluation.strengths else [],
                "created_at": evaluation.created_at
            }
            leaderboard.append(candidate_data)
        
        return {
            "job_id": job_id,
            "leaderboard": leaderboard,
            "total_candidates": len(leaderboard)
        }
        
    except Exception as e:
        logger.error(f"Error generating leaderboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating leaderboard"
        )


def _convert_evaluation_to_response(evaluation) -> EvaluationResponse:
    """Convert evaluation model to response schema."""
    return EvaluationResponse(
        id=evaluation.id,
        resume_id=evaluation.resume_id,
        job_description_id=evaluation.job_description_id,
        overall_score=evaluation.overall_score,
        hard_skills_score=evaluation.hard_skills_score,
        soft_skills_score=evaluation.soft_skills_score,
        experience_score=evaluation.experience_score,
        education_score=evaluation.education_score,
        matching_skills=evaluation.matching_skills or [],
        missing_skills=evaluation.missing_skills or [],
        additional_skills=evaluation.additional_skills or [],
        suitability=evaluation.suitability,
        recommendation=evaluation.recommendation,
        strengths=evaluation.strengths or [],
        weaknesses=evaluation.weaknesses or [],
        suggestions=evaluation.suggestions or [],
        personalized_feedback=evaluation.personalized_feedback,
        percentile_rank=evaluation.percentile_rank,
        processing_time=evaluation.processing_time,
        confidence_score=evaluation.confidence_score,
        created_at=evaluation.created_at
    )
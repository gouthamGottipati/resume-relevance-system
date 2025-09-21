from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.database.models import JobDescription
from app.core.ai_pipeline.jd_parser import JobDescriptionParser
from app.core.utils.validators import JobDescriptionValidator
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class JobService:
    """Service for job description management."""
    
    def __init__(self):
        self.jd_parser = JobDescriptionParser()
    
    async def create_job_description(
        self,
        db: Session,
        job_data: Dict[str, Any],
        created_by: int
    ) -> JobDescription:
        """Create and parse a new job description."""
        
        logger.info(f"Creating job description: {job_data.get('title', 'Unknown')}")
        
        # Validate job data
        try:
            validator = JobDescriptionValidator(**job_data)
            validated_data = validator.dict()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation error: {str(e)}"
            )
        
        try:
            # Parse job description
            parsed_jd = self.jd_parser.parse(validated_data['raw_content'], validated_data)
            
            # Create database record
            job = JobDescription(
                title=validated_data['title'],
                company=validated_data['company'],
                department=validated_data.get('department'),
                location=validated_data.get('location'),
                experience_required=validated_data.get('experience_required'),
                job_type=validated_data.get('job_type', 'full-time'),
                raw_content=validated_data['raw_content'],
                parsed_content=self._serialize_parsed_jd(parsed_jd),
                required_skills=parsed_jd.required_skills,
                preferred_skills=parsed_jd.preferred_skills,
                required_experience_years=parsed_jd.required_experience_years,
                education_requirements=parsed_jd.education_requirements,
                remote_allowed=parsed_jd.remote_allowed,
                urgency_level=parsed_jd.urgency_level,
                created_by=created_by,
                status="active"
            )
            
            db.add(job)
            db.commit()
            db.refresh(job)
            
            logger.info(f"Job description created successfully: ID {job.id}")
            return job
            
        except Exception as e:
            logger.error(f"Error creating job description: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating job description: {str(e)}"
            )
    
    async def get_job_description(self, db: Session, job_id: int) -> JobDescription:
        """Get job description by ID."""
        job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job description not found"
            )
        return job
    
    async def list_job_descriptions(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        created_by: Optional[int] = None
    ) -> List[JobDescription]:
        """List job descriptions with optional filtering."""
        
        query = db.query(JobDescription)
        
        if created_by:
            query = query.filter(JobDescription.created_by == created_by)
        
        if filters:
            if 'title' in filters:
                query = query.filter(JobDescription.title.contains(filters['title']))
            
            if 'company' in filters:
                query = query.filter(JobDescription.company.contains(filters['company']))
            
            if 'location' in filters:
                query = query.filter(JobDescription.location.contains(filters['location']))
            
            if 'status' in filters:
                query = query.filter(JobDescription.status == filters['status'])
            
            if 'job_type' in filters:
                query = query.filter(JobDescription.job_type == filters['job_type'])
            
            if 'remote_allowed' in filters:
                query = query.filter(JobDescription.remote_allowed == filters['remote_allowed'])
        
        return query.order_by(JobDescription.created_at.desc()).offset(skip).limit(limit).all()
    
    async def update_job_description(
        self,
        db: Session,
        job_id: int,
        job_data: Dict[str, Any],
        user_id: int
    ) -> JobDescription:
        """Update an existing job description."""
        
        job = await self.get_job_description(db, job_id)
        
        # Check permissions (simplified - in real app would check role/ownership)
        if job.created_by != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this job description"
            )
        
        try:
            # Update fields
            for key, value in job_data.items():
                if hasattr(job, key) and key != 'id':
                    setattr(job, key, value)
            
            # Re-parse if content changed
            if 'raw_content' in job_data:
                parsed_jd = self.jd_parser.parse(job.raw_content, job_data)
                job.parsed_content = self._serialize_parsed_jd(parsed_jd)
                job.required_skills = parsed_jd.required_skills
                job.preferred_skills = parsed_jd.preferred_skills
                job.required_experience_years = parsed_jd.required_experience_years
            
            db.commit()
            db.refresh(job)
            
            logger.info(f"Job description updated: ID {job_id}")
            return job
            
        except Exception as e:
            logger.error(f"Error updating job description {job_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating job description: {str(e)}"
            )
    
    async def delete_job_description(
        self,
        db: Session,
        job_id: int,
        user_id: int
    ) -> bool:
        """Delete a job description."""
        
        job = await self.get_job_description(db, job_id)
        
        # Check permissions
        if job.created_by != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this job description"
            )
        
        db.delete(job)
        db.commit()
        
        logger.info(f"Job description deleted: ID {job_id}")
        return True
    
    async def get_job_statistics(self, db: Session, job_id: int) -> Dict[str, Any]:
        """Get statistics for a job description."""
        
        job = await self.get_job_description(db, job_id)
        
        # Get evaluation statistics
        from app.core.database.models import ResumeEvaluation
        
        evaluations = db.query(ResumeEvaluation).filter(
            ResumeEvaluation.job_description_id == job_id
        ).all()
        
        if not evaluations:
            return {
                'total_applications': 0,
                'avg_score': 0,
                'high_suitability_count': 0,
                'medium_suitability_count': 0,
                'low_suitability_count': 0
            }
        
        scores = [e.overall_score for e in evaluations]
        suitability_counts = {}
        for suitability in ['High', 'Medium', 'Low']:
            suitability_counts[suitability.lower() + '_suitability_count'] = len(
                [e for e in evaluations if e.suitability == suitability]
            )
        
        return {
            'total_applications': len(evaluations),
            'avg_score': sum(scores) / len(scores),
            'max_score': max(scores),
            'min_score': min(scores),
            **suitability_counts
        }
    
    def _serialize_parsed_jd(self, parsed_jd) -> Dict[str, Any]:
        """Serialize parsed job description for database storage."""
        return {
            'summary': parsed_jd.summary,
            'responsibilities': parsed_jd.responsibilities,
            'requirements': parsed_jd.requirements,
            'preferred_qualifications': parsed_jd.preferred_qualifications,
            'benefits': parsed_jd.benefits
        }
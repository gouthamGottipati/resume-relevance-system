from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.ai_pipeline.resume_parser import ParsedResume, ContactInfo
import asyncio

from typing import Any
from fastapi import HTTPException, status
from app.core.database.models import Resume, JobDescription, ResumeEvaluation
from app.core.ai_pipeline.resume_parser import ResumeParser
from app.core.ai_pipeline.jd_parser import JobDescriptionParser
from app.core.ai_pipeline.skill_extractor import AdvancedSkillExtractor
from app.core.ai_pipeline.semantic_matcher import SemanticMatcher
from app.core.ai_pipeline.scoring_engine import AdvancedScoringEngine, ScoringWeights
from app.core.ai_pipeline.feedback_generator import AIFeedbackGenerator
from app.services.resume_service import ResumeService
from app.services.job_service import JobService
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class MatchingService:
    """Service for resume-job matching and evaluation."""
    
    def __init__(self):
        self.skill_extractor = AdvancedSkillExtractor()
        self.semantic_matcher = SemanticMatcher()
        self.scoring_engine = AdvancedScoringEngine()
        self.feedback_generator = AIFeedbackGenerator()
        self.resume_service = ResumeService()
        self.job_service = JobService()
    
    async def evaluate_resume_against_job(
        self,
        db: Session,
        resume_id: int,
        job_id: int,
        user_id: Optional[int] = None,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> ResumeEvaluation:
        """Evaluate a resume against a job description."""
        
        logger.info(f"Evaluating resume {resume_id} against job {job_id}")
        
        # Get resume and job
        resume = await self.resume_service.get_resume(db, resume_id)
        job = await self.job_service.get_job_description(db, job_id)
        
        # Parse resume if not already parsed
        if not resume.parsed_content or resume.processing_status != "processed":
            resume = await self.resume_service.reprocess_resume(db, resume_id)
        
        try:
            # Run matching pipeline
            evaluation_result = await self._run_matching_pipeline(
                resume, job, custom_weights
            )
            
            # Create evaluation record
            evaluation = ResumeEvaluation(
                resume_id=resume_id,
                job_description_id=job_id,
                evaluated_by=user_id,
                overall_score=evaluation_result['final_score'].overall_score,
                hard_skills_score=evaluation_result['final_score'].detailed_scores.hard_skills_score,
                soft_skills_score=evaluation_result['final_score'].detailed_scores.soft_skills_score,
                experience_score=evaluation_result['final_score'].detailed_scores.experience_score,
                education_score=evaluation_result['final_score'].detailed_scores.education_score,
                matching_skills=evaluation_result['matching_skills'],
                missing_skills=evaluation_result['missing_skills'],
                additional_skills=evaluation_result['additional_skills'],
                suitability=evaluation_result['final_score'].suitability,
                recommendation=evaluation_result['recommendation'],
                strengths=[s for s in evaluation_result['feedback'].strengths],
                weaknesses=[s for s in evaluation_result['feedback'].areas_for_improvement],
                suggestions=[s for s in evaluation_result['feedback'].specific_recommendations],
                personalized_feedback=evaluation_result['feedback'].overall_assessment,
                processing_time=evaluation_result['processing_time'],
                model_version="1.0.0",
                confidence_score=evaluation_result['final_score'].detailed_scores.overall_confidence
            )
            
            db.add(evaluation)
            db.commit()
            db.refresh(evaluation)
            
            logger.info(f"Evaluation completed: ID {evaluation.id}, Score: {evaluation.overall_score}")
            return evaluation
            
        except Exception as e:
            logger.error(f"Error in matching pipeline: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error evaluating resume: {str(e)}"
            )
    
    async def _run_matching_pipeline(
        self,
        resume: Resume,
        job: JobDescription,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Run the complete matching pipeline."""
        
        start_time = datetime.now()
        
        # Parse resume data
        parsed_resume = self._deserialize_resume(resume)
        
        # Extract skills from resume
        skill_profile = self.skill_extractor.extract_skills(resume.raw_text, "resume")
        
        # Parse job description
        jd_parser = JobDescriptionParser()
        jd_metadata = {
            'title': job.title,
            'company': job.company,
            'location': job.location,
            'department': job.department,
            'experience_required': job.experience_required
        }
        parsed_jd = jd_parser.parse(job.raw_content, jd_metadata)
        
        # Perform semantic matching
        semantic_match = self.semantic_matcher.match_resume_to_jd(
            skill_profile, parsed_jd, resume.raw_text, job.raw_content
        )
        
        # Configure scoring weights
        if custom_weights:
            weights = ScoringWeights(**custom_weights)
        else:
            weights = ScoringWeights()
        
        scoring_engine = AdvancedScoringEngine(weights)
        
        # Calculate scores
        final_score = scoring_engine.calculate_comprehensive_score(
            parsed_resume, skill_profile, semantic_match, parsed_jd
        )
        
        # Generate feedback
        feedback = self.feedback_generator.generate_comprehensive_feedback(
            parsed_resume, final_score, semantic_match, parsed_jd
        )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'final_score': final_score,
            'semantic_match': semantic_match,
            'feedback': feedback,
            'matching_skills': [match.skill_name for match in semantic_match.skill_matches],
            'missing_skills': semantic_match.missing_skills,
            'additional_skills': semantic_match.additional_skills,
            'recommendation': final_score.get_verdict_details()['description'],
            'processing_time': processing_time
        }
    
    async def batch_evaluate_resumes(
        self,
        db: Session,
        resume_ids: List[int],
        job_id: int,
        user_id: Optional[int] = None
    ) -> List[ResumeEvaluation]:
        """Evaluate multiple resumes against a single job."""
        
        logger.info(f"Batch evaluating {len(resume_ids)} resumes against job {job_id}")
        
        evaluations = []
        for resume_id in resume_ids:
            try:
                evaluation = await self.evaluate_resume_against_job(
                    db, resume_id, job_id, user_id
                )
                evaluations.append(evaluation)
            except Exception as e:
                logger.error(f"Error evaluating resume {resume_id}: {str(e)}")
                # Continue with other resumes
                continue
        
        return evaluations
    
    async def get_evaluation(self, db: Session, evaluation_id: int) -> ResumeEvaluation:
        """Get evaluation by ID."""
        evaluation = db.query(ResumeEvaluation).filter(
            ResumeEvaluation.id == evaluation_id
        ).first()
        
        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation not found"
            )
        
        return evaluation
    
    async def get_resume_evaluations(
        self,
        db: Session,
        resume_id: int,
        limit: int = 10
    ) -> List[ResumeEvaluation]:
        """Get all evaluations for a specific resume."""
        return db.query(ResumeEvaluation).filter(
            ResumeEvaluation.resume_id == resume_id
        ).order_by(ResumeEvaluation.created_at.desc()).limit(limit).all()
    
    async def get_job_evaluations(
        self,
        db: Session,
        job_id: int,
        limit: int = 100,
        min_score: Optional[float] = None
    ) -> List[ResumeEvaluation]:
        """Get all evaluations for a specific job."""
        query = db.query(ResumeEvaluation).filter(
            ResumeEvaluation.job_description_id == job_id
        )
        
        if min_score:
            query = query.filter(ResumeEvaluation.overall_score >= min_score)
        
        return query.order_by(
            ResumeEvaluation.overall_score.desc()
        ).limit(limit).all()
    
    def _deserialize_resume(self, resume: Resume) -> 'ParsedResume':
        """Deserialize resume data from database."""
        # This would reconstruct the ParsedResume object
        # For now, we'll create a minimal version
        from app.core.ai_pipeline.resume_parser import ParsedResume, ContactInfo
        
        contact_info = ContactInfo()
        if resume.parsed_content and 'contact_info' in resume.parsed_content:
            contact_data = resume.parsed_content['contact_info']
            contact_info.name = contact_data.get('name', resume.candidate_name)
            contact_info.email = contact_data.get('email', resume.candidate_email)
            contact_info.phone = contact_data.get('phone', resume.candidate_phone)
            contact_info.location = contact_data.get('location', resume.candidate_location)
        
        return ParsedResume(
            contact_info=contact_info,
            skills=resume.skills or [],
            education=resume.education or [],
            work_experience=resume.work_experience or [],
            projects=resume.projects or [],
            certifications=resume.certifications or [],
            total_experience_years=resume.experience_years,
            raw_text=resume.raw_text,
            parsing_confidence=resume.parsed_content.get('parsing_confidence', 0.8) if resume.parsed_content else 0.8
        )
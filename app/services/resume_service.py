from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.core.database.models import Resume, ResumeEvaluation
from app.core.ai_pipeline.resume_parser import ResumeParser, ParsedResume
from app.core.ai_pipeline.skill_extractor import AdvancedSkillExtractor
from app.core.utils.file_handler import FileHandler
from app.core.utils.validators import ResumeUploadValidator
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class ResumeService:
    """Service for resume management and processing."""
    
    def __init__(self):
        self.resume_parser = ResumeParser()
        self.skill_extractor = AdvancedSkillExtractor()
        self.file_handler = FileHandler()
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def upload_resume(
        self,
        db: Session,
        file: UploadFile,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Resume:
        """Upload and process a resume file."""
        
        logger.info(f"Processing resume upload: {file.filename}")
        
        # Validate file
        is_valid, error_msg = self.file_handler.validate_file(file.filename, file.size)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        try:
            # Read file content
            file_content = await file.read()
            
            # Save file to disk
            file_path, file_hash = self.file_handler.save_file(
                file_content, file.filename, "resume"
            )
            
            # Parse resume in background
            loop = asyncio.get_event_loop()
            parsed_resume = await loop.run_in_executor(
                self.executor, self._parse_resume_file, file_path, file.filename
            )
            
            # Create database record
            resume = Resume(
                candidate_name=parsed_resume.contact_info.name or "Unknown",
                candidate_email=parsed_resume.contact_info.email,
                candidate_phone=parsed_resume.contact_info.phone,
                candidate_location=parsed_resume.contact_info.location,
                filename=file.filename,
                file_path=file_path,
                file_type=file.filename.split('.')[-1].lower(),
                file_size=file.size,
                file_hash=file_hash,
                raw_text=parsed_resume.raw_text,
                parsed_content=self._serialize_parsed_resume(parsed_resume),
                skills=[skill.name for skill in parsed_resume.skills] if parsed_resume.skills else None,
                experience_years=parsed_resume.total_experience_years,
                education=self._serialize_education(parsed_resume.education) if parsed_resume.education else None,
                work_experience=self._serialize_work_experience(parsed_resume.work_experience) if parsed_resume.work_experience else None,
                projects=self._serialize_projects(parsed_resume.projects) if parsed_resume.projects else None,
                certifications=parsed_resume.certifications,
                processing_status="processed"
            )
            
            # Add metadata if provided
            if metadata:
                for key, value in metadata.items():
                    if hasattr(resume, key):
                        setattr(resume, key, value)
            
            db.add(resume)
            db.commit()
            db.refresh(resume)
            
            logger.info(f"Resume processed successfully: ID {resume.id}")
            return resume
            
        except Exception as e:
            logger.error(f"Error processing resume: {str(e)}")
            # Cleanup file if database operation fails
            if 'file_path' in locals():
                self.file_handler.delete_file(file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing resume: {str(e)}"
            )
    
    def _parse_resume_file(self, file_path: str, filename: str) -> ParsedResume:
        """Parse resume file (runs in executor)."""
        file_extension = filename.split('.')[-1].lower()
        
        if file_extension == 'pdf':
            return self.resume_parser.parse_pdf(file_path)
        elif file_extension in ['docx', 'doc']:
            return self.resume_parser.parse_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    async def get_resume(self, db: Session, resume_id: int) -> Resume:
        """Get resume by ID."""
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        return resume
    
    async def list_resumes(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Resume]:
        """List resumes with optional filtering."""
        
        query = db.query(Resume)
        
        if filters:
            if 'candidate_name' in filters:
                query = query.filter(Resume.candidate_name.contains(filters['candidate_name']))
            
            if 'skills' in filters:
                query = query.filter(Resume.skills.contains(filters['skills']))
            
            if 'experience_min' in filters:
                query = query.filter(Resume.experience_years >= filters['experience_min'])
            
            if 'experience_max' in filters:
                query = query.filter(Resume.experience_years <= filters['experience_max'])
        
        return query.offset(skip).limit(limit).all()
    
    async def delete_resume(self, db: Session, resume_id: int) -> bool:
        """Delete resume and associated files."""
        resume = await self.get_resume(db, resume_id)
        
        # Delete file from disk
        file_deleted = self.file_handler.delete_file(resume.file_path)
        
        # Delete from database
        db.delete(resume)
        db.commit()
        
        logger.info(f"Resume deleted: ID {resume_id}")
        return file_deleted
    
    async def reprocess_resume(self, db: Session, resume_id: int) -> Resume:
        """Reprocess an existing resume."""
        resume = await self.get_resume(db, resume_id)
        
        try:
            # Parse again
            loop = asyncio.get_event_loop()
            parsed_resume = await loop.run_in_executor(
                self.executor, self._parse_resume_file, resume.file_path, resume.filename
            )
            
            # Update database record
            resume.raw_text = parsed_resume.raw_text
            resume.parsed_content = self._serialize_parsed_resume(parsed_resume)
            resume.skills = [skill.name for skill in parsed_resume.skills] if parsed_resume.skills else None
            resume.experience_years = parsed_resume.total_experience_years
            resume.processing_status = "processed"
            
            db.commit()
            db.refresh(resume)
            
            logger.info(f"Resume reprocessed: ID {resume_id}")
            return resume
            
        except Exception as e:
            resume.processing_status = "failed"
            resume.processing_errors = {"error": str(e)}
            db.commit()
            
            logger.error(f"Error reprocessing resume {resume_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error reprocessing resume: {str(e)}"
            )
    
    # Helper methods for serialization
    def _serialize_parsed_resume(self, parsed_resume: ParsedResume) -> Dict[str, Any]:
        """Serialize parsed resume for database storage."""
        return {
            "contact_info": {
                "name": parsed_resume.contact_info.name,
                "email": parsed_resume.contact_info.email,
                "phone": parsed_resume.contact_info.phone,
                "linkedin": parsed_resume.contact_info.linkedin,
                "github": parsed_resume.contact_info.github,
                "location": parsed_resume.contact_info.location
            },
            "summary": parsed_resume.summary,
            "parsing_confidence": parsed_resume.parsing_confidence
        }
    
    def _serialize_education(self, education_list) -> List[Dict[str, Any]]:
        """Serialize education for database storage."""
        return [
            {
                "degree": edu.degree,
                "institution": edu.institution,
                "location": edu.location,
                "graduation_year": edu.graduation_year,
                "gpa": edu.gpa
            }
            for edu in education_list
        ]
    
    def _serialize_work_experience(self, work_experience_list) -> List[Dict[str, Any]]:
        """Serialize work experience for database storage."""
        return [
            {
                "title": exp.title,
                "company": exp.company,
                "location": exp.location,
                "start_date": exp.start_date,
                "end_date": exp.end_date,
                "description": exp.description
            }
            for exp in work_experience_list
        ]
    
    def _serialize_projects(self, projects_list) -> List[Dict[str, Any]]:
        """Serialize projects for database storage."""
        return [
            {
                "title": proj.title,
                "description": proj.description,
                "technologies": proj.technologies,
                "url": proj.url
            }
            for proj in projects_list
        ]
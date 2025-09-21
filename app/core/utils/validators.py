import re
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, validator, EmailStr
from datetime import datetime


class ResumeUploadValidator(BaseModel):
    """Validator for resume upload."""
    candidate_name: str
    candidate_email: Optional[EmailStr] = None
    candidate_phone: Optional[str] = None
    filename: str
    file_size: int
    
    @validator('candidate_name')
    def validate_candidate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Candidate name must be at least 2 characters long')
        return v.strip().title()
    
    @validator('candidate_phone')
    def validate_phone(cls, v):
        if v is None:
            return v
        # Remove all non-digit characters
        phone = re.sub(r'\D', '', v)
        if len(phone) < 10:
            raise ValueError('Phone number must be at least 10 digits')
        return phone


class JobDescriptionValidator(BaseModel):
    """Validator for job description."""
    title: str
    company: str
    location: Optional[str] = None
    department: Optional[str] = None
    experience_required: Optional[str] = None
    job_type: Optional[str] = "full-time"
    remote_allowed: bool = False
    raw_content: str
    
    @validator('title')
    def validate_title(cls, v):
        if len(v.strip()) < 5:
            raise ValueError('Job title must be at least 5 characters long')
        return v.strip().title()
    
    @validator('company')
    def validate_company(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Company name must be at least 2 characters long')
        return v.strip().title()
    
    @validator('raw_content')
    def validate_content(cls, v):
        if len(v.strip()) < 50:
            raise ValueError('Job description must be at least 50 characters long')
        return v.strip()
    
    @validator('job_type')
    def validate_job_type(cls, v):
        allowed_types = ['full-time', 'part-time', 'contract', 'internship', 'freelance']
        if v and v.lower() not in allowed_types:
            raise ValueError(f'Job type must be one of: {", ".join(allowed_types)}')
        return v.lower() if v else 'full-time'


class ScoringValidator(BaseModel):
    """Validator for scoring parameters."""
    hard_match_weight: float = 0.4
    soft_match_weight: float = 0.6
    experience_weight: float = 0.3
    skills_weight: float = 0.4
    education_weight: float = 0.3
    
    @validator('hard_match_weight', 'soft_match_weight', 'experience_weight', 'skills_weight', 'education_weight')
    def validate_weights(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Weight values must be between 0 and 1')
        return v
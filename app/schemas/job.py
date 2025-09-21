from pydantic import BaseModel, validator
from datetime import datetime
from typing import List, Optional, Dict, Any


class JobDescriptionCreate(BaseModel):
    """Schema for creating job descriptions."""
    title: str
    company: str
    department: Optional[str] = None
    location: Optional[str] = None
    experience_required: Optional[str] = None
    salary_range: Optional[str] = None
    job_type: Optional[str] = "full-time"
    raw_content: str
    remote_allowed: bool = False
    urgency_level: str = "medium"
    
    @validator('title')
    def validate_title(cls, v):
        if len(v.strip()) < 5:
            raise ValueError('Job title must be at least 5 characters long')
        return v.strip()
    
    @validator('company')
    def validate_company(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Company name must be at least 2 characters long')
        return v.strip()
    
    @validator('raw_content')
    def validate_content(cls, v):
        if len(v.strip()) < 50:
            raise ValueError('Job description must be at least 50 characters long')
        return v.strip()
    
    @validator('job_type')
    def validate_job_type(cls, v):
        allowed_types = ['full-time', 'part-time', 'contract', 'internship', 'freelance']
        if v.lower() not in allowed_types:
            raise ValueError(f'Job type must be one of: {", ".join(allowed_types)}')
        return v.lower()
    
    @validator('urgency_level')
    def validate_urgency(cls, v):
        allowed_levels = ['low', 'medium', 'high']
        if v.lower() not in allowed_levels:
            raise ValueError(f'Urgency level must be one of: {", ".join(allowed_levels)}')
        return v.lower()


class JobDescriptionUpdate(BaseModel):
    """Schema for updating job descriptions."""
    title: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    experience_required: Optional[str] = None
    salary_range: Optional[str] = None
    job_type: Optional[str] = None
    raw_content: Optional[str] = None
    remote_allowed: Optional[bool] = None
    urgency_level: Optional[str] = None
    status: Optional[str] = None


class JobDescriptionResponse(BaseModel):
    """Schema for job description response."""
    id: int
    title: str
    company: str
    department: Optional[str]
    location: Optional[str]
    experience_required: Optional[str]
    salary_range: Optional[str]
    job_type: Optional[str]
    raw_content: str
    required_skills: List[str]
    preferred_skills: List[str]
    required_experience_years: Optional[int]
    education_requirements: List[str]
    remote_allowed: bool
    urgency_level: str
    status: str
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class JobDescriptionListResponse(BaseModel):
    """Schema for job description list response."""
    jobs: List[JobDescriptionResponse]
    total: int
    skip: int
    limit: int
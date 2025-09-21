from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from typing import List, Optional, Dict, Any


class ResumeUpload(BaseModel):
    """Schema for resume upload metadata."""
    candidate_name: Optional[str] = None
    candidate_email: Optional[EmailStr] = None
    candidate_phone: Optional[str] = None
    source: str = "manual"


class ContactInfo(BaseModel):
    """Contact information schema."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    location: Optional[str] = None


class Education(BaseModel):
    """Education schema."""
    degree: Optional[str] = None
    institution: Optional[str] = None
    location: Optional[str] = None
    graduation_year: Optional[int] = None
    gpa: Optional[float] = None


class WorkExperience(BaseModel):
    """Work experience schema."""
    title: str
    company: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[List[str]] = None


class Project(BaseModel):
    """Project schema."""
    title: str
    description: str
    technologies: Optional[List[str]] = None
    url: Optional[str] = None


class ResumeResponse(BaseModel):
    """Schema for resume response."""
    id: int
    candidate_name: str
    candidate_email: Optional[str]
    candidate_phone: Optional[str]
    candidate_location: Optional[str]
    filename: str
    file_type: str
    file_size: int
    skills: List[str]
    experience_years: Optional[float]
    experience_level: Optional[str]
    education: List[Dict[str, Any]]
    work_experience: List[Dict[str, Any]]
    projects: List[Dict[str, Any]]
    certifications: List[str]
    processing_status: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ResumeListResponse(BaseModel):
    """Schema for resume list response."""
    resumes: List[ResumeResponse]
    total: int
    skip: int
    limit: int
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any, List
import uuid

Base = declarative_base()


class User(Base):
    """User model for authentication and role management."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(20), default="recruiter")  # recruiter, admin, student
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    job_descriptions = relationship("JobDescription", back_populates="created_by_user")
    resume_evaluations = relationship("ResumeEvaluation", back_populates="evaluated_by_user")


class JobDescription(Base):
    """Job description model with parsed content."""
    __tablename__ = "job_descriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    department = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    experience_required = Column(String(50), nullable=True)
    salary_range = Column(String(100), nullable=True)
    
    # Content
    raw_content = Column(Text, nullable=False)
    parsed_content = Column(JSON, nullable=True)  # Structured parsed data
    
    # Extracted Information
    required_skills = Column(JSON, nullable=True)  # List of required skills
    preferred_skills = Column(JSON, nullable=True)  # List of preferred skills
    required_experience_years = Column(Integer, nullable=True)
    education_requirements = Column(JSON, nullable=True)
    
    # Metadata
    job_type = Column(String(50), nullable=True)  # full-time, part-time, contract
    remote_allowed = Column(Boolean, default=False)
    urgency_level = Column(String(20), default="medium")  # low, medium, high
    
    # Tracking
    status = Column(String(20), default="active")  # active, closed, draft
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    created_by_user = relationship("User", back_populates="job_descriptions")
    resume_evaluations = relationship("ResumeEvaluation", back_populates="job_description")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'required_skills': self.required_skills or [],
            'experience_required': self.experience_required,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Resume(Base):
    """Resume model with parsed content and metadata."""
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Info
    candidate_name = Column(String(255), nullable=False)
    candidate_email = Column(String(255), nullable=True)
    candidate_phone = Column(String(50), nullable=True)
    candidate_location = Column(String(255), nullable=True)
    
    # File Info
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, docx, doc
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False, unique=True)  # SHA256 hash
    
    # Parsed Content
    raw_text = Column(Text, nullable=False)
    parsed_content = Column(JSON, nullable=True)  # Structured parsed data
    
    # Extracted Information
    skills = Column(JSON, nullable=True)  # List of skills
    experience_years = Column(Float, nullable=True)
    education = Column(JSON, nullable=True)  # Education details
    work_experience = Column(JSON, nullable=True)  # Work experience
    projects = Column(JSON, nullable=True)  # Projects
    certifications = Column(JSON, nullable=True)  # Certifications
    
    # Analysis Results
    skill_categories = Column(JSON, nullable=True)  # Categorized skills
    experience_level = Column(String(20), nullable=True)  # entry, mid, senior
    
    # Metadata
    upload_source = Column(String(50), default="manual")  # manual, bulk, api
    processing_status = Column(String(20), default="pending")  # pending, processed, failed
    processing_errors = Column(JSON, nullable=True)
    
    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_processed = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    evaluations = relationship("ResumeEvaluation", back_populates="resume")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'candidate_name': self.candidate_name,
            'candidate_email': self.candidate_email,
            'skills': self.skills or [],
            'experience_years': self.experience_years,
            'experience_level': self.experience_level,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ResumeEvaluation(Base):
    """Resume evaluation results against job descriptions."""
    __tablename__ = "resume_evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False)
    evaluated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Scores (0-100)
    overall_score = Column(Float, nullable=False)
    hard_skills_score = Column(Float, nullable=False)
    soft_skills_score = Column(Float, nullable=False)
    experience_score = Column(Float, nullable=False)
    education_score = Column(Float, nullable=False)
    
    # Detailed Analysis
    matching_skills = Column(JSON, nullable=True)  # Skills that match
    missing_skills = Column(JSON, nullable=True)  # Skills that are missing
    additional_skills = Column(JSON, nullable=True)  # Extra skills candidate has
    
    # Verdict
    suitability = Column(String(10), nullable=False)  # High, Medium, Low
    recommendation = Column(Text, nullable=True)
    
    # AI-Generated Feedback
    strengths = Column(JSON, nullable=True)  # List of strengths
    weaknesses = Column(JSON, nullable=True)  # List of areas for improvement
    suggestions = Column(JSON, nullable=True)  # Improvement suggestions
    personalized_feedback = Column(Text, nullable=True)  # Detailed feedback
    
    # Benchmarking
    percentile_rank = Column(Float, nullable=True)  # 0-100
    peer_comparison = Column(JSON, nullable=True)  # Comparison with similar profiles
    
    # Processing Metadata
    processing_time = Column(Float, nullable=True)  # Processing time in seconds
    model_version = Column(String(50), nullable=True)
    confidence_score = Column(Float, nullable=True)  # Model confidence
    
    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    resume = relationship("Resume", back_populates="evaluations")
    job_description = relationship("JobDescription", back_populates="resume_evaluations")
    evaluated_by_user = relationship("User", back_populates="resume_evaluations")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'overall_score': self.overall_score,
            'suitability': self.suitability,
            'matching_skills': self.matching_skills or [],
            'missing_skills': self.missing_skills or [],
            'percentile_rank': self.percentile_rank,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SkillBenchmark(Base):
    """Skill benchmarking data for peer comparison."""
    __tablename__ = "skill_benchmarks"
    
    id = Column(Integer, primary_key=True, index=True)
    
    skill_name = Column(String(255), nullable=False, index=True)
    skill_category = Column(String(100), nullable=False)
    industry = Column(String(100), nullable=True)
    experience_level = Column(String(20), nullable=False)  # entry, mid, senior
    
    # Statistical Data
    avg_score = Column(Float, nullable=False)
    median_score = Column(Float, nullable=False)
    percentile_25 = Column(Float, nullable=False)
    percentile_75 = Column(Float, nullable=False)
    percentile_90 = Column(Float, nullable=False)
    
    # Sample Data
    sample_size = Column(Integer, nullable=False)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Analytics(Base):
    """Analytics and insights data."""
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Dimensions
    metric_name = Column(String(255), nullable=False, index=True)
    dimension_type = Column(String(50), nullable=False)  # skill, location, experience, etc.
    dimension_value = Column(String(255), nullable=False)
    time_period = Column(String(50), nullable=False)  # daily, weekly, monthly
    
    # Metrics
    metric_value = Column(Float, nullable=False)
    metric_count = Column(Integer, nullable=True)
    additional_data = Column(JSON, nullable=True)
    
    # Tracking
    date_recorded = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
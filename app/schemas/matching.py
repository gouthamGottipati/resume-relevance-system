from pydantic import BaseModel, validator
from datetime import datetime
from typing import List, Optional, Dict, Any


class EvaluationRequest(BaseModel):
    """Schema for evaluation request."""
    resume_id: int
    job_id: int
    custom_weights: Optional[Dict[str, float]] = None
    
    @validator('custom_weights')
    def validate_weights(cls, v):
        if v is None:
            return v
        
        # Check that weights are valid
        allowed_keys = ['hard_skills', 'soft_skills', 'experience', 'education', 'semantic_match']
        for key in v.keys():
            if key not in allowed_keys:
                raise ValueError(f'Invalid weight key: {key}. Allowed keys: {", ".join(allowed_keys)}')
        
        # Check that values are between 0 and 1
        for key, value in v.items():
            if not 0 <= value <= 1:
                raise ValueError(f'Weight values must be between 0 and 1, got {value} for {key}')
        
        # Check that weights sum to approximately 1.0
        if abs(sum(v.values()) - 1.0) > 0.01:
            raise ValueError('Custom weights must sum to 1.0')
        
        return v


class BatchEvaluationRequest(BaseModel):
    """Schema for batch evaluation request."""
    resume_ids: List[int]
    job_id: int
    custom_weights: Optional[Dict[str, float]] = None
    
    @validator('resume_ids')
    def validate_resume_ids(cls, v):
        if len(v) == 0:
            raise ValueError('At least one resume ID must be provided')
        if len(v) > 100:
            raise ValueError('Maximum 100 resume IDs allowed per batch')
        return v


class EvaluationResponse(BaseModel):
    """Schema for evaluation response."""
    id: int
    resume_id: int
    job_description_id: int
    overall_score: float
    hard_skills_score: float
    soft_skills_score: float
    experience_score: float
    education_score: float
    matching_skills: List[str]
    missing_skills: List[str]
    additional_skills: List[str]
    suitability: str
    recommendation: Optional[str]
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    personalized_feedback: Optional[str]
    percentile_rank: Optional[float]
    processing_time: Optional[float]
    confidence_score: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True


class EvaluationListResponse(BaseModel):
    """Schema for evaluation list response."""
    evaluations: List[EvaluationResponse]
    total: int
    resume_id: Optional[int] = None
    job_id: Optional[int] = None
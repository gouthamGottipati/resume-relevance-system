from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class DashboardOverview(BaseModel):
    """Schema for dashboard overview."""
    total_resumes: int
    total_jobs: int
    total_evaluations: int
    average_score: float
    suitability_distribution: Dict[str, int]
    top_skills_in_demand: List[Dict[str, Any]]
    recent_evaluations: List[Dict[str, Any]]


class SkillAnalytics(BaseModel):
    """Schema for skill analytics."""
    top_skills_in_demand: List[Dict[str, Any]]
    biggest_skill_gaps: List[Dict[str, Any]]
    undersupplied_skills: List[Dict[str, Any]]
    oversupplied_skills: List[Dict[str, Any]]
    total_unique_skills_demanded: int
    total_unique_skills_supplied: int


class CandidateInsights(BaseModel):
    """Schema for candidate insights."""
    score_statistics: Dict[str, float]
    score_distribution: Dict[str, int]
    experience_analysis: Dict[str, int]
    location_analysis: Dict[str, int]
    top_candidates: List[Dict[str, Any]]
    total_candidates_evaluated: int


class HiringTrends(BaseModel):
    """Schema for hiring trends."""
    total_evaluations: int
    average_score_trend: Dict[str, Any]
    suitability_trends: Dict[str, float]
    top_growing_skills: List[Dict[str, Any]]
    evaluation_volume_by_week: Dict[str, int]
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from app.core.database.models import Resume, JobDescription, ResumeEvaluation, Analytics
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class AnalyticsService:
    """Service for analytics and insights."""
    
    def __init__(self):
        pass
    
    async def get_dashboard_overview(
        self,
        db: Session,
        user_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get overview statistics for dashboard."""
        
        # Date range
        start_date = datetime.now() - timedelta(days=days)
        
        # Base queries
        resume_query = db.query(Resume)
        job_query = db.query(JobDescription)
        evaluation_query = db.query(ResumeEvaluation)
        
        # Filter by user if specified
        if user_id:
            job_query = job_query.filter(JobDescription.created_by == user_id)
            evaluation_query = evaluation_query.join(JobDescription).filter(
                JobDescription.created_by == user_id
            )
        
        # Filter by date range
        resume_query = resume_query.filter(Resume.created_at >= start_date)
        job_query = job_query.filter(JobDescription.created_at >= start_date)
        evaluation_query = evaluation_query.filter(ResumeEvaluation.created_at >= start_date)
        
        # Calculate statistics
        total_resumes = resume_query.count()
        total_jobs = job_query.count()
        total_evaluations = evaluation_query.count()
        
        # Average scores
        avg_score = evaluation_query.with_entities(
            func.avg(ResumeEvaluation.overall_score)
        ).scalar() or 0
        
        # Suitability distribution
        suitability_distribution = {}
        for suitability in ['High', 'Medium', 'Low']:
            count = evaluation_query.filter(
                ResumeEvaluation.suitability == suitability
            ).count()
            suitability_distribution[suitability.lower()] = count
        
        # Top skills in demand
        top_skills = self._get_top_skills_in_demand(db, user_id, days)
        
        # Recent activity
        recent_evaluations = evaluation_query.order_by(
            ResumeEvaluation.created_at.desc()
        ).limit(5).all()
        
        return {
            'total_resumes': total_resumes,
            'total_jobs': total_jobs,
            'total_evaluations': total_evaluations,
            'average_score': round(avg_score, 1),
            'suitability_distribution': suitability_distribution,
            'top_skills_in_demand': top_skills,
            'recent_evaluations': [
                {
                    'id': e.id,
                    'score': e.overall_score,
                    'suitability': e.suitability,
                    'created_at': e.created_at.isoformat()
                }
                for e in recent_evaluations
            ]
        }
    
    async def get_skill_analytics(
        self,
        db: Session,
        user_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get skill-based analytics."""
        
        start_date = datetime.now() - timedelta(days=days)
        
        # Get all evaluations in date range
        evaluation_query = db.query(ResumeEvaluation).filter(
            ResumeEvaluation.created_at >= start_date
        )
        
        if user_id:
            evaluation_query = evaluation_query.join(JobDescription).filter(
                JobDescription.created_by == user_id
            )
        
        evaluations = evaluation_query.all()
        
        # Analyze skills
        skill_demand = {}  # Skill -> count of JDs requiring it
        skill_supply = {}  # Skill -> count of resumes having it
        skill_gaps = {}    # Skill -> count of times it was missing
        
        for evaluation in evaluations:
            # Required skills (demand)
            if evaluation.matching_skills:
                for skill in evaluation.matching_skills:
                    skill_demand[skill] = skill_demand.get(skill, 0) + 1
            
            # Missing skills (gaps)
            if evaluation.missing_skills:
                for skill in evaluation.missing_skills:
                    skill_gaps[skill] = skill_gaps.get(skill, 0) + 1
        
        # Calculate supply from resumes
        resumes = db.query(Resume).filter(Resume.created_at >= start_date).all()
        for resume in resumes:
            if resume.skills:
                for skill in resume.skills:
                    skill_supply[skill] = skill_supply.get(skill, 0) + 1
        
        # Most in-demand skills
        top_demand = sorted(skill_demand.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Biggest skill gaps
        top_gaps = sorted(skill_gaps.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Supply vs demand ratio
        supply_demand_ratio = {}
        for skill in skill_demand:
            supply = skill_supply.get(skill, 0)
            demand = skill_demand[skill]
            ratio = supply / demand if demand > 0 else 0
            supply_demand_ratio[skill] = ratio
        
        # Most oversupplied and undersupplied skills
        sorted_ratio = sorted(supply_demand_ratio.items(), key=lambda x: x[1])
        undersupplied = sorted_ratio[:5]  # Lowest ratios
        oversupplied = sorted(supply_demand_ratio.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'top_skills_in_demand': [{'skill': skill, 'count': count} for skill, count in top_demand],
            'biggest_skill_gaps': [{'skill': skill, 'count': count} for skill, count in top_gaps],
            'undersupplied_skills': [{'skill': skill, 'ratio': ratio} for skill, ratio in undersupplied],
            'oversupplied_skills': [{'skill': skill, 'ratio': ratio} for skill, ratio in oversupplied],
            'total_unique_skills_demanded': len(skill_demand),
            'total_unique_skills_supplied': len(skill_supply)
        }
    
    async def get_candidate_insights(
        self,
        db: Session,
        user_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get insights about candidates."""
        
        start_date = datetime.now() - timedelta(days=days)
        
        # Get evaluations
        evaluation_query = db.query(ResumeEvaluation).filter(
            ResumeEvaluation.created_at >= start_date
        )
        
        if user_id:
            evaluation_query = evaluation_query.join(JobDescription).filter(
                JobDescription.created_by == user_id
            )
        
        evaluations = evaluation_query.all()
        
        if not evaluations:
            return self._empty_candidate_insights()
        
        # Score distribution
        scores = [e.overall_score for e in evaluations]
        score_stats = {
            'mean': np.mean(scores),
            'median': np.median(scores),
            'std': np.std(scores),
            'min': np.min(scores),
            'max': np.max(scores)
        }
        
        # Score ranges
        score_ranges = {
            '90-100': len([s for s in scores if 90 <= s <= 100]),
            '80-89': len([s for s in scores if 80 <= s < 90]),
            '70-79': len([s for s in scores if 70 <= s < 80]),
            '60-69': len([s for s in scores if 60 <= s < 70]),
            'Below 60': len([s for s in scores if s < 60])
        }
        
        # Experience analysis
        resumes = db.query(Resume).join(ResumeEvaluation).filter(
            ResumeEvaluation.created_at >= start_date
        ).all()
        
        experience_stats = self._analyze_experience_levels(resumes)
        
        # Location analysis
        location_stats = self._analyze_candidate_locations(resumes)
        
        # Top performing candidates
        top_candidates = sorted(evaluations, key=lambda x: x.overall_score, reverse=True)[:10]
        
        return {
            'score_statistics': {k: round(v, 2) for k, v in score_stats.items()},
            'score_distribution': score_ranges,
            'experience_analysis': experience_stats,
            'location_analysis': location_stats,
            'top_candidates': [
                {
                    'evaluation_id': e.id,
                    'resume_id': e.resume_id,
                    'candidate_name': e.resume.candidate_name if e.resume else 'Unknown',
                    'score': e.overall_score,
                    'suitability': e.suitability
                }
                for e in top_candidates
            ],
            'total_candidates_evaluated': len(evaluations)
        }
    
    def _get_top_skills_in_demand(
        self,
        db: Session,
        user_id: Optional[int],
        days: int
    ) -> List[Dict[str, Any]]:
        """Get most frequently required skills."""
        
        start_date = datetime.now() - timedelta(days=days)
        
        job_query = db.query(JobDescription).filter(
            JobDescription.created_at >= start_date
        )
        
        if user_id:
            job_query = job_query.filter(JobDescription.created_by == user_id)
        
        jobs = job_query.all()
        
        skill_counts = {}
        for job in jobs:
            if job.required_skills:
                for skill in job.required_skills:
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        # Return top 10 skills
        top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        return [{'skill': skill, 'demand_count': count} for skill, count in top_skills]
    
    def _analyze_experience_levels(self, resumes: List[Resume]) -> Dict[str, Any]:
        """Analyze experience levels of candidates."""
        
        experience_levels = {
            'Entry (0-2 years)': 0,
            'Mid (2-5 years)': 0,
            'Senior (5-10 years)': 0,
            'Expert (10+ years)': 0,
            'Unknown': 0
        }
        
        for resume in resumes:
            exp_years = resume.experience_years or 0
            
            if exp_years == 0:
                experience_levels['Unknown'] += 1
            elif exp_years <= 2:
                experience_levels['Entry (0-2 years)'] += 1
            elif exp_years <= 5:
                experience_levels['Mid (2-5 years)'] += 1
            elif exp_years <= 10:
                experience_levels['Senior (5-10 years)'] += 1
            else:
                experience_levels['Expert (10+ years)'] += 1
        
        return experience_levels
    
    def _analyze_candidate_locations(self, resumes: List[Resume]) -> Dict[str, int]:
        """Analyze candidate locations."""
        
        location_counts = {}
        
        for resume in resumes:
            location = resume.candidate_location or 'Unknown'
            # Simplify location to city/country
            if ',' in location:
                location = location.split(',')[-1].strip()  # Take last part (usually country/state)
            
            location_counts[location] = location_counts.get(location, 0) + 1
        
        # Return top 10 locations
        sorted_locations = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_locations[:10])
    
    def _empty_candidate_insights(self) -> Dict[str, Any]:
        """Return empty insights when no data available."""
        return {
            'score_statistics': {'mean': 0, 'median': 0, 'std': 0, 'min': 0, 'max': 0},
            'score_distribution': {k: 0 for k in ['90-100', '80-89', '70-79', '60-69', 'Below 60']},
            'experience_analysis': {k: 0 for k in ['Entry (0-2 years)', 'Mid (2-5 years)', 'Senior (5-10 years)', 'Expert (10+ years)', 'Unknown']},
            'location_analysis': {},
            'top_candidates': [],
            'total_candidates_evaluated': 0
        }
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
from app.core.ai_pipeline.skill_extractor import SkillProfile
from app.core.ai_pipeline.semantic_matcher import SemanticMatchResult
from app.core.ai_pipeline.resume_parser import ParsedResume
from app.core.ai_pipeline.jd_parser import ParsedJobDescription
from app.config import settings
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ScoringWeights:
    """Configuration for scoring weights."""
    hard_skills: float = 0.35
    soft_skills: float = 0.15
    experience: float = 0.25
    education: float = 0.15
    semantic_match: float = 0.10
    
    def validate(self):
        """Ensure weights sum to 1.0."""
        total = self.hard_skills + self.soft_skills + self.experience + self.education + self.semantic_match
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Scoring weights must sum to 1.0, got {total}")


@dataclass
class DetailedScores:
    """Detailed breakdown of all scoring components."""
    # Main component scores (0-100)
    hard_skills_score: float
    soft_skills_score: float
    experience_score: float
    education_score: float
    semantic_match_score: float
    
    # Sub-component scores
    technical_skills_score: float
    domain_expertise_score: float
    tools_platforms_score: float
    years_experience_score: float
    experience_relevance_score: float
    education_level_score: float
    education_relevance_score: float
    
    # Matching details
    skills_matched_count: int
    skills_required_count: int
    skills_missing_count: int
    skills_additional_count: int
    
    # Confidence and quality metrics
    parsing_confidence: float
    matching_confidence: float
    overall_confidence: float


@dataclass
class FinalScore:
    """Final scoring result with verdict."""
    overall_score: float  # 0-100
    detailed_scores: DetailedScores
    suitability: str  # High, Medium, Low
    percentile_rank: Optional[float] = None
    confidence_level: str = "medium"  # low, medium, high
    
    def get_verdict_details(self) -> Dict[str, str]:
        """Get detailed verdict explanation."""
        if self.suitability == "High":
            return {
                "verdict": "Strong Match",
                "description": "Excellent candidate with strong alignment to job requirements",
                "action": "Recommend for interview"
            }
        elif self.suitability == "Medium":
            return {
                "verdict": "Potential Match",
                "description": "Good candidate with some skill gaps or experience differences",
                "action": "Consider for interview with skill assessment"
            }
        else:
            return {
                "verdict": "Weak Match",
                "description": "Limited alignment with job requirements",
                "action": "Consider only if few alternatives available"
            }


class AdvancedScoringEngine:
    """Advanced scoring engine with multi-dimensional evaluation."""
    
    def __init__(self, weights: Optional[ScoringWeights] = None):
        self.weights = weights or ScoringWeights()
        self.weights.validate()
        
        # Thresholds for different components
        self.thresholds = {
            'high_score': settings.high_threshold,
            'medium_score': settings.medium_threshold,
            'low_score': settings.low_threshold,
            'experience_penalty_threshold': 0.5,
            'education_boost_threshold': 0.8
        }
    def calculate_comprehensive_score(
        self,
        parsed_resume: ParsedResume,
        skill_profile: SkillProfile,
        semantic_match: SemanticMatchResult,
        jd_parsed: ParsedJobDescription
    ) -> FinalScore:
        """Calculate comprehensive score with detailed breakdown."""
        
        logger.info("Calculating comprehensive score")
        
        # Calculate individual component scores
        hard_skills_score = self._calculate_hard_skills_score(skill_profile, semantic_match, jd_parsed)
        soft_skills_score = self._calculate_soft_skills_score(skill_profile, jd_parsed)
        experience_score = self._calculate_experience_score(parsed_resume, jd_parsed)
        education_score = self._calculate_education_score(parsed_resume, jd_parsed)
        semantic_score = self._calculate_semantic_score(semantic_match)
        
        # Calculate weighted overall score
        overall_score = (
            hard_skills_score * self.weights.hard_skills +
            soft_skills_score * self.weights.soft_skills +
            experience_score * self.weights.experience +
            education_score * self.weights.education +
            semantic_score * self.weights.semantic_match
        ) * 100
        
        # Calculate detailed sub-scores
        detailed_scores = self._calculate_detailed_scores(
            parsed_resume, skill_profile, semantic_match, jd_parsed,
            hard_skills_score, soft_skills_score, experience_score, education_score, semantic_score
        )
        
        # Determine suitability
        suitability = self._determine_suitability(overall_score, detailed_scores)
        
        # Calculate confidence level
        confidence_level = self._calculate_confidence_level(parsed_resume, semantic_match, detailed_scores)
        
        return FinalScore(
            overall_score=round(overall_score, 1),
            detailed_scores=detailed_scores,
            suitability=suitability,
            confidence_level=confidence_level
        )
    
    def _calculate_hard_skills_score(
        self, 
        skill_profile: SkillProfile, 
        semantic_match: SemanticMatchResult,
        jd_parsed: ParsedJobDescription
    ) -> float:
        """Calculate hard/technical skills score."""
        
        if not jd_parsed.required_skills:
            return 0.5  # Neutral score if no required skills specified
        
        total_required = len(jd_parsed.required_skills)
        matched_skills = len([m for m in semantic_match.skill_matches if m.confidence >= 0.7])
        
        # Base matching score
        base_score = matched_skills / total_required if total_required > 0 else 0
        
        # Bonus for skill diversity
        diversity_bonus = skill_profile.skill_diversity_score * 0.2
        
        # Bonus for high-confidence matches
        high_confidence_matches = len([m for m in semantic_match.skill_matches if m.confidence >= 0.9])
        confidence_bonus = (high_confidence_matches / total_required) * 0.1 if total_required > 0 else 0
        
        # Penalty for critical missing skills
        critical_skills = self._identify_critical_skills(jd_parsed.required_skills)
        missing_critical = len([s for s in critical_skills if s in semantic_match.missing_skills])
        critical_penalty = (missing_critical / len(critical_skills)) * 0.3 if critical_skills else 0
        
        final_score = base_score + diversity_bonus + confidence_bonus - critical_penalty
        return max(0, min(1, final_score))
    
    def _calculate_soft_skills_score(self, skill_profile: SkillProfile, jd_parsed: ParsedJobDescription) -> float:
        """Calculate soft skills score."""
        
        # Extract soft skills from JD requirements
        jd_soft_skills = self._extract_soft_skills_from_jd(jd_parsed)
        
        if not jd_soft_skills:
            # If no specific soft skills mentioned, score based on presence
            return 0.8 if skill_profile.soft_skills else 0.3
        
        # Match soft skills
        resume_soft_skills = [s.name.lower() for s in skill_profile.soft_skills]
        matched_soft_skills = 0
        
        for jd_skill in jd_soft_skills:
            if any(jd_skill.lower() in resume_skill for resume_skill in resume_soft_skills):
                matched_soft_skills += 1
        
        base_score = matched_soft_skills / len(jd_soft_skills) if jd_soft_skills else 0
        
        # Bonus for having multiple soft skills
        variety_bonus = min(len(skill_profile.soft_skills) / 10, 0.2)  # Up to 20% bonus
        
        return min(1, base_score + variety_bonus)
    
    def _calculate_experience_score(self, parsed_resume: ParsedResume, jd_parsed: ParsedJobDescription) -> float:
        """Calculate experience score based on years and relevance."""
        
        # Years of experience component
        years_score = self._calculate_years_experience_score(parsed_resume, jd_parsed)
        
        # Experience relevance component
        relevance_score = self._calculate_experience_relevance_score(parsed_resume, jd_parsed)
        
        # Combine with weights
        return years_score * 0.6 + relevance_score * 0.4
    
    def _calculate_years_experience_score(self, parsed_resume: ParsedResume, jd_parsed: ParsedJobDescription) -> float:
        """Calculate score based on years of experience."""
        
        candidate_years = parsed_resume.total_experience_years or 0
        required_years = jd_parsed.required_experience_years or 2  # Default to 2 years if not specified
        
        if candidate_years >= required_years:
            # Full score if meets requirement, bonus for significant experience
            base_score = 1.0
            if candidate_years > required_years * 1.5:
                return min(1.0, base_score + 0.1)  # 10% bonus for 50% more experience
            return base_score
        else:
            # Partial score based on how close they are
            ratio = candidate_years / required_years
            if ratio >= 0.75:  # 75% of required experience
                return 0.8
            elif ratio >= 0.5:  # 50% of required experience
                return 0.6
            else:
                return ratio * 0.5  # Steep penalty for very little experience
    
    def _calculate_experience_relevance_score(self, parsed_resume: ParsedResume, jd_parsed: ParsedJobDescription) -> float:
        """Calculate relevance of work experience to the job."""
        
        if not parsed_resume.work_experience:
            return 0.2
        
        relevance_scores = []
        
        for exp in parsed_resume.work_experience:
            # Check if job title contains relevant keywords
            title_relevance = self._calculate_title_relevance(exp.title, jd_parsed.title)
            
            # Check if company industry is relevant
            industry_relevance = self._calculate_industry_relevance(exp.company, jd_parsed.company)
            
            # Check if description contains relevant terms
            description_relevance = self._calculate_description_relevance(exp.description or [], jd_parsed)
            
            # Weight recent experience more heavily
            recency_weight = self._calculate_recency_weight(exp.end_date)
            
            exp_relevance = (title_relevance * 0.4 + industry_relevance * 0.2 + description_relevance * 0.4) * recency_weight
            relevance_scores.append(exp_relevance)
        
        # Return weighted average with more weight on most relevant experiences
        relevance_scores.sort(reverse=True)
        if len(relevance_scores) >= 3:
            return (relevance_scores[0] * 0.5 + relevance_scores[1] * 0.3 + relevance_scores[2] * 0.2)
        elif len(relevance_scores) == 2:
            return (relevance_scores[0] * 0.7 + relevance_scores[1] * 0.3)
        else:
            return relevance_scores[0] if relevance_scores else 0
    
    def _calculate_education_score(self, parsed_resume: ParsedResume, jd_parsed: ParsedJobDescription) -> float:
        """Calculate education score."""
        
        if not parsed_resume.education:
            return 0.3  # Base score for no education info
        
        education_level_score = self._calculate_education_level_score(parsed_resume.education, jd_parsed)
        education_relevance_score = self._calculate_education_relevance_score(parsed_resume.education, jd_parsed)
        
        return education_level_score * 0.6 + education_relevance_score * 0.4
    
    def _calculate_education_level_score(self, education_list, jd_parsed: ParsedJobDescription) -> float:
        """Calculate score based on education level."""
        
        # Define education hierarchy
        education_levels = {
            'phd': 5, 'doctorate': 5, 'doctoral': 5,
            'master': 4, 'mba': 4, 'ms': 4, 'ma': 4,
            'bachelor': 3, 'bs': 3, 'ba': 3,
            'associate': 2,
            'diploma': 1, 'certificate': 1
        }
        
        # Find highest education level
        max_level = 0
        for edu in education_list:
            if edu.degree:
                degree_lower = edu.degree.lower()
                for level_name, level_value in education_levels.items():
                    if level_name in degree_lower:
                        max_level = max(max_level, level_value)
                        break
        
        # Extract required education level from JD
        required_level = self._extract_required_education_level(jd_parsed)
        
        if max_level >= required_level:
            return 1.0
        elif max_level >= required_level - 1:
            return 0.8
        else:
            return 0.5
    
    def _calculate_education_relevance_score(self, education_list, jd_parsed: ParsedJobDescription) -> float:
        """Calculate relevance of education to the job."""
        
        job_keywords = self._extract_job_domain_keywords(jd_parsed)
        if not job_keywords:
            return 0.7  # Neutral score if can't determine relevance
        
        max_relevance = 0
        for edu in education_list:
            if edu.degree:
                degree_text = edu.degree.lower()
                relevance = sum(1 for keyword in job_keywords if keyword in degree_text)
                max_relevance = max(max_relevance, relevance)
        
        return min(1.0, max_relevance / len(job_keywords)) if job_keywords else 0.7
    
    def _calculate_semantic_score(self, semantic_match: SemanticMatchResult) -> float:
        """Calculate semantic similarity score."""
        return semantic_match.overall_similarity
    
    def _calculate_detailed_scores(
        self, parsed_resume, skill_profile, semantic_match, jd_parsed,
        hard_skills_score, soft_skills_score, experience_score, education_score, semantic_score
    ) -> DetailedScores:
        """Calculate detailed breakdown of all scores."""
        
        # Technical sub-scores
        technical_skills = [s for s in skill_profile.technical_skills]
        domain_expertise = [s for s in skill_profile.domain_expertise]
        tools_platforms = [s for s in skill_profile.tools_platforms]
        
        technical_skills_score = len(technical_skills) / 10 * 100  # Normalize to 0-100
        domain_expertise_score = len(domain_expertise) / 5 * 100
        tools_platforms_score = len(tools_platforms) / 8 * 100
        
        # Experience sub-scores
        years_experience_score = self._calculate_years_experience_score(parsed_resume, jd_parsed) * 100
        experience_relevance_score = self._calculate_experience_relevance_score(parsed_resume, jd_parsed) * 100
        
        # Education sub-scores
        education_level_score = self._calculate_education_level_score(parsed_resume.education or [], jd_parsed) * 100
        education_relevance_score = self._calculate_education_relevance_score(parsed_resume.education or [], jd_parsed) * 100
        
        # Matching statistics
        skills_matched = len(semantic_match.skill_matches)
        skills_required = len(jd_parsed.required_skills) if jd_parsed.required_skills else 0
        skills_missing = len(semantic_match.missing_skills)
        skills_additional = len(semantic_match.additional_skills)
        
        # Confidence metrics
        parsing_confidence = parsed_resume.parsing_confidence * 100
        matching_confidence = np.mean([m.confidence for m in semantic_match.skill_matches]) * 100 if semantic_match.skill_matches else 50
        overall_confidence = (parsing_confidence + matching_confidence) / 2
        
        return DetailedScores(
            hard_skills_score=round(hard_skills_score * 100, 1),
            soft_skills_score=round(soft_skills_score * 100, 1),
            experience_score=round(experience_score * 100, 1),
            education_score=round(education_score * 100, 1),
            semantic_match_score=round(semantic_score * 100, 1),
            technical_skills_score=round(min(technical_skills_score, 100), 1),
            domain_expertise_score=round(min(domain_expertise_score, 100), 1),
            tools_platforms_score=round(min(tools_platforms_score, 100), 1),
            years_experience_score=round(years_experience_score, 1),
            experience_relevance_score=round(experience_relevance_score, 1),
            education_level_score=round(education_level_score, 1),
            education_relevance_score=round(education_relevance_score, 1),
            skills_matched_count=skills_matched,
            skills_required_count=skills_required,
            skills_missing_count=skills_missing,
            skills_additional_count=skills_additional,
            parsing_confidence=round(parsing_confidence, 1),
            matching_confidence=round(matching_confidence, 1),
            overall_confidence=round(overall_confidence, 1)
        )
    
    def _determine_suitability(self, overall_score: float, detailed_scores: DetailedScores) -> str:
        """Determine suitability level based on score and other factors."""
        
        # Base determination on overall score
        if overall_score >= self.thresholds['high_score']:
            base_suitability = "High"
        elif overall_score >= self.thresholds['medium_score']:
            base_suitability = "Medium"
        else:
            base_suitability = "Low"
        
        # Adjust based on specific conditions
        
        # Downgrade if critical skills are completely missing
        if detailed_scores.skills_missing_count > detailed_scores.skills_matched_count:
            if base_suitability == "High":
                base_suitability = "Medium"
            elif base_suitability == "Medium":
                base_suitability = "Low"
        
        # Upgrade if exceptional in one area
        if (detailed_scores.experience_score >= 90 or 
            detailed_scores.hard_skills_score >= 95 or
            detailed_scores.education_score >= 90):
            if base_suitability == "Low" and overall_score >= 50:
                base_suitability = "Medium"
        
        # Consider confidence level
        if detailed_scores.overall_confidence < 60:
            if base_suitability == "High":
                base_suitability = "Medium"
        
        return base_suitability
    
    def _calculate_confidence_level(self, parsed_resume, semantic_match, detailed_scores) -> str:
        """Calculate overall confidence in the evaluation."""
        
        confidence_factors = [
            detailed_scores.parsing_confidence / 100,
            detailed_scores.matching_confidence / 100,
            min(detailed_scores.skills_matched_count / max(detailed_scores.skills_required_count, 1), 1.0),
            1.0 if parsed_resume.contact_info.email else 0.5,  # Complete contact info
            1.0 if parsed_resume.work_experience else 0.3,  # Has work experience
        ]
        
        avg_confidence = np.mean(confidence_factors)
        
        if avg_confidence >= 0.8:
            return "high"
        elif avg_confidence >= 0.6:
            return "medium"
        else:
            return "low"
    
    # Helper methods for specific calculations
    
    def _identify_critical_skills(self, required_skills: List[str]) -> List[str]:
        """Identify critical skills that are must-haves."""
        critical_keywords = ['required', 'must', 'essential', 'mandatory']
        return [skill for skill in required_skills if any(keyword in skill.lower() for keyword in critical_keywords)]
    
    def _extract_soft_skills_from_jd(self, jd_parsed: ParsedJobDescription) -> List[str]:
        """Extract soft skills mentioned in job description."""
        soft_skill_keywords = [
            'leadership', 'communication', 'teamwork', 'collaboration',
            'problem solving', 'analytical', 'creative', 'adaptable',
            'organized', 'detail-oriented', 'time management', 'interpersonal'
        ]
        
        jd_text = (jd_parsed.raw_content or '').lower()
        requirements = ' '.join(jd_parsed.requirements or []).lower()
        combined_text = jd_text + ' ' + requirements
        
        found_skills = []
        for skill in soft_skill_keywords:
            if skill in combined_text:
                found_skills.append(skill)
        
        return found_skills
    
    def _calculate_title_relevance(self, resume_title: str, jd_title: str) -> float:
        """Calculate relevance between job titles."""
        if not resume_title or not jd_title:
            return 0.5
        
        resume_words = set(resume_title.lower().split())
        jd_words = set(jd_title.lower().split())
        
        common_words = resume_words.intersection(jd_words)
        total_words = resume_words.union(jd_words)
        
        return len(common_words) / len(total_words) if total_words else 0
    
    def _calculate_industry_relevance(self, resume_company: str, jd_company: str) -> float:
        """Calculate industry relevance (simplified)."""
        # This would ideally use a company/industry database
        if not resume_company or not jd_company:
            return 0.5
        
        # Simple keyword matching for now
        resume_words = set(resume_company.lower().split())
        jd_words = set(jd_company.lower().split())
        
        if resume_words.intersection(jd_words):
            return 0.9
        else:
            return 0.4  # Different companies, assume different but not necessarily bad
    
    def _calculate_description_relevance(self, description_list: List[str], jd_parsed: ParsedJobDescription) -> float:
        """Calculate relevance of job description to JD requirements."""
        if not description_list:
            return 0.3
        
        description_text = ' '.join(description_list).lower()
        jd_keywords = []
        
        # Extract keywords from JD
        if jd_parsed.required_skills:
            jd_keywords.extend([skill.lower() for skill in jd_parsed.required_skills])
        if jd_parsed.responsibilities:
            for resp in jd_parsed.responsibilities:
                jd_keywords.extend(resp.lower().split())
        
        if not jd_keywords:
            return 0.5
        
        # Count matches
        matches = sum(1 for keyword in jd_keywords if keyword in description_text)
        return min(1.0, matches / len(jd_keywords))
    
    def _calculate_recency_weight(self, end_date: Optional[str]) -> float:
        """Calculate weight based on how recent the experience is."""
        if not end_date or end_date.lower() in ['present', 'current', 'now']:
            return 1.0  # Current job gets full weight
        
        # This is simplified - would need proper date parsing
        current_year = datetime.now().year
        try:
            if any(str(year) in end_date for year in range(current_year - 10, current_year + 1)):
                years_ago = current_year - int([year for year in range(current_year - 10, current_year + 1) if str(year) in end_date][0])
                return max(0.5, 1.0 - (years_ago * 0.1))  # Decay by 10% per year
        except:
            pass
        
        return 0.7  # Default weight for uncertain dates
    
    def _extract_required_education_level(self, jd_parsed: ParsedJobDescription) -> int:
        """Extract required education level from JD."""
        jd_text = (jd_parsed.raw_content or '').lower()
        requirements = ' '.join(jd_parsed.requirements or []).lower()
        combined_text = jd_text + ' ' + requirements
        
        if any(word in combined_text for word in ['phd', 'doctorate', 'doctoral']):
            return 5
        elif any(word in combined_text for word in ['master', 'mba', 'ms', 'ma']):
            return 4
        elif any(word in combined_text for word in ['bachelor', 'bs', 'ba', 'degree']):
            return 3
        elif any(word in combined_text for word in ['associate']):
            return 2
        else:
            return 2  # Default to associate level
    
    def _extract_job_domain_keywords(self, jd_parsed: ParsedJobDescription) -> List[str]:
        """Extract domain-specific keywords from job description."""
        domain_keywords = {
            'software': ['software', 'programming', 'development', 'engineering', 'computer'],
            'data': ['data', 'analytics', 'science', 'machine learning', 'statistics'],
            'marketing': ['marketing', 'digital', 'campaign', 'brand', 'advertising'],
            'finance': ['finance', 'accounting', 'financial', 'investment', 'banking'],
            'sales': ['sales', 'business development', 'revenue', 'client', 'customer']
        }
        
        jd_text = jd_parsed.title.lower() + ' ' + (jd_parsed.raw_content or '').lower()
        
        relevant_keywords = []
        for domain, keywords in domain_keywords.items():
            if any(keyword in jd_text for keyword in keywords):
                relevant_keywords.extend(keywords)
                break  # Take first matching domain
        
        return relevant_keywords[:5]  # Limit to 5 keywords



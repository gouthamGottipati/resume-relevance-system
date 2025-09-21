from typing import Dict, List, Optional
from dataclasses import dataclass
import openai
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.schema import HumanMessage
from app.core.ai_pipeline.scoring_engine import FinalScore, DetailedScores
from app.core.ai_pipeline.semantic_matcher import SemanticMatchResult
from app.core.ai_pipeline.resume_parser import ParsedResume
from app.core.ai_pipeline.jd_parser import ParsedJobDescription
from app.config import settings
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PersonalizedFeedback:
    """Comprehensive personalized feedback for candidates."""
    overall_assessment: str
    strengths: List[str]
    areas_for_improvement: List[str]
    specific_recommendations: List[str]
    skill_gap_analysis: Dict[str, List[str]]
    career_advancement_tips: List[str]
    interview_preparation_tips: List[str]
    confidence_level: str


class AIFeedbackGenerator:
    """Generate personalized feedback using LLM."""
    
    def __init__(self):
        self.llm = None
        self._initialize_llm()
        self._create_prompt_templates()
    
    def _initialize_llm(self):
        """Initialize the language model."""
        try:
            if settings.openai_api_key:
                self.llm = OpenAI(
                    openai_api_key=settings.openai_api_key,
                    temperature=settings.temperature,
                    max_tokens=settings.max_tokens
                )
                logger.info("Initialized OpenAI LLM for feedback generation")
            else:
                logger.warning("OpenAI API key not provided. Feedback will use templates.")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
    
    def _create_prompt_templates(self):
        """Create prompt templates for different types of feedback."""
        
        self.overall_assessment_prompt = PromptTemplate(
            input_variables=["candidate_name", "job_title", "overall_score", "suitability", "key_strengths", "key_gaps"],
            template="""
            As an expert career counselor and technical recruiter, provide a comprehensive overall assessment 
            for {candidate_name} who applied for the {job_title} position.

            Evaluation Results:
            - Overall Score: {overall_score}/100
            - Suitability: {suitability}
            - Key Strengths: {key_strengths}
            - Key Gaps: {key_gaps}

            Provide a balanced, professional, and encouraging overall assessment in 2-3 paragraphs that:
            1. Summarizes their candidacy strength
            2. Highlights main competitive advantages
            3. Addresses key areas for development
            4. Maintains an encouraging and constructive tone

            Focus on actionable insights and growth opportunities rather than just evaluation.
            """
        )
        
        self.skill_gap_prompt = PromptTemplate(
            input_variables=["missing_skills", "job_title", "current_skills"],
            template="""
            Analyze the skill gap for a {job_title} position candidate:

            Missing Skills: {missing_skills}
            Current Skills: {current_skills}

            For each missing skill, provide:
            1. Why it's important for the role
            2. Specific learning resources (courses, books, platforms)
            3. Practical ways to gain experience
            4. Timeline for skill development
            5. Alternative skills that could compensate

            Format as a structured analysis with actionable recommendations.
            """
        )
        
        self.career_advancement_prompt = PromptTemplate(
            input_variables=["current_level", "target_role", "strengths", "gaps", "industry"],
            template="""
            Provide career advancement advice for someone transitioning to {target_role} in {industry}:

            Current Level: {current_level}
            Strengths: {strengths}
            Development Areas: {gaps}

            Provide specific advice on:
            1. Career progression pathway
            2. Skills to prioritize for development
            3. Industry certifications to pursue
            4. Networking strategies
            5. Project ideas to build portfolio
            6. Timeline for career advancement

            Make recommendations specific, actionable, and encouraging.
            """
        )
    
    def generate_comprehensive_feedback(
        self,
        parsed_resume: ParsedResume,
        final_score: FinalScore,
        semantic_match: SemanticMatchResult,
        jd_parsed: ParsedJobDescription
    ) -> PersonalizedFeedback:
        """Generate comprehensive personalized feedback."""
        
        logger.info("Generating comprehensive personalized feedback")
        
        # Extract key information
        candidate_name = parsed_resume.contact_info.name or "Candidate"
        job_title = jd_parsed.title or "the position"
        
        # Generate different components of feedback
        overall_assessment = self._generate_overall_assessment(
            candidate_name, job_title, final_score, semantic_match
        )
        
        strengths = self._identify_strengths(parsed_resume, final_score, semantic_match)
        areas_for_improvement = self._identify_areas_for_improvement(final_score, semantic_match)
        specific_recommendations = self._generate_specific_recommendations(
            final_score, semantic_match, jd_parsed
        )
        
        skill_gap_analysis = self._analyze_skill_gaps(semantic_match, jd_parsed)
        career_advancement_tips = self._generate_career_tips(parsed_resume, jd_parsed, final_score)
        interview_tips = self._generate_interview_tips(final_score, semantic_match, jd_parsed)
        
        return PersonalizedFeedback(
            overall_assessment=overall_assessment,
            strengths=strengths,
            areas_for_improvement=areas_for_improvement,
            specific_recommendations=specific_recommendations,
            skill_gap_analysis=skill_gap_analysis,
            career_advancement_tips=career_advancement_tips,
            interview_preparation_tips=interview_tips,
            confidence_level=final_score.confidence_level
        )
    
    def _generate_overall_assessment(
        self, 
        candidate_name: str, 
        job_title: str, 
        final_score: FinalScore,
        semantic_match: SemanticMatchResult
    ) -> str:
        """Generate overall assessment using LLM or template."""
        
        # Prepare key information
        key_strengths = self._extract_top_strengths(final_score)
        key_gaps = semantic_match.missing_skills[:3]  # Top 3 missing skills
        
        if self.llm:
            try:
                chain = LLMChain(llm=self.llm, prompt=self.overall_assessment_prompt)
                response = chain.run(
                    candidate_name=candidate_name,
                    job_title=job_title,
                    overall_score=final_score.overall_score,
                    suitability=final_score.suitability,
                    key_strengths=", ".join(key_strengths),
                    key_gaps=", ".join(key_gaps) if key_gaps else "No significant gaps identified"
                )
                return response.strip()
            except Exception as e:
                logger.error(f"Error generating LLM assessment: {e}")
                return self._generate_template_assessment(candidate_name, job_title, final_score, key_strengths, key_gaps)
        else:
            return self._generate_template_assessment(candidate_name, job_title, final_score, key_strengths, key_gaps)
    
    def _generate_template_assessment(
        self, 
        candidate_name: str, 
        job_title: str, 
        final_score: FinalScore,
        key_strengths: List[str],
        key_gaps: List[str]
    ) -> str:
        """Generate assessment using templates when LLM is not available."""
        
        verdict_details = final_score.get_verdict_details()
        
        if final_score.suitability == "High":
            opening = f"{candidate_name} presents as a strong candidate for the {job_title} position with an overall score of {final_score.overall_score}/100."
            
            strengths_text = f"Key strengths include {', '.join(key_strengths[:3])}." if key_strengths else "The candidate demonstrates solid qualifications."
            
            if key_gaps:
                development_text = f"Areas for development include {', '.join(key_gaps)}, but these gaps are manageable and shouldn't prevent progression."
            else:
                development_text = "The candidate shows strong alignment with job requirements across all key areas."
                
        elif final_score.suitability == "Medium":
            opening = f"{candidate_name} shows potential for the {job_title} position with an overall score of {final_score.overall_score}/100."
            
            strengths_text = f"Notable strengths include {', '.join(key_strengths[:2])}." if key_strengths else "The candidate has several positive qualities."
            
            if key_gaps:
                development_text = f"Key development areas include {', '.join(key_gaps)}. With focused skill development, this candidate could become a strong fit."
            else:
                development_text = "While showing promise, some areas would benefit from further development."
                
        else:  # Low suitability
            opening = f"{candidate_name} has submitted an application for the {job_title} position with an overall score of {final_score.overall_score}/100."
            
            strengths_text = f"Positive aspects include {', '.join(key_strengths[:2])}." if key_strengths else "The candidate shows some relevant experience."
            
            if key_gaps:
                development_text = f"Significant skill gaps exist in {', '.join(key_gaps)}, which would require substantial development to meet role requirements."
            else:
                development_text = "Considerable development would be needed to align with the position requirements."
        
        return f"{opening} {strengths_text} {development_text} {verdict_details['action']} based on current organizational needs and candidate potential."
    
    def _extract_top_strengths(self, final_score: FinalScore) -> List[str]:
        """Extract top strengths based on scores."""
        strengths = []
        
        detailed = final_score.detailed_scores
        
        if detailed.hard_skills_score >= 80:
            strengths.append("strong technical skills")
        if detailed.experience_score >= 80:
            strengths.append("relevant experience")
        if detailed.education_score >= 80:
            strengths.append("solid educational background")
        if detailed.soft_skills_score >= 80:
            strengths.append("good interpersonal skills")
        if detailed.semantic_match_score >= 80:
            strengths.append("excellent job alignment")
        
        return strengths if strengths else ["general qualifications"]
    
    def _identify_strengths(
        self, 
        parsed_resume: ParsedResume,
        final_score: FinalScore,
        semantic_match: SemanticMatchResult
    ) -> List[str]:
        """Identify specific strengths."""
        strengths = []
        
        detailed = final_score.detailed_scores
        
        # Technical strengths
        if detailed.technical_skills_score >= 70:
            strengths.append(f"Strong technical skill set with {detailed.skills_matched_count} relevant technologies")
        
        # Experience strengths  
        if detailed.years_experience_score >= 70:
            exp_years = parsed_resume.total_experience_years or 0
            strengths.append(f"Solid experience foundation with {exp_years} years in the field")
        
        if detailed.experience_relevance_score >= 70:
            strengths.append("Highly relevant work experience aligned with job requirements")
        
        # Education strengths
        if detailed.education_level_score >= 70:
            strengths.append("Strong educational credentials")
        
        # Skill matching strengths
        if len(semantic_match.skill_matches) > 0:
            high_confidence_matches = [m for m in semantic_match.skill_matches if m.confidence >= 0.9]
            if high_confidence_matches:
                top_skills = [m.skill_name for m in high_confidence_matches[:3]]
                strengths.append(f"Excellent proficiency in key skills: {', '.join(top_skills)}")
        
        # Additional skills
        if semantic_match.additional_skills:
            strengths.append(f"Brings additional valuable skills beyond job requirements: {', '.join(semantic_match.additional_skills[:3])}")
        
        # Portfolio/Projects
        if parsed_resume.projects:
            strengths.append(f"Demonstrates practical application through {len(parsed_resume.projects)} documented projects")
        
        # Certifications
        if parsed_resume.certifications:
            strengths.append(f"Professional development through certifications: {', '.join(parsed_resume.certifications[:2])}")
        
        return strengths[:6]  # Limit to top 6 strengths
    
    def _identify_areas_for_improvement(
        self,
        final_score: FinalScore,
        semantic_match: SemanticMatchResult
    ) -> List[str]:
        """Identify areas needing improvement."""
        improvements = []
        
        detailed = final_score.detailed_scores
        
        # Technical skills gaps
        if detailed.hard_skills_score < 60:
            missing_count = len(semantic_match.missing_skills)
            improvements.append(f"Technical skills development needed - {missing_count} key skills missing")
        
        # Experience gaps
        if detailed.experience_score < 60:
            if detailed.years_experience_score < 60:
                improvements.append("Additional years of relevant experience would strengthen candidacy")
            if detailed.experience_relevance_score < 60:
                improvements.append("More directly relevant work experience in similar roles")
        
        # Education gaps
        if detailed.education_score < 60:
            improvements.append("Consider pursuing additional education or certifications")
        
        # Specific missing skills
        if semantic_match.missing_skills:
            critical_missing = semantic_match.missing_skills[:3]
            improvements.append(f"Develop proficiency in: {', '.join(critical_missing)}")
        
        # Soft skills
        if detailed.soft_skills_score < 50:
            improvements.append("Strengthen soft skills and professional communication abilities")
        
        # Overall confidence
        if detailed.overall_confidence < 70:
            improvements.append("Enhance resume presentation and provide more detailed skill descriptions")
        
        return improvements[:5]  # Limit to top 5 areas
    
    def _generate_specific_recommendations(
        self,
        final_score: FinalScore,
        semantic_match: SemanticMatchResult,
        jd_parsed: ParsedJobDescription
    ) -> List[str]:
        """Generate specific, actionable recommendations."""
        recommendations = []
        
        # Skill development recommendations
        if semantic_match.missing_skills:
            for skill in semantic_match.missing_skills[:3]:
                recommendations.append(f"Develop {skill} through online courses, tutorials, or hands-on projects")
        
        # Experience recommendations
        if final_score.detailed_scores.experience_relevance_score < 70:
            recommendations.append("Seek opportunities in similar industries or roles to build relevant experience")
        
        # Project recommendations
        recommendations.append("Create portfolio projects that demonstrate your skills in real-world scenarios")
        
        # Certification recommendations
        if jd_parsed.required_skills:
            tech_skills = [skill for skill in jd_parsed.required_skills if any(tech in skill.lower() for tech in ['aws', 'azure', 'google', 'microsoft', 'oracle'])]
            if tech_skills:
                recommendations.append(f"Pursue professional certifications in {tech_skills[0]} to validate your expertise")
        
        # Networking recommendations
        recommendations.append("Engage with professional communities and attend industry events to expand your network")
        
        # Resume enhancement
        if final_score.detailed_scores.overall_confidence < 80:
            recommendations.append("Enhance resume with more specific examples and quantified achievements")
        
        return recommendations[:6]
    
    def _analyze_skill_gaps(
        self,
        semantic_match: SemanticMatchResult,
        jd_parsed: ParsedJobDescription
    ) -> Dict[str, List[str]]:
        """Analyze skill gaps by category."""
        
        skill_gaps = {
            'critical_missing': [],
            'nice_to_have': [],
            'learning_resources': [],
            'alternative_skills': []
        }
        
        required_skills = jd_parsed.required_skills or []
        preferred_skills = jd_parsed.preferred_skills or []
        
        # Categorize missing skills
        for skill in semantic_match.missing_skills:
            if skill in required_skills:
                skill_gaps['critical_missing'].append(skill)
            elif skill in preferred_skills:
                skill_gaps['nice_to_have'].append(skill)
        
        # Generate learning resources for top missing skills
        for skill in semantic_match.missing_skills[:3]:
            resource = self._get_learning_resource(skill)
            if resource:
                skill_gaps['learning_resources'].append(f"{skill}: {resource}")
        
        # Suggest alternative skills
        for additional_skill in semantic_match.additional_skills[:2]:
            skill_gaps['alternative_skills'].append(f"{additional_skill} - leverage this existing skill")
        
        return skill_gaps
    
    def _get_learning_resource(self, skill: str) -> str:
        """Get learning resource recommendations for specific skills."""
        
        resource_map = {
            'python': 'Codecademy Python Course, Real Python tutorials',
            'java': 'Oracle Java Tutorials, Coursera Java Specialization',
            'javascript': 'MDN Web Docs, freeCodeCamp JavaScript curriculum',
            'react': 'React Official Tutorial, Scrimba React Course',
            'aws': 'AWS Training and Certification, A Cloud Guru',
            'docker': 'Docker Official Documentation, Docker Mastery course',
            'kubernetes': 'Kubernetes.io tutorials, CNCF training',
            'machine learning': 'Coursera ML Course, Kaggle Learn',
            'data science': 'DataCamp, edX Data Science MicroMasters',
            'project management': 'PMI certification, Coursera Project Management'
        }
        
        skill_lower = skill.lower()
        for key, resource in resource_map.items():
            if key in skill_lower:
                return resource
        
        return f"Online courses on platforms like Coursera, Udemy, or Pluralsight"
    
    def _generate_career_tips(
        self,
        parsed_resume: ParsedResume,
        jd_parsed: ParsedJobDescription,
        final_score: FinalScore
    ) -> List[str]:
        """Generate career advancement tips."""
        
        tips = []
        
        # Experience-based tips
        exp_years = parsed_resume.total_experience_years or 0
        if exp_years < 3:
            tips.append("Focus on building foundational experience through internships, entry-level positions, or freelance projects")
        elif exp_years < 7:
            tips.append("Consider specializing in high-demand areas while broadening your skill set")
        else:
            tips.append("Leverage your experience by mentoring others and taking on leadership roles")
        
        # Skill development tips
        if final_score.detailed_scores.technical_skills_score < 70:
            tips.append("Invest in continuous learning - dedicate 5-10 hours per week to skill development")
        
        # Industry-specific tips
        job_title_lower = (jd_parsed.title or '').lower()
        if 'senior' in job_title_lower or 'lead' in job_title_lower:
            tips.append("Develop leadership and mentoring skills to advance to senior positions")
        
        if 'manager' in job_title_lower:
            tips.append("Gain experience in project management, team leadership, and stakeholder communication")
        
        # General career tips
        tips.extend([
            "Build a strong professional online presence through LinkedIn and GitHub",
            "Attend industry conferences and networking events to stay current with trends",
            "Seek opportunities to present your work or write about your experiences",
            "Consider finding a mentor in your target role or industry"
        ])
        
        return tips[:6]
    
    def _generate_interview_tips(
        self,
        final_score: FinalScore,
        semantic_match: SemanticMatchResult,
        jd_parsed: ParsedJobDescription
    ) -> List[str]:
        """Generate interview preparation tips."""
        
        tips = []
        
        # Strengths to emphasize
        if final_score.detailed_scores.hard_skills_score >= 70:
            matched_skills = [m.skill_name for m in semantic_match.skill_matches[:3]]
            tips.append(f"Emphasize your strong technical skills, especially: {', '.join(matched_skills)}")
        
        if final_score.detailed_scores.experience_score >= 70:
            tips.append("Prepare detailed examples from your work experience that demonstrate problem-solving and impact")
        
        # Areas to address
        if semantic_match.missing_skills:
            tips.append(f"Be prepared to discuss how you would approach learning: {', '.join(semantic_match.missing_skills[:2])}")
        
        # General interview tips
        tips.extend([
            "Research the company's recent projects, values, and technology stack thoroughly",
            "Prepare specific examples using the STAR method (Situation, Task, Action, Result)",
            "Practice explaining technical concepts in simple terms for non-technical stakeholders",
            "Prepare thoughtful questions about the role, team, and company culture",
            "Review your resume and be ready to discuss any project or experience in detail"
        ])
        
        # Role-specific tips
        if 'engineer' in (jd_parsed.title or '').lower():
            tips.append("Be ready for technical coding challenges and system design discussions")
        elif 'manager' in (jd_parsed.title or '').lower():
            tips.append("Prepare examples of leadership, conflict resolution, and team management")
        
        return tips[:8]
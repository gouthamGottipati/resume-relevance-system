import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from fuzzywuzzy import fuzz, process
import faiss
from app.core.ai_pipeline.skill_extractor import SkillProfile, ExtractedSkill
from app.core.ai_pipeline.jd_parser import ParsedJobDescription
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SkillMatch:
    """Represents a skill match between resume and JD."""
    skill_name: str
    resume_skill: Optional[str]
    jd_skill: str
    match_type: str  # exact, fuzzy, semantic
    confidence: float
    semantic_similarity: Optional[float] = None


@dataclass
class SemanticMatchResult:
    """Result of semantic matching between resume and JD."""
    overall_similarity: float
    skill_matches: List[SkillMatch]
    missing_skills: List[str]
    additional_skills: List[str]
    category_similarities: Dict[str, float]
    embedding_similarity: float
    text_similarity: float


class SemanticMatcher:
    """Advanced semantic matching using embeddings and similarity metrics."""
    
    def __init__(self):
        self.sentence_transformer = None
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self._load_models()
        self._initialize_faiss_index()
    
    def _load_models(self):
        """Load sentence transformer model."""
        try:
            self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded sentence transformer for semantic matching")
        except Exception as e:
            logger.error(f"Failed to load sentence transformer: {e}")
    
    def _initialize_faiss_index(self):
        """Initialize FAISS index for fast similarity search."""
        try:
            # Initialize with 384 dimensions (MiniLM embedding size)
            self.faiss_index = faiss.IndexFlatIP(384)  # Inner product for cosine similarity
            logger.info("Initialized FAISS index")
        except Exception as e:
            logger.warning(f"FAISS not available: {e}")
            self.faiss_index = None
    
    def match_resume_to_jd(
        self, 
        resume_skills: SkillProfile, 
        jd_parsed: ParsedJobDescription,
        resume_text: str,
        jd_text: str
    ) -> SemanticMatchResult:
        """Perform comprehensive semantic matching."""
        
        logger.info("Performing semantic matching between resume and JD")
        
        # Extract all resume skills
        all_resume_skills = []
        all_resume_skills.extend([s.name for s in resume_skills.technical_skills])
        all_resume_skills.extend([s.name for s in resume_skills.soft_skills])
        all_resume_skills.extend([s.name for s in resume_skills.domain_expertise])
        all_resume_skills.extend([s.name for s in resume_skills.tools_platforms])
        
        # Get JD required skills
        jd_required_skills = jd_parsed.required_skills or []
        jd_preferred_skills = jd_parsed.preferred_skills or []
        all_jd_skills = jd_required_skills + jd_preferred_skills
        
        # Perform different types of matching
        skill_matches = self._match_skills_comprehensive(all_resume_skills, all_jd_skills)
        
        # Calculate missing and additional skills
        matched_jd_skills = [match.jd_skill for match in skill_matches]
        missing_skills = [skill for skill in jd_required_skills if skill not in matched_jd_skills]
        additional_skills = [skill for skill in all_resume_skills if skill not in [match.resume_skill for match in skill_matches if match.resume_skill]]
        
        # Calculate category-wise similarities
        category_similarities = self._calculate_category_similarities(resume_skills, jd_parsed)
        
        # Calculate overall text similarity
        embedding_similarity = self._calculate_embedding_similarity(resume_text, jd_text)
        text_similarity = self._calculate_tfidf_similarity(resume_text, jd_text)
        
        # Calculate overall similarity score
        overall_similarity = self._calculate_overall_similarity(
            skill_matches, len(jd_required_skills), embedding_similarity, text_similarity
        )
        
        return SemanticMatchResult(
            overall_similarity=overall_similarity,
            skill_matches=skill_matches,
            missing_skills=missing_skills,
            additional_skills=additional_skills,
            category_similarities=category_similarities,
            embedding_similarity=embedding_similarity,
            text_similarity=text_similarity
        )
    
    def _match_skills_comprehensive(self, resume_skills: List[str], jd_skills: List[str]) -> List[SkillMatch]:
        """Perform comprehensive skill matching using multiple techniques."""
        matches = []
        
        # 1. Exact matching (case-insensitive)
        exact_matches = self._exact_match_skills(resume_skills, jd_skills)
        matches.extend(exact_matches)
        
        # Get unmatched skills for further processing
        matched_resume_skills = [m.resume_skill for m in exact_matches if m.resume_skill]
        matched_jd_skills = [m.jd_skill for m in exact_matches]
        
        unmatched_resume = [s for s in resume_skills if s not in matched_resume_skills]
        unmatched_jd = [s for s in jd_skills if s not in matched_jd_skills]
        
        # 2. Fuzzy matching
        fuzzy_matches = self._fuzzy_match_skills(unmatched_resume, unmatched_jd)
        matches.extend(fuzzy_matches)
        
        # Update unmatched lists
        matched_resume_skills.extend([m.resume_skill for m in fuzzy_matches if m.resume_skill])
        matched_jd_skills.extend([m.jd_skill for m in fuzzy_matches])
        
        unmatched_resume = [s for s in unmatched_resume if s not in [m.resume_skill for m in fuzzy_matches if m.resume_skill]]
        unmatched_jd = [s for s in unmatched_jd if s not in [m.jd_skill for m in fuzzy_matches]]
        
        # 3. Semantic matching using embeddings
        if self.sentence_transformer and unmatched_resume and unmatched_jd:
            semantic_matches = self._semantic_match_skills(unmatched_resume, unmatched_jd)
            matches.extend(semantic_matches)
        
        return matches
    
    def _exact_match_skills(self, resume_skills: List[str], jd_skills: List[str]) -> List[SkillMatch]:
        """Perform exact skill matching."""
        matches = []
        resume_lower = [s.lower() for s in resume_skills]
        
        for jd_skill in jd_skills:
            jd_skill_lower = jd_skill.lower()
            if jd_skill_lower in resume_lower:
                resume_skill = resume_skills[resume_lower.index(jd_skill_lower)]
                matches.append(SkillMatch(
                    skill_name=jd_skill,
                    resume_skill=resume_skill,
                    jd_skill=jd_skill,
                    match_type="exact",
                    confidence=1.0
                ))
        
        return matches
    
    def _fuzzy_match_skills(self, resume_skills: List[str], jd_skills: List[str], threshold: float = 85) -> List[SkillMatch]:
        """Perform fuzzy skill matching."""
        matches = []
        
        for jd_skill in jd_skills:
            # Find best match in resume skills
            best_match = process.extractOne(jd_skill, resume_skills, scorer=fuzz.token_sort_ratio)
            
            if best_match and best_match[1] >= threshold:
                confidence = best_match[1] / 100.0
                matches.append(SkillMatch(
                    skill_name=jd_skill,
                    resume_skill=best_match[0],
                    jd_skill=jd_skill,
                    match_type="fuzzy",
                    confidence=confidence
                ))
        
        return matches
    
    def _semantic_match_skills(self, resume_skills: List[str], jd_skills: List[str], threshold: float = 0.7) -> List[SkillMatch]:
        """Perform semantic skill matching using embeddings."""
        if not self.sentence_transformer:
            return []
        
        matches = []
        
        # Generate embeddings
        resume_embeddings = self.sentence_transformer.encode(resume_skills)
        jd_embeddings = self.sentence_transformer.encode(jd_skills)
        
        # Calculate similarity matrix
        similarity_matrix = cosine_similarity(jd_embeddings, resume_embeddings)
        
        # Find best matches above threshold
        for i, jd_skill in enumerate(jd_skills):
            best_match_idx = np.argmax(similarity_matrix[i])
            best_similarity = similarity_matrix[i][best_match_idx]
            
            if best_similarity >= threshold:
                matches.append(SkillMatch(
                    skill_name=jd_skill,
                    resume_skill=resume_skills[best_match_idx],
                    jd_skill=jd_skill,
                    match_type="semantic",
                    confidence=float(best_similarity),
                    semantic_similarity=float(best_similarity)
                ))
        
        return matches
    
    def _calculate_category_similarities(self, resume_skills: SkillProfile, jd_parsed: ParsedJobDescription) -> Dict[str, float]:
        """Calculate similarity scores for different skill categories."""
        similarities = {}
        
        # Technical skills similarity
        resume_technical = [s.name for s in resume_skills.technical_skills]
        jd_technical = jd_parsed.required_skills or []
        
        if jd_technical:
            technical_similarity = self._calculate_jaccard_similarity(resume_technical, jd_technical)
            similarities['technical'] = technical_similarity
        
        # Tools/platforms similarity
        resume_tools = [s.name for s in resume_skills.tools_platforms]
        jd_tools = [skill for skill in (jd_parsed.required_skills or []) if 'cloud' in skill.lower() or 'tool' in skill.lower()]
        
        if jd_tools:
            tools_similarity = self._calculate_jaccard_similarity(resume_tools, jd_tools)
            similarities['tools'] = tools_similarity
        
        return similarities
    
    def _calculate_jaccard_similarity(self, list1: List[str], list2: List[str]) -> float:
        """Calculate Jaccard similarity between two lists."""
        set1 = set([item.lower() for item in list1])
        set2 = set([item.lower() for item in list2])
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_embedding_similarity(self, resume_text: str, jd_text: str) -> float:
        """Calculate semantic similarity using sentence embeddings."""
        if not self.sentence_transformer:
            return 0.0
        
        try:
            # Truncate texts to prevent memory issues
            resume_text = resume_text[:2000]
            jd_text = jd_text[:2000]
            
            embeddings = self.sentence_transformer.encode([resume_text, jd_text])
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating embedding similarity: {e}")
            return 0.0
    
    def _calculate_tfidf_similarity(self, resume_text: str, jd_text: str) -> float:
        """Calculate TF-IDF based similarity."""
        try:
            # Fit TF-IDF on both texts
            tfidf_matrix = self.tfidf_vectorizer.fit_transform([resume_text, jd_text])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating TF-IDF similarity: {e}")
            return 0.0
    
    def _calculate_overall_similarity(
        self, 
        skill_matches: List[SkillMatch], 
        total_required_skills: int,
        embedding_similarity: float,
        text_similarity: float
    ) -> float:
        """Calculate weighted overall similarity score."""
        
        # Skill matching score (40% weight)
        if total_required_skills > 0:
            skill_score = len(skill_matches) / total_required_skills
            # Weight by confidence
            weighted_skill_score = sum(match.confidence for match in skill_matches) / total_required_skills
            skill_component = min((skill_score + weighted_skill_score) / 2, 1.0)
        else:
            skill_component = 0.0
        
        # Semantic similarity score (35% weight)
        semantic_component = embedding_similarity
        
        # Text similarity score (25% weight)
        text_component = text_similarity
        
        # Weighted final score
        overall_score = (
            skill_component * 0.40 +
            semantic_component * 0.35 +
            text_component * 0.25
        )
        
        return min(overall_score, 1.0)
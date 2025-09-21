import pytest
from unittest.mock import Mock

from app.core.ai_pipeline.scoring_engine import AdvancedScoringEngine, ScoringWeights, FinalScore
from app.core.ai_pipeline.skill_extractor import SkillProfile, ExtractedSkill
from app.core.ai_pipeline.semantic_matcher import SemanticMatchResult, SkillMatch
from app.core.ai_pipeline.resume_parser import ParsedResume, ContactInfo
from app.core.ai_pipeline.jd_parser import ParsedJobDescription


class TestScoringEngine:
    """Test scoring engine functionality."""
    
    def setup_method(self):
        """Setup test cases."""
        self.scoring_engine = AdvancedScoringEngine()
    
    def test_scoring_weights_validation(self):
        """Test scoring weights validation."""
        # Valid weights
        valid_weights = ScoringWeights(
            hard_skills=0.4,
            soft_skills=0.2,
            experience=0.2,
            education=0.1,
            semantic_match=0.1
        )
        valid_weights.validate()  # Should not raise exception
        
        # Invalid weights (don't sum to 1.0)
        with pytest.raises(ValueError):
            invalid_weights = ScoringWeights(
                hard_skills=0.5,
                soft_skills=0.5,
                experience=0.5,
                education=0.5,
                semantic_match=0.5
            )
            invalid_weights.validate()
    
    def test_suitability_determination(self):
        """Test suitability level determination."""
        # High score should give High suitability
        high_score = 85.0
        mock_detailed_scores = Mock()
        mock_detailed_scores.skills_missing_count = 1
        mock_detailed_scores.skills_matched_count = 8
        mock_detailed_scores.overall_confidence = 85.0
        
        suitability = self.scoring_engine._determine_suitability(high_score, mock_detailed_scores)
        assert suitability == "High"
        
        # Low score should give Low suitability
        low_score = 30.0
        suitability = self.scoring_engine._determine_suitability(low_score, mock_detailed_scores)
        assert suitability == "Low"

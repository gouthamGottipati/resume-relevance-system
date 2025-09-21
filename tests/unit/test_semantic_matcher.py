import pytest
import numpy as np
from unittest.mock import Mock, patch

from app.core.ai_pipeline.semantic_matcher import SemanticMatcher, SkillMatch
from app.core.ai_pipeline.skill_extractor import SkillProfile, ExtractedSkill
from app.core.ai_pipeline.jd_parser import ParsedJobDescription


class TestSemanticMatcher:
    """Test semantic matching functionality."""
    
    def setup_method(self):
        """Setup test cases."""
        self.matcher = SemanticMatcher()
    
    def test_exact_skill_matching(self):
        """Test exact skill matching."""
        resume_skills = ['Python', 'JavaScript', 'React', 'Docker']
        jd_skills = ['Python', 'React', 'AWS', 'Kubernetes']
        
        matches = self.matcher._exact_match_skills(resume_skills, jd_skills)
        
        assert len(matches) == 2  # Python and React should match
        skill_names = [match.skill_name for match in matches]
        assert 'Python' in skill_names
        assert 'React' in skill_names
    
    def test_fuzzy_skill_matching(self):
        """Test fuzzy skill matching."""
        resume_skills = ['Javascript', 'ReactJS', 'PostgresQL']
        jd_skills = ['JavaScript', 'React', 'PostgreSQL']
        
        matches = self.matcher._fuzzy_match_skills(resume_skills, jd_skills, threshold=80)
        
        assert len(matches) >= 2  # Should match JavaScript and PostgreSQL
        
    def test_jaccard_similarity(self):
        """Test Jaccard similarity calculation."""
        list1 = ['Python', 'Java', 'React']
        list2 = ['Python', 'JavaScript', 'React', 'Angular']
        
        similarity = self.matcher._calculate_jaccard_similarity(list1, list2)
        
        # Should be 2/5 = 0.4 (Python and React are common, 5 total unique)
        assert 0.3 <= similarity <= 0.5
    
    @patch('app.core.ai_pipeline.semantic_matcher.SentenceTransformer')
    def test_semantic_matching_with_embeddings(self, mock_transformer):
        """Test semantic matching using embeddings."""
        # Mock sentence transformer
        mock_model = Mock()
        mock_model.encode.return_value = np.array([[1, 0], [0, 1], [0.5, 0.5]])
        mock_transformer.return_value = mock_model
        
        matcher = SemanticMatcher()
        matcher.sentence_transformer = mock_model
        
        resume_skills = ['Machine Learning', 'Data Science']
        jd_skills = ['ML', 'Artificial Intelligence', 'Data Analysis']
        
        matches = matcher._semantic_match_skills(resume_skills, jd_skills, threshold=0.3)
        
        assert isinstance(matches, list)
        # Should find at least one match given the mock embeddings

import pytest
from unittest.mock import Mock, patch
import tempfile
import os

from app.core.ai_pipeline.resume_parser import ResumeParser, ParsedResume, ContactInfo


class TestResumeParser:
    """Test resume parsing functionality."""
    
    def setup_method(self):
        """Setup test cases."""
        self.parser = ResumeParser()
    
    def test_extract_contact_info(self):
        """Test contact information extraction."""
        sample_text = """
        John Doe
        john.doe@email.com
        +1 (555) 123-4567
        linkedin.com/in/johndoe
        github.com/johndoe
        San Francisco, CA
        """
        
        contact = self.parser._extract_contact_info(sample_text)
        
        assert contact.name == "John Doe"
        assert contact.email == "john.doe@email.com"
        assert "555" in contact.phone
        assert "linkedin.com/in/johndoe" in contact.linkedin
        assert "github.com/johndoe" in contact.github
    
    def test_extract_skills(self):
        """Test skill extraction."""
        sample_text = """
        Technical Skills:
        Python, JavaScript, React, Node.js, AWS, Docker, Kubernetes
        
        Programming Languages: Java, C++, Go
        Databases: PostgreSQL, MongoDB, Redis
        """
        
        skills = self.parser._extract_skills(sample_text)
        
        expected_skills = ['Python', 'JavaScript', 'React', 'Node.js', 'AWS', 'Docker', 'Kubernetes']
        for skill in expected_skills:
            assert skill in [s.title() for s in skills]
    
    def test_extract_work_experience(self):
        """Test work experience extraction."""
        sample_text = """
        EXPERIENCE
        
        Senior Software Engineer at Google
        January 2020 - Present
        • Led development of microservices architecture
        • Managed team of 5 engineers
        • Improved system performance by 40%
        
        Software Engineer at Microsoft
        June 2018 - December 2019
        • Developed web applications using React
        • Collaborated with cross-functional teams
        """
        
        experience = self.parser._extract_work_experience(sample_text)
        
        assert len(experience) >= 1
        assert any("Google" in exp.company for exp in experience)
        assert any("Senior Software Engineer" in exp.title for exp in experience)
    
    def test_extract_education(self):
        """Test education extraction."""
        sample_text = """
        EDUCATION
        
        Master of Science in Computer Science
        Stanford University, Stanford, CA
        Graduated: 2018, GPA: 3.8/4.0
        
        Bachelor of Science in Software Engineering
        UC Berkeley, Berkeley, CA
        Graduated: 2016
        """
        
        education = self.parser._extract_education(sample_text)
        
        assert len(education) >= 1
        assert any("Stanford" in edu.institution for edu in education)
        assert any("Master" in edu.degree for edu in education)
    
    def test_calculate_experience_years(self):
        """Test experience years calculation."""
        from app.core.ai_pipeline.resume_parser import WorkExperience
        
        experiences = [
            WorkExperience(
                title="Senior Engineer",
                company="Google",
                start_date="2020",
                end_date="Present"
            ),
            WorkExperience(
                title="Engineer",
                company="Microsoft",
                start_date="2018",
                end_date="2020"
            )
        ]
        
        total_years = self.parser._calculate_total_experience(experiences)
        assert total_years is not None
        assert total_years > 0

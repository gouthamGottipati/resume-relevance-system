import re
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ParsedJobDescription:
    """Structured job description data."""
    title: str
    company: str
    location: Optional[str] = None
    department: Optional[str] = None
    job_type: Optional[str] = None
    experience_required: Optional[str] = None
    salary_range: Optional[str] = None
    
    # Parsed content
    summary: Optional[str] = None
    responsibilities: List[str] = None
    requirements: List[str] = None
    preferred_qualifications: List[str] = None
    
    # Extracted skills and requirements
    required_skills: List[str] = None
    preferred_skills: List[str] = None
    required_experience_years: Optional[int] = None
    education_requirements: List[str] = None
    
    # Benefits and perks
    benefits: List[str] = None
    
    # Metadata
    remote_allowed: bool = False
    urgency_level: str = "medium"
    raw_content: str = ""


class JobDescriptionParser:
    """Parser for job descriptions with advanced extraction."""
    
    def __init__(self):
        # Skill patterns for better recognition
        self.programming_languages = {
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 
            'ruby', 'go', 'rust', 'kotlin', 'swift', 'scala', 'r', 'matlab',
            'perl', 'bash', 'powershell'
        }
        
        self.frameworks_libraries = {
            'react', 'angular', 'vue', 'django', 'flask', 'spring', 'express',
            'node.js', 'tensorflow', 'pytorch', 'pandas', 'numpy', 'scipy',
            'bootstrap', 'jquery', 'laravel', 'rails'
        }
        
        self.databases = {
            'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
            'oracle', 'sqlite', 'cassandra', 'dynamodb', 'neo4j'
        }
        
        self.cloud_tools = {
            'aws', 'azure', 'gcp', 'google cloud', 'kubernetes', 'docker',
            'jenkins', 'ansible', 'terraform', 'chef', 'puppet'
        }
        
        # Experience patterns
        self.experience_patterns = [
            r'(\d+)\+?\s*(?:to\s+(\d+))?\s*years?\s+(?:of\s+)?experience',
            r'minimum\s+(\d+)\s+years?',
            r'at least\s+(\d+)\s+years?',
            r'(\d+)-(\d+)\s+years?'
        ]
        
        # Education patterns
        self.education_keywords = {
            'bachelor', 'master', 'phd', 'doctorate', 'associate', 'diploma',
            'degree', 'certification', 'bs', 'ba', 'ms', 'ma', 'mba'
        }
    
    def parse(self, raw_content: str, metadata: Dict = None) -> ParsedJobDescription:
        """Parse job description content."""
        if metadata is None:
            metadata = {}
        
        # Clean and normalize text
        cleaned_content = self._clean_text(raw_content)
        
        # Extract structured information
        summary = self._extract_summary(cleaned_content)
        responsibilities = self._extract_responsibilities(cleaned_content)
        requirements = self._extract_requirements(cleaned_content)
        preferred_quals = self._extract_preferred_qualifications(cleaned_content)
        benefits = self._extract_benefits(cleaned_content)
        
        # Extract skills and requirements
        required_skills = self._extract_required_skills(cleaned_content, requirements)
        preferred_skills = self._extract_preferred_skills(cleaned_content, preferred_quals)
        experience_years = self._extract_experience_years(cleaned_content)
        education_reqs = self._extract_education_requirements(cleaned_content)
        
        # Determine job characteristics
        remote_allowed = self._is_remote_allowed(cleaned_content)
        urgency_level = self._determine_urgency(cleaned_content)
        
        return ParsedJobDescription(
            title=metadata.get('title', ''),
            company=metadata.get('company', ''),
            location=metadata.get('location'),
            department=metadata.get('department'),
            job_type=metadata.get('job_type'),
            experience_required=metadata.get('experience_required'),
            salary_range=metadata.get('salary_range'),
            summary=summary,
            responsibilities=responsibilities,
            requirements=requirements,
            preferred_qualifications=preferred_quals,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            required_experience_years=experience_years,
            education_requirements=education_reqs,
            benefits=benefits,
            remote_allowed=remote_allowed,
            urgency_level=urgency_level,
            raw_content=raw_content
        )
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that might interfere
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)]', ' ', text)
        return text.strip()
    
    def _extract_summary(self, text: str) -> Optional[str]:
        """Extract job summary/overview."""
        summary_keywords = [
            'job summary', 'overview', 'about the role', 'position summary',
            'job description', 'role description', 'summary'
        ]
        
        return self._extract_section(text, summary_keywords, max_sentences=5)
    
    def _extract_responsibilities(self, text: str) -> List[str]:
        """Extract job responsibilities."""
        resp_keywords = [
            'responsibilities', 'duties', 'role responsibilities',
            'key responsibilities', 'what you\'ll do', 'you will'
        ]
        
        section_text = self._extract_section(text, resp_keywords)
        if section_text:
            return self._extract_bullet_points(section_text)
        return []
    
    def _extract_requirements(self, text: str) -> List[str]:
        """Extract job requirements."""
        req_keywords = [
            'requirements', 'qualifications', 'required qualifications',
            'must have', 'required skills', 'essential skills',
            'minimum requirements', 'required experience'
        ]
        
        section_text = self._extract_section(text, req_keywords)
        if section_text:
            return self._extract_bullet_points(section_text)
        return []
    
    def _extract_preferred_qualifications(self, text: str) -> List[str]:
        """Extract preferred qualifications."""
        pref_keywords = [
            'preferred', 'nice to have', 'bonus', 'preferred qualifications',
            'additional skills', 'plus', 'preferred experience'
        ]
        
        section_text = self._extract_section(text, pref_keywords)
        if section_text:
            return self._extract_bullet_points(section_text)
        return []
    
    def _extract_benefits(self, text: str) -> List[str]:
        """Extract benefits and perks."""
        benefits_keywords = [
            'benefits', 'perks', 'what we offer', 'compensation',
            'package', 'why join us'
        ]
        
        section_text = self._extract_section(text, benefits_keywords)
        if section_text:
            return self._extract_bullet_points(section_text)
        return []
    
    def _extract_required_skills(self, text: str, requirements: List[str]) -> List[str]:
        """Extract required technical skills."""
        skills = set()
        
        # Combine text and requirements for comprehensive skill extraction
        combined_text = text.lower()
        if requirements:
            combined_text += ' ' + ' '.join(requirements).lower()
        
        # Extract programming languages
        for lang in self.programming_languages:
            if lang in combined_text:
                skills.add(lang.title())
        
        # Extract frameworks and libraries
        for framework in self.frameworks_libraries:
            if framework.lower() in combined_text:
                skills.add(framework)
        
        # Extract databases
        for db in self.databases:
            if db in combined_text:
                skills.add(db.upper() if len(db) <= 3 else db.title())
        
        # Extract cloud and tools
        for tool in self.cloud_tools:
            if tool.lower() in combined_text:
                skills.add(tool.upper() if tool.lower() in ['aws', 'gcp'] else tool.title())
        
        return list(skills)
    
    def _extract_preferred_skills(self, text: str, preferred_quals: List[str]) -> List[str]:
        """Extract preferred skills from preferred qualifications section."""
        if not preferred_quals:
            return []
        
        preferred_text = ' '.join(preferred_quals).lower()
        skills = set()
        
        # Use same logic as required skills but on preferred section
        for lang in self.programming_languages:
            if lang in preferred_text:
                skills.add(lang.title())
        
        for framework in self.frameworks_libraries:
            if framework.lower() in preferred_text:
                skills.add(framework)
        
        return list(skills)
    
    def _extract_experience_years(self, text: str) -> Optional[int]:
        """Extract required years of experience."""
        text_lower = text.lower()
        
        for pattern in self.experience_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                # Return the first number found (minimum experience)
                if isinstance(matches[0], tuple):
                    return int(matches[0][0]) if matches[0][0] else None
                else:
                    return int(matches[0])
        
        return None
    
    def _extract_education_requirements(self, text: str) -> List[str]:
        """Extract education requirements."""
        education_reqs = []
        text_lower = text.lower()
        
        for keyword in self.education_keywords:
            if keyword in text_lower:
                # Find sentences containing education keywords
                sentences = text.split('.')
                for sentence in sentences:
                    if keyword in sentence.lower() and len(sentence.strip()) > 10:
                        education_reqs.append(sentence.strip())
                        break
        
        return education_reqs
    
    def _is_remote_allowed(self, text: str) -> bool:
        """Determine if remote work is allowed."""
        remote_keywords = ['remote', 'work from home', 'wfh', 'distributed', 'telecommute']
        text_lower = text.lower()
        
        return any(keyword in text_lower for keyword in remote_keywords)
    
    def _determine_urgency(self, text: str) -> str:
        """Determine job urgency level."""
        text_lower = text.lower()
        
        urgent_keywords = ['urgent', 'immediate', 'asap', 'immediately', 'critical']
        high_keywords = ['fast-paced', 'quickly', 'soon', 'rapid']
        
        if any(keyword in text_lower for keyword in urgent_keywords):
            return 'high'
        elif any(keyword in text_lower for keyword in high_keywords):
            return 'medium'
        else:
            return 'low'
    
    def _extract_section(self, text: str, keywords: List[str], max_sentences: int = None) -> Optional[str]:
        """Extract a section based on keywords."""
        paragraphs = text.split('\n')
        section_start = None
        
        for i, paragraph in enumerate(paragraphs):
            if any(keyword.lower() in paragraph.lower() for keyword in keywords):
                section_start = i
                break
        
        if section_start is None:
            return None
        
        # Extract section content
        section_lines = []
        for i in range(section_start, len(paragraphs)):
            line = paragraphs[i].strip()
            
            # Stop at next major section
            if i > section_start and self._is_section_header(line):
                break
            
            if line:
                section_lines.append(line)
        
        section_text = ' '.join(section_lines)
        
        # Limit sentences if specified
        if max_sentences:
            sentences = section_text.split('.')
            section_text = '. '.join(sentences[:max_sentences])
        
        return section_text if section_text.strip() else None
    
    def _extract_bullet_points(self, text: str) -> List[str]:
        """Extract bullet points from text."""
        # Split by common bullet point markers
        bullet_markers = ['•', '*', '-', '◦', '▪', '▫']
        lines = text.split('\n')
        
        bullet_points = []
        for line in lines:
            line = line.strip()
            
            # Check for bullet markers
            for marker in bullet_markers:
                if line.startswith(marker):
                    clean_line = line[1:].strip()
                    if clean_line:
                        bullet_points.append(clean_line)
                    break
            else:
                # Check for numbered lists
                if re.match(r'^\d+\.?\s+', line):
                    clean_line = re.sub(r'^\d+\.?\s+', '', line).strip()
                    if clean_line:
                        bullet_points.append(clean_line)
                elif line and len(line.split()) > 3:  # Substantial content
                    bullet_points.append(line)
        
        return bullet_points
    
    def _is_section_header(self, line: str) -> bool:
        """Check if line is likely a section header."""
        if not line or len(line.split()) > 5:
            return False
        
        section_headers = [
            'requirements', 'qualifications', 'responsibilities', 'duties',
            'benefits', 'perks', 'about', 'overview', 'summary', 'skills',
            'experience', 'education', 'preferred', 'nice to have'
        ]
        
        line_lower = line.lower().strip()
        return any(header in line_lower for header in section_headers)
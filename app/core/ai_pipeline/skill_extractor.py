import re
import json
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
import spacy
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ExtractedSkill:
    """Represents an extracted skill with metadata."""
    name: str
    category: str
    confidence: float
    context: str  # Context where skill was found
    aliases: List[str] = None  # Alternative names
    proficiency_level: Optional[str] = None  # beginner, intermediate, advanced


@dataclass
class SkillProfile:
    """Complete skill profile for a candidate."""
    technical_skills: List[ExtractedSkill]
    soft_skills: List[ExtractedSkill]
    domain_expertise: List[ExtractedSkill]
    tools_platforms: List[ExtractedSkill]
    certifications: List[str]
    skill_categories: Dict[str, List[str]]
    total_skills_count: int
    skill_diversity_score: float


class AdvancedSkillExtractor:
    """Advanced skill extraction using multiple NLP techniques."""
    
    def __init__(self):
        self.nlp = None
        self.skill_embeddings = None
        self._load_models()
        self._load_skill_database()
    
    def _load_models(self):
        """Load NLP models."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy model successfully")
        except OSError:
            logger.warning("spaCy model not found. Some features will be limited.")
        
        try:
            # Use a lightweight sentence transformer
            self.skill_embeddings = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded sentence transformer model")
        except Exception as e:
            logger.warning(f"Could not load sentence transformer: {e}")
    
    def _load_skill_database(self):
        """Load comprehensive skill database with categories."""
        self.skill_database = {
            'programming_languages': {
                'python': ['python', 'py', 'python3'],
                'javascript': ['javascript', 'js', 'ecmascript', 'es6', 'es2015'],
                'java': ['java', 'jvm'],
                'typescript': ['typescript', 'ts'],
                'c++': ['c++', 'cpp', 'c plus plus'],
                'c#': ['c#', 'csharp', 'c sharp'],
                'php': ['php', 'php7', 'php8'],
                'ruby': ['ruby', 'rb'],
                'go': ['go', 'golang'],
                'rust': ['rust', 'rust-lang'],
                'kotlin': ['kotlin', 'kt'],
                'swift': ['swift', 'swift5'],
                'scala': ['scala'],
                'r': ['r programming', 'r language'],
                'matlab': ['matlab'],
                'perl': ['perl'],
                'bash': ['bash', 'shell scripting', 'bash scripting'],
                'powershell': ['powershell', 'ps1']
            },
            
            'web_technologies': {
                'react': ['react', 'reactjs', 'react.js'],
                'angular': ['angular', 'angularjs', 'angular2+'],
                'vue': ['vue', 'vue.js', 'vuejs'],
                'html': ['html', 'html5'],
                'css': ['css', 'css3', 'cascading style sheets'],
                'sass': ['sass', 'scss'],
                'less': ['less css'],
                'bootstrap': ['bootstrap', 'bootstrap4', 'bootstrap5'],
                'tailwind': ['tailwind', 'tailwindcss'],
                'jquery': ['jquery', 'jquery ui'],
                'node.js': ['node.js', 'nodejs', 'node js'],
                'express': ['express', 'express.js', 'expressjs'],
                'django': ['django', 'django rest framework'],
                'flask': ['flask', 'flask-restful'],
                'spring': ['spring', 'spring boot', 'spring framework'],
                'laravel': ['laravel', 'laravel framework'],
                'rails': ['ruby on rails', 'rails', 'ror']
            },
            
            'databases': {
                'mysql': ['mysql', 'my sql'],
                'postgresql': ['postgresql', 'postgres', 'psql'],
                'mongodb': ['mongodb', 'mongo'],
                'redis': ['redis'],
                'elasticsearch': ['elasticsearch', 'elastic search', 'elk stack'],
                'oracle': ['oracle database', 'oracle db'],
                'sqlite': ['sqlite', 'sqlite3'],
                'cassandra': ['cassandra', 'apache cassandra'],
                'dynamodb': ['dynamodb', 'dynamo db'],
                'neo4j': ['neo4j', 'graph database'],
                'influxdb': ['influxdb', 'time series database']
            },
            
            'cloud_platforms': {
                'aws': ['aws', 'amazon web services', 'ec2', 's3', 'lambda', 'rds'],
                'azure': ['azure', 'microsoft azure'],
                'gcp': ['gcp', 'google cloud platform', 'google cloud'],
                'kubernetes': ['kubernetes', 'k8s'],
                'docker': ['docker', 'containerization'],
                'terraform': ['terraform', 'infrastructure as code'],
                'ansible': ['ansible', 'configuration management'],
                'jenkins': ['jenkins', 'ci/cd'],
                'gitlab': ['gitlab', 'gitlab ci'],
                'circleci': ['circleci', 'circle ci']
            },
            
            'data_science': {
                'pandas': ['pandas', 'pd'],
                'numpy': ['numpy', 'np'],
                'scikit-learn': ['scikit-learn', 'sklearn', 'sci-kit learn'],
                'tensorflow': ['tensorflow', 'tf'],
                'pytorch': ['pytorch', 'torch'],
                'keras': ['keras'],
                'matplotlib': ['matplotlib', 'pyplot'],
                'seaborn': ['seaborn', 'sns'],
                'plotly': ['plotly', 'plotly dash'],
                'jupyter': ['jupyter', 'jupyter notebook', 'ipython'],
                'apache spark': ['spark', 'apache spark', 'pyspark'],
                'hadoop': ['hadoop', 'hdfs'],
                'tableau': ['tableau'],
                'power bi': ['power bi', 'powerbi'],
                'r shiny': ['shiny', 'r shiny']
            },
            
            'mobile_development': {
                'ios': ['ios development', 'ios', 'iphone development'],
                'android': ['android development', 'android'],
                'react native': ['react native', 'react-native'],
                'flutter': ['flutter', 'dart'],
                'xamarin': ['xamarin'],
                'cordova': ['cordova', 'phonegap'],
                'ionic': ['ionic framework', 'ionic']
            },
            
            'devops_tools': {
                'git': ['git', 'version control', 'github', 'gitlab'],
                'svn': ['svn', 'subversion'],
                'maven': ['maven', 'apache maven'],
                'gradle': ['gradle'],
                'webpack': ['webpack', 'module bundler'],
                'npm': ['npm', 'node package manager'],
                'yarn': ['yarn package manager', 'yarn'],
                'pip': ['pip', 'python package installer']
            },
            
            'soft_skills': {
                'leadership': ['leadership', 'team leadership', 'leading teams'],
                'communication': ['communication', 'public speaking', 'presentation'],
                'problem solving': ['problem solving', 'analytical thinking', 'troubleshooting'],
                'project management': ['project management', 'agile', 'scrum', 'kanban'],
                'teamwork': ['teamwork', 'collaboration', 'cross-functional teams'],
                'adaptability': ['adaptability', 'flexibility', 'learning agility'],
                'time management': ['time management', 'organization', 'prioritization'],
                'creativity': ['creativity', 'innovation', 'creative thinking'],
                'critical thinking': ['critical thinking', 'analysis', 'evaluation'],
                'mentoring': ['mentoring', 'coaching', 'training others']
            }
        }
        
        # Create reverse lookup for faster searching
        self.skill_lookup = {}
        for category, skills in self.skill_database.items():
            for skill, aliases in skills.items():
                self.skill_lookup[skill.lower()] = (skill, category)
                for alias in aliases:
                    self.skill_lookup[alias.lower()] = (skill, category)
    
    def extract_skills(self, text: str, context_type: str = "resume") -> SkillProfile:
        """Extract comprehensive skill profile from text."""
        logger.info(f"Extracting skills from {context_type}")
        
        # Clean and prepare text
        cleaned_text = self._preprocess_text(text)
        
        # Extract skills using multiple methods
        extracted_skills = []
        
        # Method 1: Dictionary-based exact matching
        dict_skills = self._extract_skills_dictionary(cleaned_text)
        extracted_skills.extend(dict_skills)
        
        # Method 2: Pattern-based extraction
        pattern_skills = self._extract_skills_patterns(cleaned_text)
        extracted_skills.extend(pattern_skills)
        
        # Method 3: NLP-based extraction (if spaCy is available)
        if self.nlp:
            nlp_skills = self._extract_skills_nlp(cleaned_text)
            extracted_skills.extend(nlp_skills)
        
        # Method 4: Context-aware extraction
        context_skills = self._extract_skills_contextual(cleaned_text)
        extracted_skills.extend(context_skills)
        
        # Deduplicate and categorize
        unique_skills = self._deduplicate_skills(extracted_skills)
        categorized_skills = self._categorize_skills(unique_skills)
        
        # Build skill profile
        return self._build_skill_profile(categorized_skills, text)
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for better skill extraction."""
        # Normalize common variations
        text = re.sub(r'(\w+)\.js', r'\1.js', text, flags=re.IGNORECASE)
        text = re.sub(r'(\w+)JS', r'\1.js', text)
        text = re.sub(r'HTML5', 'HTML', text, flags=re.IGNORECASE)
        text = re.sub(r'CSS3', 'CSS', text, flags=re.IGNORECASE)
        
        # Handle common separators
        text = re.sub(r'[,;|•▪▫◦]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _extract_skills_dictionary(self, text: str) -> List[ExtractedSkill]:
        """Extract skills using dictionary matching."""
        skills = []
        text_lower = text.lower()
        
        for skill_term, (canonical_name, category) in self.skill_lookup.items():
            if skill_term in text_lower:
                # Find context around the skill
                context = self._extract_context(text, skill_term)
                confidence = self._calculate_dictionary_confidence(skill_term, text_lower)
                
                skills.append(ExtractedSkill(
                    name=canonical_name,
                    category=category,
                    confidence=confidence,
                    context=context
                ))
        
        return skills
    
    def _extract_skills_patterns(self, text: str) -> List[ExtractedSkill]:
        """Extract skills using regex patterns."""
        skills = []
        
        # Programming language patterns
        prog_patterns = [
            r'\b(python|java|javascript|typescript|c\+\+|c#|php|ruby|go|rust)\b',
            r'\b(kotlin|swift|scala|matlab|perl|bash|powershell)\b'
        ]
        
        for pattern in prog_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                skill_name = match.group(1).lower()
                if skill_name in self.skill_lookup:
                    canonical_name, category = self.skill_lookup[skill_name]
                    context = self._extract_context(text, skill_name, match.start())
                    
                    skills.append(ExtractedSkill(
                        name=canonical_name,
                        category=category,
                        confidence=0.9,  # High confidence for pattern matches
                        context=context
                    ))
        
        # Framework patterns
        framework_patterns = [
            r'\b(react|angular|vue)(?:\.js)?\b',
            r'\b(django|flask|spring|express)(?:\s+(?:boot|framework))?\b',
            r'\b(tensorflow|pytorch|keras|scikit-learn)\b'
        ]
        
        for pattern in framework_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                skill_name = match.group(1).lower()
                if skill_name in self.skill_lookup:
                    canonical_name, category = self.skill_lookup[skill_name]
                    context = self._extract_context(text, skill_name, match.start())
                    
                    skills.append(ExtractedSkill(
                        name=canonical_name,
                        category=category,
                        confidence=0.85,
                        context=context
                    ))
        
        return skills
    
    def _extract_skills_nlp(self, text: str) -> List[ExtractedSkill]:
        """Extract skills using NLP techniques."""
        if not self.nlp:
            return []
        
        skills = []
        doc = self.nlp(text)
        
        # Extract noun phrases that might be skills
        for noun_phrase in doc.noun_chunks:
            phrase_text = noun_phrase.text.lower().strip()
            
            # Skip very short or very long phrases
            if len(phrase_text.split()) > 3 or len(phrase_text) < 3:
                continue
            
            # Check if phrase matches known skills
            if phrase_text in self.skill_lookup:
                canonical_name, category = self.skill_lookup[phrase_text]
                context = self._extract_context(text, phrase_text)
                
                skills.append(ExtractedSkill(
                    name=canonical_name,
                    category=category,
                    confidence=0.75,  # Lower confidence for NLP extraction
                    context=context
                ))
        
        # Extract named entities that might be technologies
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'PRODUCT']:
                ent_text = ent.text.lower().strip()
                if ent_text in self.skill_lookup:
                    canonical_name, category = self.skill_lookup[ent_text]
                    context = self._extract_context(text, ent_text)
                    
                    skills.append(ExtractedSkill(
                        name=canonical_name,
                        category=category,
                        confidence=0.70,
                        context=context
                    ))
        
        return skills
    
    def _extract_skills_contextual(self, text: str) -> List[ExtractedSkill]:
        """Extract skills based on context clues."""
        skills = []
        
        # Look for skill-indicating phrases
        skill_indicators = [
            r'(?:experience (?:with|in)|proficient (?:in|with)|skilled (?:in|with)|expertise (?:in|with))\s+([^,.\n]+)',
            r'(?:technologies:|skills:|tools:)\s*([^.\n]+)',
            r'(?:worked with|used|implemented|developed using)\s+([^,.\n]+)',
            r'(?:programming languages?|technologies?|frameworks?|tools?):\s*([^.\n]+)'
        ]
        
        for pattern in skill_indicators:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                skill_text = match.group(1).strip()
                
                # Split by common delimiters and check each part
                potential_skills = re.split(r'[,;|&]', skill_text)
                for potential_skill in potential_skills:
                    clean_skill = potential_skill.strip().lower()
                    
                    if clean_skill in self.skill_lookup:
                        canonical_name, category = self.skill_lookup[clean_skill]
                        context = skill_text
                        
                        skills.append(ExtractedSkill(
                            name=canonical_name,
                            category=category,
                            confidence=0.80,
                            context=context
                        ))
        
        return skills
    
    def _extract_context(self, text: str, skill: str, position: int = None) -> str:
        """Extract context around a skill mention."""
        if position is None:
            position = text.lower().find(skill.lower())
        
        if position == -1:
            return ""
        
        # Extract 50 characters before and after
        start = max(0, position - 50)
        end = min(len(text), position + len(skill) + 50)
        
        return text[start:end].strip()
    
    def _calculate_dictionary_confidence(self, skill_term: str, text: str) -> float:
        """Calculate confidence score for dictionary matches."""
        base_confidence = 0.8
        
        # Boost confidence if skill appears multiple times
        count = text.count(skill_term.lower())
        if count > 1:
            base_confidence += min(0.1 * (count - 1), 0.2)
        
        # Boost confidence if skill appears in typical skill sections
        skill_sections = ['skills', 'technologies', 'experience', 'projects']
        for section in skill_sections:
            if section in text and skill_term in text[text.find(section):text.find(section) + 200]:
                base_confidence += 0.1
                break
        
        return min(base_confidence, 1.0)
    
    def _deduplicate_skills(self, skills: List[ExtractedSkill]) -> List[ExtractedSkill]:
        """Remove duplicate skills, keeping the one with highest confidence."""
        skill_dict = {}
        
        for skill in skills:
            key = (skill.name.lower(), skill.category)
            if key not in skill_dict or skill.confidence > skill_dict[key].confidence:
                skill_dict[key] = skill
        
        return list(skill_dict.values())
    
    def _categorize_skills(self, skills: List[ExtractedSkill]) -> Dict[str, List[ExtractedSkill]]:
        """Categorize skills by type."""
        categorized = {
            'technical_skills': [],
            'soft_skills': [],
            'domain_expertise': [],
            'tools_platforms': []
        }
        
        for skill in skills:
            if skill.category == 'soft_skills':
                categorized['soft_skills'].append(skill)
            elif skill.category in ['cloud_platforms', 'devops_tools']:
                categorized['tools_platforms'].append(skill)
            elif skill.category in ['data_science', 'mobile_development']:
                categorized['domain_expertise'].append(skill)
            else:
                categorized['technical_skills'].append(skill)
        
        return categorized
    
    def _build_skill_profile(self, categorized_skills: Dict[str, List[ExtractedSkill]], original_text: str) -> SkillProfile:
        """Build comprehensive skill profile."""
        # Calculate skill categories distribution
        skill_categories = {}
        for category, skills in categorized_skills.items():
            skill_categories[category] = [skill.name for skill in skills]
        
        # Calculate diversity score
        total_categories = len([cat for cat, skills in skill_categories.items() if skills])
        max_categories = 4  # technical, soft, domain, tools
        diversity_score = min(total_categories / max_categories, 1.0)
        
        # Extract certifications (simple pattern matching)
        certifications = self._extract_certifications(original_text)
        
        return SkillProfile(
            technical_skills=categorized_skills['technical_skills'],
            soft_skills=categorized_skills['soft_skills'],
            domain_expertise=categorized_skills['domain_expertise'],
            tools_platforms=categorized_skills['tools_platforms'],
            certifications=certifications,
            skill_categories=skill_categories,
            total_skills_count=sum(len(skills) for skills in categorized_skills.values()),
            skill_diversity_score=diversity_score
        )
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications from text."""
        cert_patterns = [
            r'(AWS|Azure|Google Cloud|GCP)\s+(Certified|Certification)',
            r'(PMP|CISSP|CISM|CISA)\s*(Certified|Certification)?',
            r'(Scrum Master|Product Owner|Agile)\s*(Certified|Certification)',
            r'(Oracle|Microsoft|Cisco|CompTIA)\s+\w+\s*(Certified|Certification)'
        ]
        
        certifications = []
        for pattern in cert_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                certifications.append(match.group().strip())
        
        return certifications
from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Database
    database_url: str = "sqlite:///./resume_system.db"
    postgres_url: Optional[str] = None
    
    # Security
    secret_key: str = "your-super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # OpenAI & LangChain
    openai_api_key: str
    langsmith_api_key: Optional[str] = None
    langsmith_project: str = "resume-relevance-system"
    
    # AI Configuration
    embedding_model: str = "all-MiniLM-L6-v2"
    max_tokens: int = 4000
    temperature: float = 0.7
    
    # File Upload
    max_file_size: int = 10485760  # 10MB
    allowed_extensions: List[str] = ["pdf", "docx", "doc", "txt"]
    upload_directory: str = "./uploads"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Email
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    email_user: Optional[str] = None
    email_password: Optional[str] = None
    
    # Monitoring
    prometheus_port: int = 8001
    log_level: str = "INFO"
    
    # Development
    debug: bool = False
    reload: bool = False
    
    # Scoring Weights
    hard_match_weight: float = 0.4
    soft_match_weight: float = 0.6
    experience_weight: float = 0.3
    skills_weight: float = 0.4
    education_weight: float = 0.3
    
    # Thresholds
    high_threshold: float = 80.0
    medium_threshold: float = 60.0
    low_threshold: float = 40.0
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
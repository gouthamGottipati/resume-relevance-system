#!/usr/bin/env python3
"""
Database setup script for Resume Relevance Check System.
Run this to initialize the database with tables and sample data.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database.database import create_tables, drop_tables
from app.core.database.models import User, JobDescription, Resume
from app.core.database.database import SessionLocal
from app.core.utils.encryption import hash_password
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


def create_sample_users():
    """Create sample users for testing."""
    db = SessionLocal()
    
    try:
        # Check if users already exist
        existing_user = db.query(User).filter(User.username == "admin").first()
        if existing_user:
            logger.info("Sample users already exist, skipping creation")
            return
        
        # Create admin user
        admin_user = User(
            email="admin@resumeai.com",
            username="admin",
            hashed_password=hash_password("admin123"),
            full_name="System Administrator",
            role="admin",
            is_active=True
        )
        
        # Create recruiter user
        recruiter_user = User(
            email="recruiter@company.com",
            username="recruiter",
            hashed_password=hash_password("recruiter123"),
            full_name="Jane Recruiter",
            role="recruiter",
            is_active=True
        )
        
        # Create student user
        student_user = User(
            email="student@university.edu",
            username="student",
            hashed_password=hash_password("student123"),
            full_name="John Student",
            role="student",
            is_active=True
        )
        
        db.add_all([admin_user, recruiter_user, student_user])
        db.commit()
        
        logger.info("Sample users created successfully")
        logger.info("Login credentials:")
        logger.info("Admin: admin / admin123")
        logger.info("Recruiter: recruiter / recruiter123")
        logger.info("Student: student / student123")
        
    except Exception as e:
        logger.error(f"Error creating sample users: {e}")
        db.rollback()
    finally:
        db.close()


def process_sample_data():
    """Process sample data from the sample_data folder."""
    sample_data_path = project_root / "data" / "sample_data"
    
    if not sample_data_path.exists():
        logger.error("Sample data folder not found. Expected at: data/sample_data/")
        logger.info("Please ensure you have:")
        logger.info("- data/sample_data/resumes/ (with PDF files)")
        logger.info("- data/sample_data/JD/ (with PDF/text files)")
        return
    
    resume_folder = sample_data_path / "resumes"
    jd_folder = sample_data_path / "JD"
    
    logger.info(f"Sample data folders:")
    logger.info(f"Resumes: {resume_folder}")
    logger.info(f"Job Descriptions: {jd_folder}")
    
    # Count files
    if resume_folder.exists():
        resume_files = list(resume_folder.glob("*.pdf"))
        logger.info(f"Found {len(resume_files)} resume PDFs")
        
        for resume_file in resume_files[:5]:  # Show first 5
            logger.info(f"  - {resume_file.name}")
    
    if jd_folder.exists():
        jd_files = list(jd_folder.glob("*.pdf")) + list(jd_folder.glob("*.txt"))
        logger.info(f"Found {len(jd_files)} job description files")
        
        for jd_file in jd_files[:5]:  # Show first 5
            logger.info(f"  - {jd_file.name}")
    
    logger.info("Use the web interface or API to upload and process these files")


def main():
    """Main setup function."""
    print("🚀 Setting up Resume Relevance Check System Database...")
    
    try:
        # Create database tables
        logger.info("Creating database tables...")
        create_tables()
        logger.info("✅ Database tables created successfully")
        
        # Create sample users
        logger.info("Creating sample users...")
        create_sample_users()
        logger.info("✅ Sample users created successfully")
        
        # Process sample data information
        logger.info("Checking sample data...")
        process_sample_data()
        
        print("\n🎉 Database setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Start the FastAPI server: uvicorn app.main:app --reload")
        print("2. Start the Streamlit frontend: streamlit run frontend/streamlit_app/main.py")
        print("3. Login with sample credentials and upload files from data/sample_data/")
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
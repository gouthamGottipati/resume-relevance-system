#!/usr/bin/env python3
"""
Script to populate database with sample job descriptions.
This creates some sample JDs that can be used immediately.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database.database import SessionLocal
from app.core.database.models import JobDescription, User
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


def create_sample_job_descriptions():
    """Create sample job descriptions in database."""
    db = SessionLocal()
    
    try:
        # Get a user to assign as creator
        user = db.query(User).filter(User.role == "recruiter").first()
        if not user:
            logger.error("No recruiter user found. Run setup_database.py first.")
            return
        
        sample_jobs = [
            {
                "title": "Senior Python Developer",
                "company": "TechCorp Inc.",
                "location": "San Francisco, CA",
                "department": "Engineering",
                "experience_required": "5+ years",
                "job_type": "full-time",
                "raw_content": """
We are seeking a Senior Python Developer to join our dynamic engineering team. 

RESPONSIBILITIES:
• Design and develop scalable web applications using Python and Django
• Collaborate with cross-functional teams to deliver high-quality software
• Mentor junior developers and provide technical leadership
• Implement best practices for code quality, testing, and deployment
• Work with cloud platforms (AWS, Azure) for application deployment

REQUIRED SKILLS:
• 5+ years of Python development experience
• Strong knowledge of Django, Flask, or FastAPI
• Experience with PostgreSQL, MongoDB, or Redis
• Proficiency in JavaScript, HTML, CSS
• Knowledge of containerization (Docker, Kubernetes)
• Experience with version control (Git)
• Understanding of CI/CD pipelines

PREFERRED QUALIFICATIONS:
• Master's degree in Computer Science or related field
• AWS/Azure cloud certifications
• Experience with microservices architecture
• Knowledge of machine learning libraries (scikit-learn, pandas)
• Agile/Scrum methodology experience

BENEFITS:
• Competitive salary and equity package
• Health, dental, and vision insurance
• Flexible work arrangements
• Professional development opportunities
• 401(k) with company matching
                """,
                "required_skills": ["Python", "Django", "PostgreSQL", "JavaScript", "Docker", "Git", "AWS"],
                "preferred_skills": ["Machine Learning", "Microservices", "Kubernetes", "Redis"],
                "required_experience_years": 5,
                "education_requirements": ["Bachelor's degree in Computer Science or related field"],
                "remote_allowed": True,
                "urgency_level": "high",
                "status": "active"
            },
            {
                "title": "Data Scientist",
                "company": "DataTech Solutions",
                "location": "New York, NY",
                "department": "Data Science",
                "experience_required": "3+ years",
                "job_type": "full-time",
                "raw_content": """
Join our Data Science team to build innovative ML solutions and drive data-driven decision making.

RESPONSIBILITIES:
• Develop and deploy machine learning models for business applications
• Analyze large datasets to extract actionable insights
• Collaborate with product teams to integrate ML solutions
• Create data visualizations and reports for stakeholders
• Stay current with latest ML techniques and tools

REQUIRED SKILLS:
• 3+ years of data science experience
• Proficiency in Python, R, or Scala
• Strong knowledge of ML libraries (scikit-learn, TensorFlow, PyTorch)
• Experience with SQL and data manipulation (pandas, numpy)
• Statistical analysis and hypothesis testing
• Data visualization tools (matplotlib, seaborn, Plotly)

PREFERRED QUALIFICATIONS:
• PhD in Data Science, Statistics, or related field
• Experience with big data tools (Spark, Hadoop)
• Cloud platform experience (AWS SageMaker, Google Cloud ML)
• Deep learning and neural networks experience
• A/B testing and experimental design

BENEFITS:
• Competitive compensation package
• Comprehensive health benefits
• Flexible PTO policy
• Learning and development budget
• Stock options
                """,
                "required_skills": ["Python", "Machine Learning", "SQL", "Statistics", "TensorFlow", "pandas", "scikit-learn"],
                "preferred_skills": ["Deep Learning", "Spark", "AWS", "A/B Testing", "R"],
                "required_experience_years": 3,
                "education_requirements": ["Master's degree in Data Science, Statistics, or related field"],
                "remote_allowed": True,
                "urgency_level": "medium",
                "status": "active"
            },
            {
                "title": "Frontend React Developer",
                "company": "WebTech Innovations",
                "location": "Austin, TX",
                "department": "Engineering",
                "experience_required": "2+ years",
                "job_type": "full-time",
                "raw_content": """
We're looking for a talented Frontend Developer to create amazing user experiences with React.

RESPONSIBILITIES:
• Develop responsive web applications using React and TypeScript
• Collaborate with UX/UI designers to implement pixel-perfect designs
• Optimize applications for maximum speed and scalability
• Write clean, maintainable, and testable code
• Participate in code reviews and technical discussions

REQUIRED SKILLS:
• 2+ years of React development experience
• Strong proficiency in JavaScript ES6+ and TypeScript
• Experience with modern CSS (Grid, Flexbox, SASS/SCSS)
• Knowledge of state management (Redux, Context API)
• Familiarity with testing frameworks (Jest, React Testing Library)
• Version control with Git

PREFERRED QUALIFICATIONS:
• Experience with Next.js or Gatsby
• Knowledge of GraphQL and Apollo Client
• Familiarity with design systems and component libraries
• Understanding of web performance optimization
• Experience with CI/CD workflows

BENEFITS:
• Competitive salary
• Health and wellness benefits
• Remote work options
• Professional growth opportunities
• Team building events
                """,
                "required_skills": ["React", "JavaScript", "TypeScript", "CSS", "HTML", "Git"],
                "preferred_skills": ["Next.js", "GraphQL", "Redux", "Jest", "SASS"],
                "required_experience_years": 2,
                "education_requirements": ["Bachelor's degree preferred"],
                "remote_allowed": True,
                "urgency_level": "medium",
                "status": "active"
            }
        ]
        
        # Check if sample jobs already exist
        existing_job = db.query(JobDescription).filter(JobDescription.title.contains("Senior Python Developer")).first()
        if existing_job:
            logger.info("Sample job descriptions already exist, skipping creation")
            return
        
        # Create job descriptions
        for job_data in sample_jobs:
            job = JobDescription(
                title=job_data["title"],
                company=job_data["company"],
                location=job_data["location"],
                department=job_data["department"],
                experience_required=job_data["experience_required"],
                job_type=job_data["job_type"],
                raw_content=job_data["raw_content"],
                required_skills=job_data["required_skills"],
                preferred_skills=job_data["preferred_skills"],
                required_experience_years=job_data["required_experience_years"],
                education_requirements=job_data["education_requirements"],
                remote_allowed=job_data["remote_allowed"],
                urgency_level=job_data["urgency_level"],
                status=job_data["status"],
                created_by=user.id
            )
            db.add(job)
        
        db.commit()
        logger.info(f"✅ Created {len(sample_jobs)} sample job descriptions")
        
        # Print summary
        for job in sample_jobs:
            logger.info(f"  - {job['title']} at {job['company']}")
        
    except Exception as e:
        logger.error(f"Error creating sample job descriptions: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """Main function."""
    print("📋 Creating sample job descriptions...")
    create_sample_job_descriptions()
    print("✅ Sample job descriptions created successfully!")
    print("You can now use these jobs for testing resume evaluations.")


if __name__ == "__main__":
    main()
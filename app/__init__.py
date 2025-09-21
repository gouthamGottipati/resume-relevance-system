"""
Resume Relevance Check System

An AI-powered system for automated resume evaluation and matching
against job descriptions with advanced analytics and insights.
"""

__version__ = "1.0.0"
__author__ = "Resume AI Team"
__description__ = "Hackathon-winning Resume Relevance Check System"


# ===== setup.py =====
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="resume-relevance-system",
    version="1.0.0",
    author="Resume AI Team",
    author_email="team@resumeai.com",
    description="AI-powered resume relevance checking system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/resume-relevance-system",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0",
        "langchain>=0.1.0",
        "streamlit>=1.28.2",
        "sqlalchemy>=2.0.23",
        "sentence-transformers>=2.2.2",
        "PyMuPDF>=1.23.8",
        "python-docx>=1.1.0",
        "plotly>=5.17.0",
        "pandas>=2.1.3",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "black>=23.11.0",
            "isort>=5.12.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
        ],
        "production": [
            "psycopg2-binary>=2.9.9",
            "redis>=5.0.1",
            "celery>=5.3.4",
        ],
    },
)
#!/usr/bin/env python3
"""
Script to run the complete test suite.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Run the complete test suite."""
    print("🧪 Running Resume AI Test Suite...")
    
    # Change to project directory
    project_root = Path(__file__).parent.parent
    
    try:
        # Run pytest with coverage
        cmd = [
            "python", "-m", "pytest",
            "tests/",
            "-v",
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=70"
        ]
        
        result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ All tests passed!")
            print("📊 Coverage report generated in htmlcov/index.html")
        else:
            print("❌ Some tests failed!")
            sys.exit(1)
            
    except FileNotFoundError:
        print("❌ pytest not found. Install with: pip install pytest pytest-cov")
        sys.exit(1)


if __name__ == "__main__":
    main()# ===== tests/conftest.py =====
import pytest
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.core.database.database import get_database
from app.core.database.models import Base
from app.config import settings


@pytest.fixture(scope="session")
def test_db():
    """Create test database."""
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp()
    test_db_url = f"sqlite:///{db_path}"
    
    # Create test engine
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    yield TestingSessionLocal
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def db_session(test_db):
    """Get database session for testing."""
    session = test_db()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db_session):
    """Get test client."""
    def override_get_database():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_database] = override_get_database
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Get authentication headers."""
    # Create test user
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPassword123",
        "full_name": "Test User",
        "role": "recruiter"
    }
    
    # Register user
    client.post("/api/v1/auth/register", json=user_data)
    
    # Login
    login_data = {
        "email_or_username": "testuser",
        "password": "TestPassword123"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}

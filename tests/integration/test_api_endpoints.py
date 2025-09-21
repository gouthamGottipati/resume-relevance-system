import pytest
from fastapi.testclient import TestClient
import json


class TestAPIEndpoints:
    """Test API endpoints integration."""
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()
        assert response.json()["status"] == "healthy"
    
    def test_user_registration_and_login(self, client):
        """Test user registration and login flow."""
        # Register user
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "TestPassword123",
            "full_name": "Test User",
            "role": "recruiter"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 200
        assert "id" in response.json()
        
        # Login
        login_data = {
            "email_or_username": "testuser",
            "password": "TestPassword123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert "token_type" in response.json()
    
    def test_protected_endpoint_without_auth(self, client):
        """Test accessing protected endpoint without authentication."""
        response = client.get("/api/v1/resumes/")
        assert response.status_code == 401
    
    def test_job_description_crud(self, client, auth_headers):
        """Test job description CRUD operations."""
        # Create job description
        job_data = {
            "title": "Senior Python Developer",
            "company": "Tech Corp",
            "location": "San Francisco, CA",
            "job_type": "full-time",
            "raw_content": """
            We are looking for a Senior Python Developer with 5+ years of experience.
            
            Required Skills:
            - Python, Django, Flask
            - PostgreSQL, Redis
            - AWS, Docker, Kubernetes
            - Git, CI/CD
            
            Responsibilities:
            - Design and develop scalable web applications
            - Lead technical architecture decisions
            - Mentor junior developers
            - Collaborate with product teams
            
            Requirements:
            - Bachelor's degree in Computer Science
            - 5+ years Python development experience
            - Strong knowledge of web frameworks
            - Experience with cloud platforms
            """,
            "remote_allowed": True,
            "urgency_level": "high"
        }
        
        response = client.post("/api/v1/jobs/", json=job_data, headers=auth_headers)
        assert response.status_code == 200
        job_id = response.json()["id"]
        
        # Get job description
        response = client.get(f"/api/v1/jobs/{job_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["title"] == "Senior Python Developer"
        
        # List job descriptions
        response = client.get("/api/v1/jobs/", headers=auth_headers)
        assert response.status_code == 200
        assert "jobs" in response.json()
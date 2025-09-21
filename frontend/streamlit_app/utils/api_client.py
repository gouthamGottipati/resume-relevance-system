import requests
import streamlit as st
from typing import Dict, List, Any, Optional, Union
import json


class APIClient:
    """Client for communicating with the FastAPI backend."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        # Set auth token if available
        if hasattr(st.session_state, 'auth_token'):
            self.session.headers.update({
                'Authorization': f'Bearer {st.session_state.auth_token}'
            })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make HTTP request to the API."""
        url = f"{self.base_url}/api/v1{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {str(e)}")
            return None
        except json.JSONDecodeError:
            st.error("Invalid JSON response from API")
            return None
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make GET request."""
        return self._make_request('GET', endpoint, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict] = None, json_data: Optional[Dict] = None, files: Optional[Dict] = None) -> Optional[Dict]:
        """Make POST request."""
        kwargs = {}
        if data:
            kwargs['data'] = data
        if json_data:
            kwargs['json'] = json_data
        if files:
            kwargs['files'] = files
        
        return self._make_request('POST', endpoint, **kwargs)
    
    def put(self, endpoint: str, json_data: Optional[Dict] = None) -> Optional[Dict]:
        """Make PUT request."""
        return self._make_request('PUT', endpoint, json=json_data)
    
    def delete(self, endpoint: str) -> Optional[Dict]:
        """Make DELETE request."""
        return self._make_request('DELETE', endpoint)
    
    # Authentication methods
    def login(self, email_or_username: str, password: str) -> tuple[bool, Optional[Dict]]:
        """Login user."""
        data = {
            'email_or_username': email_or_username,
            'password': password
        }
        
        response = self.post('/auth/login', json_data=data)
        if response and 'access_token' in response:
            # Store token
            st.session_state.auth_token = response['access_token']
            self.session.headers.update({
                'Authorization': f'Bearer {response["access_token"]}'
            })
            
            # Get user info
            user_info = self.get('/auth/me')
            return True, user_info
        
        return False, None
    
    def register(self, email: str, username: str, full_name: str, password: str, role: str = 'recruiter') -> tuple[bool, str]:
        """Register new user."""
        data = {
            'email': email,
            'username': username,
            'full_name': full_name,
            'password': password,
            'role': role
        }
        
        response = self.post('/auth/register', json_data=data)
        if response:
            return True, "Registration successful"
        else:
            return False, "Registration failed"
    
    # Resume methods
    def upload_resume(self, file, candidate_name: str = None, candidate_email: str = None) -> bool:
        """Upload resume file."""
        files = {'file': (file.name, file.getvalue(), file.type)}
        data = {}
        
        if candidate_name:
            data['candidate_name'] = candidate_name
        if candidate_email:
            data['candidate_email'] = candidate_email
        
        response = self.post('/resumes/upload', files=files, data=data)
        return response is not None
    
    def get_resumes(self, name_filter: str = None, skills_filter: str = None, experience_min: float = None) -> List[Dict]:
        """Get list of resumes."""
        params = {}
        if name_filter:
            params['candidate_name'] = name_filter
        if skills_filter:
            params['skills'] = skills_filter
        if experience_min:
            params['experience_min'] = experience_min
        
        response = self.get('/resumes/', params=params)
        return response.get('resumes', []) if response else []
    
    def get_resume(self, resume_id: int) -> Optional[Dict]:
        """Get specific resume."""
        return self.get(f'/resumes/{resume_id}')
    
    # Job methods
    def create_job_description(self, job_data: Dict) -> bool:
        """Create new job description."""
        response = self.post('/jobs/', json_data=job_data)
        return response is not None
    
    def get_job_descriptions(self, title_filter: str = None, company_filter: str = None, location_filter: str = None, my_jobs: bool = False) -> List[Dict]:
        """Get list of job descriptions."""
        params = {}
        if title_filter:
            params['title'] = title_filter
        if company_filter:
            params['company'] = company_filter
        if location_filter:
            params['location'] = location_filter
        if my_jobs:
            params['my_jobs'] = True
        
        response = self.get('/jobs/', params=params)
        return response.get('jobs', []) if response else []
    
    def get_job_description(self, job_id: int) -> Optional[Dict]:
        """Get specific job description."""
        return self.get(f'/jobs/{job_id}')
    
    # Matching methods
    def evaluate_resume(self, resume_id: int, job_id: int, custom_weights: Optional[Dict] = None) -> Optional[Dict]:
        """Evaluate resume against job."""
        data = {
            'resume_id': resume_id,
            'job_id': job_id
        }
        if custom_weights:
            data['custom_weights'] = custom_weights
        
        return self.post('/matching/evaluate', json_data=data)
    
    def batch_evaluate_resumes(self, resume_ids: List[int], job_id: int) -> Optional[Dict]:
        """Batch evaluate resumes."""
        data = {
            'resume_ids': resume_ids,
            'job_id': job_id
        }
        
        return self.post('/matching/batch-evaluate', json_data=data)

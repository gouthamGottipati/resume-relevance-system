import streamlit as st
from typing import Optional, Tuple
from .api_client import APIClient


class AuthManager:
    """Handle authentication state and operations."""
    
    def __init__(self):
        self.api_client = APIClient()
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return st.session_state.get('auth_token') is not None and st.session_state.get('user') is not None
    
    def login(self, email_or_username: str, password: str) -> Tuple[bool, Optional[dict]]:
        """Login user."""
        success, user_data = self.api_client.login(email_or_username, password)
        
        if success:
            st.session_state.user = user_data
            return True, user_data
        
        return False, None
    
    def register(self, email: str, username: str, full_name: str, password: str, role: str) -> Tuple[bool, str]:
        """Register new user."""
        return self.api_client.register(email, username, full_name, password, role)
    
    def logout(self):
        """Logout user."""
        # Clear session state
        if 'auth_token' in st.session_state:
            del st.session_state.auth_token
        if 'user' in st.session_state:
            del st.session_state.user
        if 'current_page' in st.session_state:
            del st.session_state.current_page
        
        st.success("Logged out successfully!")
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any
import base64
from pathlib import Path

# Set page config FIRST
st.set_page_config(
    page_title="Resume AI - Intelligent Resume Evaluation System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/resume-ai',
        'Report a bug': 'https://github.com/your-repo/resume-ai/issues',
        'About': """
        # Resume AI System v1.0
        
        **The world's most advanced resume evaluation platform**
        
        Built with cutting-edge AI technology to revolutionize recruitment.
        
        Features:
        - AI-powered resume parsing
        - Semantic skill matching
        - Personalized candidate feedback
        - Advanced analytics dashboard
        - Peer benchmarking system
        """
    }
)

from utils.api_client import APIClient
from utils.auth import AuthManager
from components.charts import ChartComponents
from components.cards import CardComponents
from components.tables import TableComponents

# Initialize components
api_client = APIClient()
auth_manager = AuthManager()
charts = ChartComponents()
cards = CardComponents()
tables = TableComponents()

# Custom CSS for stunning UI
def load_css():
    """Load custom CSS for amazing UI."""
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    /* Header Styles */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-weight: 700;
        font-size: 2.5rem;
    }
    
    .main-header p {
        color: rgba(255,255,255,0.9);
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
    }
    
    /* Card Styles */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.15);
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #2c3e50;
        margin: 0;
    }
    
    .metric-label {
        color: #7f8c8d;
        font-size: 0.9rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin: 0;
    }
    
    .metric-delta {
        font-size: 0.8rem;
        font-weight: 500;
        margin-top: 0.5rem;
    }
    
    .metric-delta.positive {
        color: #27ae60;
    }
    
    .metric-delta.negative {
        color: #e74c3c;
    }
    
    /* Status Badge Styles */
    .status-high {
        background: linear-gradient(135deg, #27ae60, #2ecc71);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        text-align: center;
        display: inline-block;
    }
    
    .status-medium {
        background: linear-gradient(135deg, #f39c12, #e67e22);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        text-align: center;
        display: inline-block;
    }
    
    .status-low {
        background: linear-gradient(135deg, #e74c3c, #c0392b);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        text-align: center;
        display: inline-block;
    }
    
    /* Progress Bar Styles */
    .progress-container {
        background: #ecf0f1;
        border-radius: 10px;
        overflow: hidden;
        margin: 0.5rem 0;
    }
    
    .progress-bar {
        height: 8px;
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-radius: 10px;
        transition: width 0.3s ease;
    }
    
    /* Sidebar Styles */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Button Styles */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* File Uploader Styles */
    .uploadedFile {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background: rgba(102, 126, 234, 0.05);
    }
    
    /* Skill Tag Styles */
    .skill-tag {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 0.2rem 0.6rem;
        margin: 0.1rem;
        border-radius: 15px;
        font-size: 0.8rem;
        display: inline-block;
    }
    
    /* Animation Classes */
    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .slide-in-up {
        animation: slideInUp 0.5s ease-out;
    }
    
    /* Data Table Styles */
    .dataframe {
        font-size: 0.9rem;
    }
    
    .dataframe th {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        font-weight: 600;
    }
    
    .dataframe tr:nth-child(even) {
        background: rgba(102, 126, 234, 0.05);
    }
    
    /* Tooltip Styles */
    .tooltip {
        position: relative;
        display: inline-block;
        border-bottom: 1px dotted #667eea;
        cursor: help;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        background-color: #2c3e50;
        color: white;
        text-align: center;
        border-radius: 6px;
        padding: 5px 10px;
        position: absolute;
        z-index: 1;
        bottom: 150%;
        left: 50%;
        margin-left: -60px;
        font-size: 0.8rem;
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
    }
    </style>
    """, unsafe_allow_html=True)

def render_header():
    """Render the main header."""
    st.markdown("""
    <div class="main-header">
        <h1>🧠 Resume AI Dashboard</h1>
        <p>Intelligent Resume Evaluation System - Transforming recruitment with AI</p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render the enhanced sidebar."""
    with st.sidebar:
        st.image("static/images/logo.png", width=120) if Path("static/images/logo.png").exists() else st.markdown("# 🧠 Resume AI")
        
        # User info
        if st.session_state.get('user'):
            user = st.session_state.user
            st.success(f"Welcome, {user.get('full_name', user.get('username', 'User'))}")
            st.write(f"**Role:** {user.get('role', 'Unknown').title()}")
            
            if st.button("🚪 Logout", key="logout"):
                auth_manager.logout()
                st.rerun()
        
        st.markdown("---")
        
        # Navigation
        st.markdown("### 📊 Navigation")
        
        pages = {
            "🏠 Dashboard": "dashboard",
            "📄 Resume Management": "resumes",
            "💼 Job Descriptions": "jobs", 
            "🔍 Matching Engine": "matching",
            "📈 Analytics": "analytics",
            "🎯 Benchmarking": "benchmarking",
            "⚙️ Settings": "settings"
        }
        
        for page_name, page_key in pages.items():
            if st.button(page_name, key=f"nav_{page_key}", use_container_width=True):
                st.session_state.current_page = page_key
                st.rerun()
        
        st.markdown("---")
        
        # Quick stats
        st.markdown("### 📊 Quick Stats")
        try:
            stats = api_client.get("/analytics/dashboard?days=7")
            if stats:
                st.metric("This Week", f"{stats.get('total_evaluations', 0)} evaluations")
                st.metric("Avg Score", f"{stats.get('average_score', 0):.1f}/100")
        except:
            st.info("Connect to see quick stats")

def main():
    """Main application logic."""
    load_css()
    
    # Initialize session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'dashboard'
    
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    # Check authentication
    if not auth_manager.is_authenticated():
        render_login_page()
        return
    
    # Render sidebar
    render_sidebar()
    
    # Render header
    render_header()
    
    # Route to appropriate page
    current_page = st.session_state.get('current_page', 'dashboard')
    
    if current_page == 'dashboard':
        render_dashboard_page()
    elif current_page == 'resumes':
        render_resumes_page()
    elif current_page == 'jobs':
        render_jobs_page()
    elif current_page == 'matching':
        render_matching_page()
    elif current_page == 'analytics':
        render_analytics_page()
    elif current_page == 'benchmarking':
        render_benchmarking_page()
    elif current_page == 'settings':
        render_settings_page()

def render_login_page():
    """Render the login page."""
    st.markdown("""
    <div class="main-header">
        <h1>🧠 Resume AI System</h1>
        <p>Please log in to access the intelligent resume evaluation platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.container():
            st.markdown("### 🔐 Login")
            
            with st.form("login_form"):
                email_or_username = st.text_input("Email or Username", placeholder="Enter your email or username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                
                col_login, col_register = st.columns(2)
                
                with col_login:
                    login_clicked = st.form_submit_button("🚀 Login", use_container_width=True)
                
                with col_register:
                    register_clicked = st.form_submit_button("✨ Register", use_container_width=True, type="secondary")
                
                if login_clicked:
                    if email_or_username and password:
                        success, user_data = auth_manager.login(email_or_username, password)
                        if success:
                            st.session_state.user = user_data
                            st.success("🎉 Login successful!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid credentials")
                    else:
                        st.warning("⚠️ Please fill in all fields")
                
                if register_clicked:
                    st.session_state.show_register = True
                    st.rerun()
        
        # Registration form
        if st.session_state.get('show_register', False):
            st.markdown("---")
            st.markdown("### ✨ Create New Account")
            
            with st.form("register_form"):
                reg_email = st.text_input("Email", placeholder="your.email@company.com")
                reg_username = st.text_input("Username", placeholder="Choose a username")
                reg_full_name = st.text_input("Full Name", placeholder="Your full name")
                reg_password = st.text_input("Password", type="password", placeholder="Choose a strong password")
                reg_role = st.selectbox("Role", ["recruiter", "admin", "student"])
                
                register_submit = st.form_submit_button("🎯 Create Account", use_container_width=True)
                
                if register_submit:
                    if all([reg_email, reg_username, reg_full_name, reg_password]):
                        success, message = auth_manager.register(
                            email=reg_email,
                            username=reg_username,
                            full_name=reg_full_name,
                            password=reg_password,
                            role=reg_role
                        )
                        if success:
                            st.success("🎉 Account created successfully! Please login.")
                            st.session_state.show_register = False
                            st.rerun()
                        else:
                            st.error(f"❌ Registration failed: {message}")
                    else:
                        st.warning("⚠️ Please fill in all fields")

def render_dashboard_page():
    """Render the main dashboard."""
    st.markdown("## 🏠 Executive Dashboard")
    
    # Load dashboard data
    try:
        dashboard_data = api_client.get("/analytics/dashboard?days=30")
        
        # Key Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cards.metric_card(
                "Total Resumes", 
                dashboard_data.get('total_resumes', 0),
                delta="+12% vs last month",
                color="#667eea"
            )
        
        with col2:
            cards.metric_card(
                "Active Jobs", 
                dashboard_data.get('total_jobs', 0),
                delta="+5% vs last month",
                color="#27ae60"
            )
        
        with col3:
            cards.metric_card(
                "Evaluations", 
                dashboard_data.get('total_evaluations', 0),
                delta="+23% vs last month",
                color="#f39c12"
            )
        
        with col4:
            cards.metric_card(
                "Avg Score", 
                f"{dashboard_data.get('average_score', 0):.1f}/100",
                delta="+2.3 points",
                color="#e74c3c"
            )
        
        # Charts Row
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎯 Suitability Distribution")
            suitability_data = dashboard_data.get('suitability_distribution', {})
            charts.suitability_pie_chart(suitability_data)
        
        with col2:
            st.markdown("### 📈 Skills in Demand")
            skills_data = dashboard_data.get('top_skills_in_demand', [])
            charts.skills_bar_chart(skills_data)
        
        # Recent Activity
        st.markdown("### ⚡ Recent Evaluations")
        recent_evaluations = dashboard_data.get('recent_evaluations', [])
        if recent_evaluations:
            tables.recent_evaluations_table(recent_evaluations)
        else:
            st.info("No recent evaluations found.")
            
    except Exception as e:
        st.error(f"❌ Error loading dashboard data: {str(e)}")
        st.info("Make sure the API server is running on http://localhost:8000")

def render_resumes_page():
    """Render the resume management page."""
    st.markdown("## 📄 Resume Management")
    
    # Resume Upload Section
    with st.expander("📤 Upload New Resume", expanded=True):
        uploaded_file = st.file_uploader(
            "Choose a resume file",
            type=['pdf', 'docx', 'doc'],
            help="Upload PDF or Word documents"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            candidate_name = st.text_input("Candidate Name (Optional)")
        with col2:
            candidate_email = st.text_input("Candidate Email (Optional)")
        
        if uploaded_file and st.button("🚀 Process Resume"):
            with st.spinner("Processing resume..."):
                try:
                    success = api_client.upload_resume(
                        uploaded_file, 
                        candidate_name, 
                        candidate_email
                    )
                    if success:
                        st.success("✅ Resume processed successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to process resume")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # Resume List
    st.markdown("### 📋 Resume Database")
    
    # Filters
    with st.expander("🔍 Filters"):
        col1, col2, col3 = st.columns(3)
        with col1:
            name_filter = st.text_input("Candidate Name")
        with col2:
            skills_filter = st.text_input("Skills")
        with col3:
            exp_filter = st.slider("Min Experience (years)", 0, 20, 0)
    
    # Load and display resumes
    try:
        resumes = api_client.get_resumes(
            name_filter=name_filter,
            skills_filter=skills_filter,
            experience_min=exp_filter if exp_filter > 0 else None
        )
        
        if resumes:
            tables.resumes_table(resumes)
        else:
            st.info("No resumes found matching your criteria.")
            
    except Exception as e:
        st.error(f"❌ Error loading resumes: {str(e)}")

def render_jobs_page():
    """Render the job descriptions page."""
    st.markdown("## 💼 Job Descriptions")
    
    # Create New Job Section
    with st.expander("➕ Create New Job Description", expanded=False):
        with st.form("new_job_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                job_title = st.text_input("Job Title*")
                company = st.text_input("Company*")
                location = st.text_input("Location")
                
            with col2:
                department = st.text_input("Department")
                experience_required = st.text_input("Experience Required")
                job_type = st.selectbox("Job Type", 
                    ["full-time", "part-time", "contract", "internship", "freelance"])
            
            raw_content = st.text_area(
                "Job Description*", 
                height=300,
                help="Paste the complete job description here"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                remote_allowed = st.checkbox("Remote Work Allowed")
            with col2:
                urgency_level = st.selectbox("Urgency Level", ["low", "medium", "high"])
            
            if st.form_submit_button("🎯 Create Job Description"):
                if job_title and company and raw_content:
                    try:
                        success = api_client.create_job_description({
                            "title": job_title,
                            "company": company,
                            "location": location,
                            "department": department,
                            "experience_required": experience_required,
                            "job_type": job_type,
                            "raw_content": raw_content,
                            "remote_allowed": remote_allowed,
                            "urgency_level": urgency_level
                        })
                        
                        if success:
                            st.success("✅ Job description created successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to create job description")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                else:
                    st.warning("⚠️ Please fill in all required fields")
    
    # Job Descriptions List
    st.markdown("### 📋 Job Descriptions Database")
    
    # Filters
    with st.expander("🔍 Filters"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            title_filter = st.text_input("Job Title")
        with col2:
            company_filter = st.text_input("Company")
        with col3:
            location_filter = st.text_input("Location")
        with col4:
            my_jobs_only = st.checkbox("My Jobs Only")
    
    try:
        jobs = api_client.get_job_descriptions(
            title_filter=title_filter,
            company_filter=company_filter,
            location_filter=location_filter,
            my_jobs=my_jobs_only
        )
        
        if jobs:
            tables.jobs_table(jobs)
        else:
            st.info("No job descriptions found matching your criteria.")
            
    except Exception as e:
        st.error(f"❌ Error loading job descriptions: {str(e)}")

def render_matching_page():
    """Render the matching engine page."""
    st.markdown("## 🔍 AI Matching Engine")
    
    # Single Evaluation
    with st.expander("🎯 Single Resume Evaluation", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Select Resume**")
            try:
                resumes = api_client.get_resumes()
                resume_options = {f"{r['candidate_name']} - {r['filename']}": r['id'] for r in resumes}
                selected_resume = st.selectbox("Choose Resume", options=list(resume_options.keys()))
                resume_id = resume_options.get(selected_resume) if selected_resume else None
            except:
                st.error("Failed to load resumes")
                resume_id = None
        
        with col2:
            st.markdown("**Select Job Description**")
            try:
                jobs = api_client.get_job_descriptions()
                job_options = {f"{j['title']} at {j['company']}": j['id'] for j in jobs}
                selected_job = st.selectbox("Choose Job", options=list(job_options.keys()))
                job_id = job_options.get(selected_job) if selected_job else None
            except:
                st.error("Failed to load job descriptions")
                job_id = None
        
        # Custom weights
        st.markdown("**Custom Scoring Weights (Optional)**")
        use_custom_weights = st.checkbox("Use Custom Weights")
        
        custom_weights = None
        if use_custom_weights:
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                hard_skills = st.slider("Hard Skills", 0.0, 1.0, 0.35, 0.05)
            with col2:
                soft_skills = st.slider("Soft Skills", 0.0, 1.0, 0.15, 0.05)
            with col3:
                experience = st.slider("Experience", 0.0, 1.0, 0.25, 0.05)
            with col4:
                education = st.slider("Education", 0.0, 1.0, 0.15, 0.05)
            with col5:
                semantic = st.slider("Semantic Match", 0.0, 1.0, 0.10, 0.05)
            
            total_weight = hard_skills + soft_skills + experience + education + semantic
            if abs(total_weight - 1.0) > 0.01:
                st.warning(f"Weights must sum to 1.0 (current: {total_weight:.2f})")
            else:
                custom_weights = {
                    "hard_skills": hard_skills,
                    "soft_skills": soft_skills,
                    "experience": experience,
                    "education": education,
                    "semantic_match": semantic
                }
        
        if st.button("🚀 Run Evaluation", disabled=not (resume_id and job_id)):
            if resume_id and job_id:
                with st.spinner("Running AI evaluation..."):
                    try:
                        evaluation = api_client.evaluate_resume(resume_id, job_id, custom_weights)
                        if evaluation:
                            st.success("Evaluation completed!")
                            display_evaluation_results(evaluation)
                        else:
                            st.error("Evaluation failed")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    # Batch Evaluation
    with st.expander("📊 Batch Evaluation", expanded=False):
        st.markdown("Evaluate multiple resumes against a single job description")
        
        col1, col2 = st.columns(2)
        
        with col1:
            try:
                jobs = api_client.get_job_descriptions()
                job_options = {f"{j['title']} at {j['company']}": j['id'] for j in jobs}
                selected_batch_job = st.selectbox("Select Job Description", options=list(job_options.keys()), key="batch_job")
                batch_job_id = job_options.get(selected_batch_job) if selected_batch_job else None
            except:
                st.error("Failed to load job descriptions")
                batch_job_id = None
        
        with col2:
            try:
                resumes = api_client.get_resumes()
                resume_options = {f"{r['candidate_name']} - {r['filename']}": r['id'] for r in resumes}
                selected_resumes = st.multiselect("Select Resumes (max 50)", options=list(resume_options.keys()))
                resume_ids = [resume_options[r] for r in selected_resumes]
            except:
                st.error("Failed to load resumes")
                resume_ids = []
        
        if st.button("🎯 Run Batch Evaluation", disabled=not (batch_job_id and resume_ids)):
            if len(resume_ids) > 50:
                st.warning("Maximum 50 resumes allowed per batch")
            elif batch_job_id and resume_ids:
                with st.spinner(f"Evaluating {len(resume_ids)} resumes..."):
                    try:
                        results = api_client.batch_evaluate_resumes(resume_ids, batch_job_id)
                        if results:
                            st.success(f"Batch evaluation completed! Processed {results.get('total_processed', 0)} resumes")
                            display_batch_results(results)
                        else:
                            st.error("Batch evaluation failed")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

def display_evaluation_results(evaluation):
    """Display detailed evaluation results."""
    st.markdown("### 📊 Evaluation Results")
    
    # Overall Score Display
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        score = evaluation['overall_score']
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{score:.1f}/100</div>
            <div class="metric-label">Overall Score</div>
            <div class="progress-container">
                <div class="progress-bar" style="width: {score}%"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        suitability = evaluation['suitability']
        suitability_class = f"status-{suitability.lower()}"
        st.markdown(f"""
        <div class="metric-card">
            <div class="{suitability_class}">{suitability}</div>
            <div class="metric-label">Suitability</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        confidence = evaluation.get('confidence_score', 85)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{confidence:.0f}%</div>
            <div class="metric-label">Confidence</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Detailed Scores
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Score Breakdown")
        score_data = {
            'Category': ['Hard Skills', 'Soft Skills', 'Experience', 'Education'],
            'Score': [
                evaluation['hard_skills_score'],
                evaluation['soft_skills_score'],
                evaluation['experience_score'],
                evaluation['education_score']
            ]
        }
        charts.score_breakdown_chart(score_data)
    
    with col2:
        st.markdown("#### 🎯 Skills Analysis")
        
        matching_skills = evaluation.get('matching_skills', [])
        missing_skills = evaluation.get('missing_skills', [])
        
        if matching_skills:
            st.markdown("**✅ Matching Skills:**")
            for skill in matching_skills[:8]:
                st.markdown(f'<span class="skill-tag">{skill}</span>', unsafe_allow_html=True)
        
        if missing_skills:
            st.markdown("**❌ Missing Skills:**")
            for skill in missing_skills[:8]:
                st.markdown(f'<span class="skill-tag" style="background: #e74c3c;">{skill}</span>', unsafe_allow_html=True)
    
    # Feedback Section
    st.markdown("#### 💡 AI-Generated Feedback")
    
    col1, col2 = st.columns(2)
    
    with col1:
        strengths = evaluation.get('strengths', [])
        if strengths:
            st.markdown("**🌟 Key Strengths:**")
            for strength in strengths[:5]:
                st.markdown(f"• {strength}")
    
    with col2:
        weaknesses = evaluation.get('weaknesses', [])
        if weaknesses:
            st.markdown("**📈 Areas for Improvement:**")
            for weakness in weaknesses[:5]:
                st.markdown(f"• {weakness}")
    
    # Personalized Feedback
    feedback = evaluation.get('personalized_feedback')
    if feedback:
        st.markdown("#### 📝 Detailed Assessment")
        st.info(feedback)
    
    # Recommendations
    suggestions = evaluation.get('suggestions', [])
    if suggestions:
        st.markdown("#### 🎯 Actionable Recommendations")
        for i, suggestion in enumerate(suggestions[:5], 1):
            st.markdown(f"{i}. {suggestion}")

def display_batch_results(results):
    """Display batch evaluation results."""
    evaluations = results.get('evaluations', [])
    
    if not evaluations:
        st.warning("No evaluation results to display")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    scores = [e['overall_score'] for e in evaluations]
    avg_score = sum(scores) / len(scores)
    
    with col1:
        st.metric("Total Evaluated", len(evaluations))
    with col2:
        st.metric("Average Score", f"{avg_score:.1f}")
    with col3:
        high_suitability = len([e for e in evaluations if e['suitability'] == 'High'])
        st.metric("High Suitability", high_suitability)
    with col4:
        top_score = max(scores)
        st.metric("Top Score", f"{top_score:.1f}")
    
    # Results table
    st.markdown("### 📊 Batch Results")
    
    # Create DataFrame for better display
    df_data = []
    for eval_data in evaluations:
        df_data.append({
            'Rank': 0,  # Will be set after sorting
            'Resume ID': eval_data['resume_id'],
            'Overall Score': eval_data['overall_score'],
            'Suitability': eval_data['suitability'],
            'Hard Skills': eval_data['hard_skills_score'],
            'Experience': eval_data['experience_score'],
            'Matching Skills': len(eval_data.get('matching_skills', [])),
            'Missing Skills': len(eval_data.get('missing_skills', []))
        })
    
    df = pd.DataFrame(df_data)
    df = df.sort_values('Overall Score', ascending=False)
    df['Rank'] = range(1, len(df) + 1)
    
    # Display with color coding
    def color_suitability(val):
        if val == 'High':
            return 'background-color: #d4edda'
        elif val == 'Medium':
            return 'background-color: #fff3cd'
        else:
            return 'background-color: #f8d7da'
    
    styled_df = df.style.applymap(color_suitability, subset=['Suitability'])
    st.dataframe(styled_df, use_container_width=True)

def render_analytics_page():
    """Render the analytics page."""
    st.markdown("## 📈 Advanced Analytics")
    
    # Time range selector
    col1, col2 = st.columns([3, 1])
    with col2:
        days = st.selectbox("Time Range", [7, 30, 90, 365], index=1)
    
    try:
        # Load analytics data
        dashboard_data = api_client.get("/analytics/dashboard", params={"days": days})
        skill_data = api_client.get("/analytics/skills", params={"days": days})
        candidate_data = api_client.get("/analytics/candidates", params={"days": days})
        
        # Skills Analytics
        st.markdown("### 🎯 Skills Intelligence")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Most In-Demand Skills")
            skills_in_demand = skill_data.get('top_skills_in_demand', [])
            charts.skills_demand_chart(skills_in_demand)
        
        with col2:
            st.markdown("#### ⚠️ Biggest Skill Gaps")
            skill_gaps = skill_data.get('biggest_skill_gaps', [])
            charts.skill_gaps_chart(skill_gaps)
        
        # Supply vs Demand Analysis
        st.markdown("### ⚖️ Supply vs Demand Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📉 Undersupplied Skills")
            undersupplied = skill_data.get('undersupplied_skills', [])
            if undersupplied:
                df = pd.DataFrame(undersupplied)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No undersupplied skills data available")
        
        with col2:
            st.markdown("#### 📈 Oversupplied Skills")
            oversupplied = skill_data.get('oversupplied_skills', [])
            if oversupplied:
                df = pd.DataFrame(oversupplied)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No oversupplied skills data available")
        
        # Candidate Analytics
        st.markdown("### 👥 Candidate Insights")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 📊 Score Distribution")
            score_dist = candidate_data.get('score_distribution', {})
            charts.score_distribution_chart(score_dist)
        
        with col2:
            st.markdown("#### 💼 Experience Levels")
            exp_analysis = candidate_data.get('experience_analysis', {})
            charts.experience_levels_chart(exp_analysis)
        
        with col3:
            st.markdown("#### 🌍 Top Locations")
            location_analysis = candidate_data.get('location_analysis', {})
            charts.location_chart(location_analysis)
        
    except Exception as e:
        st.error(f"Failed to load analytics data: {str(e)}")

def render_benchmarking_page():
    """Render the benchmarking page."""
    st.markdown("## 🎯 Peer Benchmarking System")
    
    st.info("🚀 **Innovation Feature**: Compare candidates against industry benchmarks and top performers")
    
    # Job selection for benchmarking
    try:
        jobs = api_client.get_job_descriptions()
        job_options = {f"{j['title']} at {j['company']}": j['id'] for j in jobs}
        selected_job = st.selectbox("Select Job for Benchmarking", options=list(job_options.keys()))
        job_id = job_options.get(selected_job) if selected_job else None
        
        if job_id:
            # Load benchmark data
            benchmark_data = api_client.get(f"/analytics/benchmarks/{job_id}")
            
            if benchmark_data.get('total_candidates', 0) > 0:
                st.markdown("### 📊 Performance Benchmarks")
                
                col1, col2, col3, col4 = st.columns(4)
                
                percentiles = benchmark_data.get('score_percentiles', {})
                
                with col1:
                    st.metric("90th Percentile", f"{percentiles.get('p90', 0):.1f}")
                with col2:
                    st.metric("75th Percentile", f"{percentiles.get('p75', 0):.1f}")
                with col3:
                    st.metric("50th Percentile", f"{percentiles.get('p50', 0):.1f}")
                with col4:
                    st.metric("25th Percentile", f"{percentiles.get('p25', 0):.1f}")
                
                # Benchmark visualization
                charts.benchmark_distribution_chart(percentiles)
                
                # Top performers
                st.markdown("### 🏆 Top Performers Analysis")
                
                evaluations = api_client.get(f"/matching/jobs/{job_id}/evaluations?limit=10")
                if evaluations:
                    top_performers = evaluations.get('evaluations', [])[:5]
                    tables.top_performers_table(top_performers)
                
            else:
                st.warning("No benchmark data available for this job. Evaluations needed to generate benchmarks.")
    
    except Exception as e:
        st.error(f"Failed to load benchmarking data: {str(e)}")

def render_settings_page():
    """Render the settings page."""
    st.markdown("## ⚙️ System Settings")
    
    # User settings
    user = st.session_state.get('user', {})
    
    with st.expander("👤 User Profile", expanded=True):
        with st.form("profile_form"):
            st.text_input("Full Name", value=user.get('full_name', ''))
            st.text_input("Email", value=user.get('email', ''), disabled=True)
            st.text_input("Username", value=user.get('username', ''), disabled=True)
            st.selectbox("Role", ['recruiter', 'admin', 'student'], 
                        index=['recruiter', 'admin', 'student'].index(user.get('role', 'recruiter')))
            
            if st.form_submit_button("Update Profile"):
                st.success("Profile updated successfully!")
    
    # System Configuration
    with st.expander("🔧 Scoring Configuration"):
        st.markdown("Configure default scoring weights for evaluations")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.slider("Hard Skills Weight", 0.0, 1.0, 0.35, key="default_hard_skills")
        with col2:
            st.slider("Soft Skills Weight", 0.0, 1.0, 0.15, key="default_soft_skills")
        with col3:
            st.slider("Experience Weight", 0.0, 1.0, 0.25, key="default_experience")
        with col4:
            st.slider("Education Weight", 0.0, 1.0, 0.15, key="default_education")
        with col5:
            st.slider("Semantic Weight", 0.0, 1.0, 0.10, key="default_semantic")
        
        if st.button("Save Default Weights"):
            st.success("Default weights saved!")
    
    # API Configuration
    with st.expander("🔌 API Configuration"):
        api_url = st.text_input("API Base URL", value="http://localhost:8000")
        if st.button("Test Connection"):
            try:
                response = api_client.get("/health")
                if response:
                    st.success("✅ API connection successful!")
                else:
                    st.error("❌ API connection failed")
            except:
                st.error("❌ Could not connect to API")

if __name__ == "__main__":
    main()
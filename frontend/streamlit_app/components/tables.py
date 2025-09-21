import streamlit as st
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime


class TableComponents:
    """Table components for displaying structured data."""
    
    def recent_evaluations_table(self, evaluations: List[Dict[str, Any]]):
        """Display recent evaluations in a formatted table."""
        if not evaluations:
            st.info("No recent evaluations found")
            return
        
        # Prepare data for display
        table_data = []
        for eval_data in evaluations:
            table_data.append({
                'ID': eval_data.get('id', 'N/A'),
                'Score': f"{eval_data.get('score', 0):.1f}",
                'Suitability': eval_data.get('suitability', 'Unknown'),
                'Date': eval_data.get('created_at', ''),
            })
        
        df = pd.DataFrame(table_data)
        
        # Style the dataframe
        def color_suitability(val):
            if val == 'High':
                return 'background-color: #d4edda; color: #155724'
            elif val == 'Medium':
                return 'background-color: #fff3cd; color: #856404'
            elif val == 'Low':
                return 'background-color: #f8d7da; color: #721c24'
            return ''
        
        styled_df = df.style.applymap(color_suitability, subset=['Suitability'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    def resumes_table(self, resumes: List[Dict[str, Any]]):
        """Display resumes in a comprehensive table."""
        if not resumes:
            st.info("No resumes found")
            return
        
        # Prepare data
        table_data = []
        for resume in resumes:
            skills_preview = ', '.join(resume.get('skills', [])[:3])
            if len(resume.get('skills', [])) > 3:
                skills_preview += f" (+{len(resume.get('skills', [])) - 3} more)"
            
            table_data.append({
                'ID': resume.get('id'),
                'Candidate': resume.get('candidate_name', 'Unknown'),
                'Email': resume.get('candidate_email', 'N/A'),
                'Experience': f"{resume.get('experience_years', 0)} years" if resume.get('experience_years') else 'N/A',
                'Top Skills': skills_preview,
                'Status': resume.get('processing_status', 'Unknown'),
                'Uploaded': resume.get('created_at', '')[:10] if resume.get('created_at') else 'N/A'
            })
        
        df = pd.DataFrame(table_data)
        
        # Add action buttons
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("**Actions**")
            for i, resume in enumerate(resumes[:10]):  # Limit to first 10
                if st.button(f"View {resume['id']}", key=f"view_resume_{resume['id']}"):
                    st.session_state[f'selected_resume'] = resume
                    st.rerun()
    
    def jobs_table(self, jobs: List[Dict[str, Any]]):
        """Display job descriptions in a table."""
        if not jobs:
            st.info("No job descriptions found")
            return
        
        # Prepare data
        table_data = []
        for job in jobs:
            req_skills = ', '.join(job.get('required_skills', [])[:3])
            if len(job.get('required_skills', [])) > 3:
                req_skills += f" (+{len(job.get('required_skills', [])) - 3} more)"
            
            table_data.append({
                'ID': job.get('id'),
                'Title': job.get('title', 'Unknown'),
                'Company': job.get('company', 'Unknown'),
                'Location': job.get('location', 'N/A'),
                'Type': job.get('job_type', 'N/A'),
                'Required Skills': req_skills,
                'Status': job.get('status', 'Unknown'),
                'Created': job.get('created_at', '')[:10] if job.get('created_at') else 'N/A'
            })
        
        df = pd.DataFrame(table_data)
        
        # Style based on status
        def color_status(val):
            if val == 'active':
                return 'background-color: #d4edda'
            elif val == 'closed':
                return 'background-color: #f8d7da'
            return ''
        
        styled_df = df.style.applymap(color_status, subset=['Status'])
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("**Actions**")
            for job in jobs[:10]:  # Limit to first 10
                if st.button(f"View {job['id']}", key=f"view_job_{job['id']}"):
                    st.session_state[f'selected_job'] = job
                    st.rerun()
    
    def top_performers_table(self, performers: List[Dict[str, Any]]):
        """Display top performers table."""
        if not performers:
            st.info("No top performers data available")
            return
        
        table_data = []
        for i, performer in enumerate(performers, 1):
            table_data.append({
                'Rank': i,
                'Resume ID': performer.get('resume_id'),
                'Overall Score': f"{performer.get('overall_score', 0):.1f}",
                'Hard Skills': f"{performer.get('hard_skills_score', 0):.1f}",
                'Experience': f"{performer.get('experience_score', 0):.1f}",
                'Suitability': performer.get('suitability', 'Unknown'),
                'Date': performer.get('created_at', '')[:10] if performer.get('created_at') else 'N/A'
            })
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
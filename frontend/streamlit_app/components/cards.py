import streamlit as st
from typing import Optional


class CardComponents:
    """Card components for displaying metrics and information."""
    
    def metric_card(self, title: str, value: str, delta: Optional[str] = None, color: str = "#667eea"):
        """Create a styled metric card."""
        delta_class = ""
        delta_html = ""
        
        if delta:
            if delta.startswith('+'):
                delta_class = "positive"
                delta_html = f'<div class="metric-delta {delta_class}">↗️ {delta}</div>'
            elif delta.startswith('-'):
                delta_class = "negative"
                delta_html = f'<div class="metric-delta {delta_class}">↘️ {delta}</div>'
            else:
                delta_html = f'<div class="metric-delta">{delta}</div>'
        
        card_html = f"""
        <div class="metric-card" style="border-left-color: {color};">
            <div class="metric-value">{value}</div>
            <div class="metric-label">{title}</div>
            {delta_html}
        </div>
        """
        
        st.markdown(card_html, unsafe_allow_html=True)
    
    def skill_tags(self, skills: list, title: str = "Skills", max_display: int = 10):
        """Display skills as styled tags."""
        if not skills:
            return
        
        st.markdown(f"**{title}:**")
        
        skills_html = ""
        for skill in skills[:max_display]:
            skills_html += f'<span class="skill-tag">{skill}</span> '
        
        if len(skills) > max_display:
            skills_html += f'<span class="skill-tag" style="background: #95a5a6;">+{len(skills) - max_display} more</span>'
        
        st.markdown(skills_html, unsafe_allow_html=True)
    
    def progress_bar(self, value: float, max_value: float = 100, label: str = "", color: str = "#667eea"):
        """Create a styled progress bar."""
        percentage = (value / max_value) * 100 if max_value > 0 else 0
        
        progress_html = f"""
        <div style="margin: 0.5rem 0;">
            {f'<div style="font-size: 0.9rem; margin-bottom: 0.2rem;">{label}</div>' if label else ''}
            <div class="progress-container">
                <div class="progress-bar" style="width: {percentage}%; background: {color};"></div>
            </div>
            <div style="font-size: 0.8rem; color: #7f8c8d; text-align: right;">{value}/{max_value}</div>
        </div>
        """
        
        st.markdown(progress_html, unsafe_allow_html=True)
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from typing import Any, Dict, List


def format_date(date_string: str) -> str:
    """Format date string for display."""
    try:
        if not date_string:
            return "N/A"
        
        # Parse ISO format
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return date_string


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f}{size_names[i]}"


def get_score_color(score: float) -> str:
    """Get color based on score value."""
    if score >= 80:
        return "#27ae60"  # Green
    elif score >= 60:
        return "#f39c12"  # Orange
    else:
        return "#e74c3c"  # Red


def get_suitability_emoji(suitability: str) -> str:
    """Get emoji for suitability level."""
    emoji_map = {
        'High': '🟢',
        'Medium': '🟡',
        'Low': '🔴'
    }
    return emoji_map.get(suitability, '⚪')


def create_download_link(data: Any, filename: str, link_text: str = "Download") -> str:
    """Create download link for data."""
    import base64
    import json
    
    if isinstance(data, dict) or isinstance(data, list):
        data_str = json.dumps(data, indent=2)
    else:
        data_str = str(data)
    
    b64 = base64.b64encode(data_str.encode()).decode()
    href = f'<a href="data:application/json;base64,{b64}" download="{filename}" target="_blank">{link_text}</a>'
    return href


def display_skill_heatmap(skills_data: List[Dict[str, Any]]):
    """Display skills as a heatmap-style visualization."""
    if not skills_data:
        st.info("No skills data available")
        return
    
    # Create columns for skill display
    cols = st.columns(4)
    
    for i, skill_data in enumerate(skills_data[:20]):  # Top 20 skills
        col_idx = i % 4
        skill = skill_data.get('skill', 'Unknown')
        count = skill_data.get('count', 0)
        
        with cols[col_idx]:
            # Normalize count for visual representation
            max_count = max([s.get('count', 0) for s in skills_data]) if skills_data else 1
            intensity = (count / max_count) * 100
            
            color_intensity = int(255 - (intensity * 2))  # Darker = higher demand
            bg_color = f"rgba(102, 126, 234, {intensity/100})"
            
            st.markdown(f"""
            <div style="
                background: {bg_color};
                padding: 0.5rem;
                margin: 0.2rem 0;
                border-radius: 5px;
                text-align: center;
                font-size: 0.8rem;
                color: {'white' if intensity > 50 else 'black'};
            ">
                <strong>{skill}</strong><br>
                {count} mentions
            </div>
            """, unsafe_allow_html=True)


def show_processing_status(status: str):
    """Show processing status with appropriate styling."""
    status_styles = {
        'processed': {'color': '#27ae60', 'icon': '✅'},
        'processing': {'color': '#f39c12', 'icon': '⏳'},
        'failed': {'color': '#e74c3c', 'icon': '❌'},
        'pending': {'color': '#95a5a6', 'icon': '⏸️'}
    }
    
    style = status_styles.get(status, {'color': '#95a5a6', 'icon': '❓'})
    
    st.markdown(f"""
    <span style="color: {style['color']};">
        {style['icon']} {status.title()}
    </span>
    """, unsafe_allow_html=True)


def create_metric_cards_row(metrics: List[Dict[str, Any]]):
    """Create a row of metric cards."""
    if not metrics:
        return
    
    cols = st.columns(len(metrics))
    
    for i, metric in enumerate(metrics):
        with cols[i]:
            title = metric.get('title', 'Metric')
            value = metric.get('value', 0)
            delta = metric.get('delta')
            color = metric.get('color', '#667eea')
            
            from components.cards import CardComponents
            cards = CardComponents()
            cards.metric_card(title, str(value), delta, color)
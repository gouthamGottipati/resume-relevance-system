import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Any


class ChartComponents:
    """Chart components for data visualization."""
    
    def suitability_pie_chart(self, data: Dict[str, int]):
        """Create a suitability distribution pie chart."""
        if not data:
            st.info("No data available for suitability distribution")
            return
        
        labels = [k.title() for k in data.keys()]
        values = list(data.values())
        colors = ['#27ae60', '#f39c12', '#e74c3c']  # Green, Orange, Red
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker_colors=colors,
            textinfo='label+percent',
            textfont_size=12,
            hole=0.4
        )])
        
        fig.update_layout(
            showlegend=True,
            height=350,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def skills_bar_chart(self, skills_data: List[Dict[str, Any]]):
        """Create a horizontal bar chart for top skills."""
        if not skills_data:
            st.info("No skills data available")
            return
        
        df = pd.DataFrame(skills_data[:10])  # Top 10 skills
        if df.empty:
            st.info("No skills data to display")
            return
        
        fig = px.bar(
            df,
            x='demand_count' if 'demand_count' in df.columns else 'count',
            y='skill',
            orientation='h',
            color='demand_count' if 'demand_count' in df.columns else 'count',
            color_continuous_scale=['#667eea', '#764ba2'],
            title="Skills Demand Analysis"
        )
        
        fig.update_layout(
            height=400,
            showlegend=False,
            xaxis_title="Demand Count",
            yaxis_title="Skills",
            yaxis={'categoryorder': 'total ascending'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def score_breakdown_chart(self, score_data: Dict[str, List]):
        """Create a radar chart for score breakdown."""
        categories = score_data['Category']
        scores = score_data['Score']
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=scores,
            theta=categories,
            fill='toself',
            fillcolor='rgba(102, 126, 234, 0.2)',
            line=dict(color='rgba(102, 126, 234, 1)', width=2),
            marker=dict(size=8, color='rgba(102, 126, 234, 1)'),
            name='Scores'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickmode='linear',
                    tick0=0,
                    dtick=20
                )
            ),
            showlegend=False,
            height=350,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def skills_demand_chart(self, skills_data: List[Dict[str, Any]]):
        """Create a chart for skills demand analysis."""
        if not skills_data:
            st.info("No skills demand data available")
            return
        
        df = pd.DataFrame(skills_data)
        if df.empty:
            return
        
        fig = px.treemap(
            df,
            path=['skill'],
            values='count' if 'count' in df.columns else 'demand_count',
            color='count' if 'count' in df.columns else 'demand_count',
            color_continuous_scale='Viridis',
            title="Skills Demand Heatmap"
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    def skill_gaps_chart(self, gaps_data: List[Dict[str, Any]]):
        """Create a chart for skill gaps."""
        if not gaps_data:
            st.info("No skill gaps data available")
            return
        
        df = pd.DataFrame(gaps_data[:8])  # Top 8 gaps
        if df.empty:
            return
        
        fig = px.bar(
            df,
            x='skill',
            y='count',
            color='count',
            color_continuous_scale=['#e74c3c', '#c0392b'],
            title="Most Critical Skill Gaps"
        )
        
        fig.update_layout(
            height=300,
            showlegend=False,
            xaxis_title="Skills",
            yaxis_title="Gap Frequency"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def score_distribution_chart(self, score_dist: Dict[str, int]):
        """Create a chart for score distribution."""
        if not score_dist:
            st.info("No score distribution data")
            return
        
        df = pd.DataFrame(list(score_dist.items()), columns=['Range', 'Count'])
        
        fig = px.bar(
            df,
            x='Range',
            y='Count',
            color='Count',
            color_continuous_scale='RdYlGn',
            title="Candidate Score Distribution"
        )
        
        fig.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    def experience_levels_chart(self, exp_data: Dict[str, int]):
        """Create a chart for experience levels."""
        if not exp_data:
            st.info("No experience data available")
            return
        
        labels = list(exp_data.keys())
        values = list(exp_data.values())
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            textinfo='label+value',
            textfont_size=10
        )])
        
        fig.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    def location_chart(self, location_data: Dict[str, int]):
        """Create a chart for candidate locations."""
        if not location_data:
            st.info("No location data available")
            return
        
        df = pd.DataFrame(list(location_data.items()), columns=['Location', 'Count'])
        df = df.head(10)  # Top 10 locations
        
        fig = px.bar(
            df,
            x='Count',
            y='Location',
            orientation='h',
            color='Count',
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(
            height=300,
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def benchmark_distribution_chart(self, percentiles: Dict[str, float]):
        """Create a benchmark distribution chart."""
        if not percentiles:
            st.info("No benchmark data available")
            return
        
        # Create a box plot style visualization
        fig = go.Figure()
        
        fig.add_trace(go.Box(
            y=[percentiles.get('p25', 0), percentiles.get('p50', 0), 
               percentiles.get('p75', 0), percentiles.get('p90', 0)],
            name="Score Distribution",
            boxpoints='all',
            jitter=0.3,
            pointpos=-1.8,
            marker_color='rgba(102, 126, 234, 0.6)'
        ))
        
        fig.update_layout(
            title="Performance Benchmark Distribution",
            yaxis_title="Scores",
            height=300,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
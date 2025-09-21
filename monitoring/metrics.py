"""Custom metrics collection for Resume AI System."""

import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class MetricsCollector:
    """Collect and export custom metrics."""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        self._setup_metrics()
    
    def _setup_metrics(self):
        """Setup Prometheus metrics."""
        # Counters
        self.resume_uploads_total = Counter(
            'resume_uploads_total',
            'Total number of resume uploads',
            ['status'],
            registry=self.registry
        )
        
        self.evaluations_total = Counter(
            'resume_evaluations_total',
            'Total number of resume evaluations',
            ['suitability'],
            registry=self.registry
        )
        
        self.api_requests_total = Counter(
            'api_requests_total',
            'Total API requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        # Histograms
        self.resume_processing_duration = Histogram(
            'resume_processing_duration_seconds',
            'Time spent processing resumes',
            ['file_type'],
            registry=self.registry
        )
        
        self.evaluation_duration = Histogram(
            'evaluation_duration_seconds',
            'Time spent on resume evaluations',
            ['complexity'],
            registry=self.registry
        )
        
        self.api_request_duration = Histogram(
            'api_request_duration_seconds',
            'API request duration',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # Gauges
        self.active_users = Gauge(
            'active_users',
            'Number of active users',
            registry=self.registry
        )
        
        self.pending_evaluations = Gauge(
            'pending_evaluations',
            'Number of pending evaluations',
            registry=self.registry
        )
        
        self.system_health = Gauge(
            'system_health_score',
            'Overall system health score (0-1)',
            registry=self.registry
        )
    
    def record_resume_upload(self, status: str):
        """Record resume upload event."""
        self.resume_uploads_total.labels(status=status).inc()
    
    def record_evaluation(self, suitability: str, duration: float):
        """Record evaluation event."""
        self.evaluations_total.labels(suitability=suitability).inc()
        complexity = "high" if duration > 30 else "medium" if duration > 10 else "low"
        self.evaluation_duration.labels(complexity=complexity).observe(duration)
    
    def record_api_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record API request."""
        self.api_requests_total.labels(
            method=method, 
            endpoint=endpoint, 
            status=str(status)
        ).inc()
        
        self.api_request_duration.labels(
            method=method, 
            endpoint=endpoint
        ).observe(duration)
    
    def record_resume_processing(self, file_type: str, duration: float):
        """Record resume processing metrics."""
        self.resume_processing_duration.labels(file_type=file_type).observe(duration)
    
    def update_active_users(self, count: int):
        """Update active users count."""
        self.active_users.set(count)
    
    def update_pending_evaluations(self, count: int):
        """Update pending evaluations count."""
        self.pending_evaluations.set(count)
    
    def update_system_health(self, score: float):
        """Update system health score."""
        self.system_health.set(score)
    
    def get_metrics(self) -> str:
        """Get metrics in Prometheus format."""
        return generate_latest(self.registry).decode()


# Global metrics collector
metrics_collector = MetricsCollector()

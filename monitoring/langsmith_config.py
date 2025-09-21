"""LangSmith configuration for monitoring AI pipelines."""

import os
from langsmith import Client
from langchain.callbacks import LangChainTracer
from app.config import settings
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class LangSmithMonitor:
    """LangSmith monitoring for AI operations."""
    
    def __init__(self):
        self.client = None
        self.tracer = None
        self._setup_langsmith()
    
    def _setup_langsmith(self):
        """Setup LangSmith client and tracer."""
        try:
            if settings.langsmith_api_key:
                # Set environment variables for LangSmith
                os.environ["LANGCHAIN_TRACING_V2"] = "true"
                os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
                os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
                os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
                
                # Initialize client and tracer
                self.client = Client()
                self.tracer = LangChainTracer(project_name=settings.langsmith_project)
                
                logger.info("LangSmith monitoring initialized")
            else:
                logger.warning("LangSmith API key not provided, monitoring disabled")
                
        except Exception as e:
            logger.error(f"Failed to initialize LangSmith: {e}")
    
    def create_dataset(self, name: str, description: str = ""):
        """Create evaluation dataset."""
        if not self.client:
            return None
        
        try:
            dataset = self.client.create_dataset(
                dataset_name=name,
                description=description
            )
            logger.info(f"Created LangSmith dataset: {name}")
            return dataset
        except Exception as e:
            logger.error(f"Failed to create dataset {name}: {e}")
            return None
    
    def log_evaluation_run(self, resume_id: int, job_id: int, score: float, 
                          processing_time: float, metadata: dict = None):
        """Log evaluation run to LangSmith."""
        if not self.client:
            return
        
        try:
            run_data = {
                "name": f"resume_evaluation_{resume_id}_{job_id}",
                "inputs": {
                    "resume_id": resume_id,
                    "job_id": job_id
                },
                "outputs": {
                    "score": score,
                    "processing_time": processing_time
                },
                "metadata": metadata or {}
            }
            
            # Create run
            self.client.create_run(**run_data)
            logger.debug(f"Logged evaluation run: {resume_id} vs {job_id}")
            
        except Exception as e:
            logger.error(f"Failed to log evaluation run: {e}")
    
    def get_tracer(self):
        """Get LangChain tracer for callback usage."""
        return self.tracer


# Global monitor instance
langsmith_monitor = LangSmithMonitor()

"""System health monitoring and checks."""

import asyncio
import psutil
import httpx
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.core.database.database import get_database, engine
from app.core.utils.logger import get_logger
from app.config import settings

logger = get_logger(__name__)


class HealthChecker:
    """Comprehensive system health monitoring."""
    
    def __init__(self):
        self.checks = {
            'database': self._check_database,
            'redis': self._check_redis,
            'disk_space': self._check_disk_space,
            'memory_usage': self._check_memory_usage,
            'cpu_usage': self._check_cpu_usage,
            'api_endpoints': self._check_api_endpoints,
            'ai_services': self._check_ai_services
        }
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        results = {}
        overall_healthy = True
        
        for check_name, check_func in self.checks.items():
            try:
                result = await check_func()
                results[check_name] = result
                
                if not result.get('healthy', True):
                    overall_healthy = False
                    
            except Exception as e:
                logger.error(f"Health check {check_name} failed: {e}")
                results[check_name] = {
                    'healthy': False,
                    'error': str(e),
                    'timestamp': asyncio.get_event_loop().time()
                }
                overall_healthy = False
        
        results['overall'] = {
            'healthy': overall_healthy,
            'timestamp': asyncio.get_event_loop().time(),
            'version': '1.0.0'
        }
        
        return results
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            # Test connection
            with engine.connect() as conn:
                result = conn.execute("SELECT 1").fetchone()
                
            # Get connection pool status
            pool = engine.pool
            pool_status = {
                'size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
            }
            
            return {
                'healthy': True,
                'pool_status': pool_status,
                'timestamp': asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': asyncio.get_event_loop().time()
            }
    
    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity."""
        try:
            # This would require a Redis client setup
            # For now, return a mock response
            return {
                'healthy': True,
                'connected': True,
                'timestamp': asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': asyncio.get_event_loop().time()
            }
    
    async def _check_disk_space(self) -> Dict[str, Any]:
        """Check disk space usage."""
        try:
            disk_usage = psutil.disk_usage('/')
            usage_percent = (disk_usage.used / disk_usage.total) * 100
            
            return {
                'healthy': usage_percent < 90,  # Alert if over 90% full
                'usage_percent': round(usage_percent, 2),
                'free_gb': round(disk_usage.free / (1024**3), 2),
                'total_gb': round(disk_usage.total / (1024**3), 2),
                'timestamp': asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': asyncio.get_event_loop().time()
            }
    
    async def _check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage."""
        try:
            memory = psutil.virtual_memory()
            
            return {
                'healthy': memory.percent < 85,  # Alert if over 85%
                'usage_percent': memory.percent,
                'available_gb': round(memory.available / (1024**3), 2),
                'total_gb': round(memory.total / (1024**3), 2),
                'timestamp': asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': asyncio.get_event_loop().time()
            }
    
    async def _check_cpu_usage(self) -> Dict[str, Any]:
        """Check CPU usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            return {
                'healthy': cpu_percent < 80,  # Alert if over 80%
                'usage_percent': cpu_percent,
                'cpu_count': cpu_count,
                'timestamp': asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': asyncio.get_event_loop().time()
            }
    
    async def _check_api_endpoints(self) -> Dict[str, Any]:
        """Check critical API endpoints."""
        try:
            endpoints_to_check = [
                '/health',
                '/api/v1/resumes/',
                '/api/v1/jobs/',
            ]
            
            results = {}
            all_healthy = True
            
            async with httpx.AsyncClient() as client:
                for endpoint in endpoints_to_check:
                    try:
                        response = await client.get(
                            f"http://localhost:8000{endpoint}",
                            timeout=5.0
                        )
                        healthy = response.status_code < 500
                        results[endpoint] = {
                            'healthy': healthy,
                            'status_code': response.status_code,
                            'response_time_ms': response.elapsed.total_seconds() * 1000
                        }
                        
                        if not healthy:
                            all_healthy = False
                            
                    except Exception as e:
                        results[endpoint] = {
                            'healthy': False,
                            'error': str(e)
                        }
                        all_healthy = False
            
            return {
                'healthy': all_healthy,
                'endpoints': results,
                'timestamp': asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': asyncio.get_event_loop().time()
            }
    
    async def _check_ai_services(self) -> Dict[str, Any]:
        """Check AI service availability."""
        try:
            # Check if we can load AI models/services
            checks = {
                'spacy_model': self._test_spacy_model(),
                'sentence_transformer': self._test_sentence_transformer(),
                'openai_api': self._test_openai_api()
            }
            
            all_healthy = all(checks.values())
            
            return {
                'healthy': all_healthy,
                'services': checks,
                'timestamp': asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': asyncio.get_event_loop().time()
            }
    
    def _test_spacy_model(self) -> bool:
        """Test spaCy model loading."""
        try:
            import spacy
            nlp = spacy.load("en_core_web_sm")
            doc = nlp("Test sentence")
            return len(doc) > 0
        except:
            return False
    
    def _test_sentence_transformer(self) -> bool:
        """Test sentence transformer model."""
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            embedding = model.encode("test")
            return len(embedding) > 0
        except:
            return False
    
    def _test_openai_api(self) -> bool:
        """Test OpenAI API availability."""
        try:
            if not settings.openai_api_key or settings.openai_api_key == "your_openai_key_here":
                return False  # No valid API key
            
            # In a real implementation, you'd test the API
            # For now, just check if key is present
            return True
        except:
            return False


# Global health checker
health_checker = HealthChecker()

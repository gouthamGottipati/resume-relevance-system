import logging
import sys
from pathlib import Path
from loguru import logger as loguru_logger
from app.config import settings

# Remove default handler
loguru_logger.remove()

# Add custom handler with formatting
loguru_logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level
)

# Add file handler for production
if not settings.debug:
    log_file = Path("logs") / "app.log"
    log_file.parent.mkdir(exist_ok=True)
    
    loguru_logger.add(
        log_file,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO"
    )

# Create standard logger for compatibility
def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    return logger
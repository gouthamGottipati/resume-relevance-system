import os
import hashlib
import shutil
from pathlib import Path
from typing import Optional, Tuple, List
from werkzeug.utils import secure_filename
from app.config import settings
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class FileHandler:
    """Handle file upload, validation, and management."""
    
    def __init__(self):
        self.upload_dir = Path(settings.upload_directory)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.upload_dir / "resumes").mkdir(exist_ok=True)
        (self.upload_dir / "job_descriptions").mkdir(exist_ok=True)
        (self.upload_dir / "temp").mkdir(exist_ok=True)
    
    def validate_file(self, filename: str, file_size: int) -> Tuple[bool, Optional[str]]:
        """Validate uploaded file."""
        if file_size > settings.max_file_size:
            return False, f"File size exceeds {settings.max_file_size} bytes"
        
        if not filename:
            return False, "No filename provided"
        
        file_extension = filename.rsplit('.', 1)[-1].lower()
        if file_extension not in settings.allowed_extensions:
            return False, f"File type not allowed. Allowed types: {', '.join(settings.allowed_extensions)}"
        
        return True, None
    
    def save_file(self, file_content: bytes, filename: str, file_type: str = "resume") -> Tuple[str, str]:
        """Save file to disk and return file path and hash."""
        # Secure filename
        secure_name = secure_filename(filename)
        
        # Generate file hash
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # Create unique filename with hash
        name, ext = secure_name.rsplit('.', 1)
        unique_filename = f"{name}_{file_hash[:8]}.{ext}"
        
        # Determine save path
        if file_type == "resume":
            file_path = self.upload_dir / "resumes" / unique_filename
        else:
            file_path = self.upload_dir / "job_descriptions" / unique_filename
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"File saved: {file_path}")
        return str(file_path), file_hash
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file from disk."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            return False
    
    def get_file_info(self, file_path: str) -> Optional[dict]:
        """Get file information."""
        try:
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            return {
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'name': os.path.basename(file_path)
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {str(e)}")
            return None
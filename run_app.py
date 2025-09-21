import sys
import os
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variables
os.environ['DATABASE_URL'] = 'sqlite:///./resume_system.db'
os.environ['SECRET_KEY'] = 'demo-secret-key'
os.environ['DEBUG'] = 'True'

# Now import and run
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
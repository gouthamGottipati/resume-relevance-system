import os
import sqlite3
import sys
from pathlib import Path

def create_simple_database():
    """Create a simple SQLite database with basic tables"""
    
    # Create database file
    db_path = "resume_system.db"
    
    # Connect to SQLite database (creates if doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        username TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        full_name TEXT,
        role TEXT DEFAULT 'recruiter',
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create job_descriptions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS job_descriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        company TEXT NOT NULL,
        raw_content TEXT NOT NULL,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users (id)
    )
    """)
    
    # Create resumes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_name TEXT NOT NULL,
        candidate_email TEXT,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        raw_text TEXT,
        processing_status TEXT DEFAULT 'processed',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Insert admin user (simple password hash for demo)
    cursor.execute("""
    INSERT OR IGNORE INTO users (email, username, hashed_password, full_name, role)
    VALUES ('admin@test.com', 'admin', 'admin123', 'Admin User', 'admin')
    """)
    
    # Insert sample job description
    cursor.execute("""
    INSERT OR IGNORE INTO job_descriptions (title, company, raw_content, created_by)
    VALUES ('Python Developer', 'Tech Corp', 'We are looking for a Python developer with experience in FastAPI, Django, and machine learning.', 1)
    """)
    
    conn.commit()
    conn.close()
    
    print("Database created successfully!")
    print("Admin login: admin / admin123")

def main():
    print("Setting up Resume AI System...")
    
    # Create necessary directories
    os.makedirs("uploads/resumes", exist_ok=True)
    os.makedirs("uploads/job_descriptions", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    print("Created directories")
    
    # Create simple database
    create_simple_database()
    
    # Create minimal .env file if it doesn't exist
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write("""DATABASE_URL=sqlite:///./resume_system.db
SECRET_KEY=your-secret-key-for-demo
DEBUG=True
OPENAI_API_KEY=your_openai_key_here
""")
        print("Created .env file")
    
    print("\nSetup complete!")
    print("\nTo start the system:")
    print("1. Backend: uvicorn app.main:app --host 127.0.0.1 --port 8000")
    print("2. Frontend: streamlit run frontend/streamlit_app/main.py")

if __name__ == "__main__":
    main()
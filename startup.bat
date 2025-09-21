# startup.bat (for Windows)
@echo off
echo Starting Resume AI System...

echo Creating necessary directories...
if not exist "uploads" mkdir uploads
if not exist "uploads\resumes" mkdir uploads\resumes
if not exist "uploads\job_descriptions" mkdir uploads\job_descriptions
if not exist "logs" mkdir logs

echo Checking for .env file...
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo Please edit .env file with your OpenAI API key
    pause
)

echo Starting services...
docker compose -f simple-docker-compose.yml up -d

echo Waiting for services to start...
timeout /t 30 /nobreak

echo System should be running at:
echo Frontend: http://localhost:8501
echo Backend API: http://localhost:8000/docs
echo.
echo Default login: admin / admin123
echo.
pause
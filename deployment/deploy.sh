#!/bin/bash

set -e

# Production deployment script for Resume AI System
echo "🚀 Starting Resume AI System Deployment..."

# Configuration
ENV=${1:-production}
DOMAIN=${2:-resumeai.com}
DOCKER_REGISTRY=${3:-your-registry.com}

echo "Environment: $ENV"
echo "Domain: $DOMAIN"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command_exists docker; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command_exists docker-compose; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs uploads/resumes uploads/job_descriptions uploads/temp
mkdir -p deployment/postgres deployment/nginx/ssl
mkdir -p data/processed/embeddings data/processed/extracted_text

# Generate SSL certificates (self-signed for development, replace with real certs for production)
echo "🔒 Setting up SSL certificates..."
if [[ ! -f "deployment/nginx/ssl/cert.pem" ]]; then
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout deployment/nginx/ssl/key.pem \
        -out deployment/nginx/ssl/cert.pem \
        -subj "/C=US/ST=CA/L=San Francisco/O=ResumeAI/OU=IT Department/CN=$DOMAIN"
    echo "✅ SSL certificates generated"
fi

# Create environment file if it doesn't exist
if [[ ! -f ".env" ]]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please update .env file with your actual configuration"
fi

# Build and start services
echo "🔨 Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
timeout=300
interval=10
elapsed=0

while [ $elapsed -lt $timeout ]; do
    if curl -f http://localhost/health > /dev/null 2>&1; then
        echo "✅ Services are ready!"
        break
    fi
    
    echo "⏳ Still waiting for services... ($elapsed/$timeout seconds)"
    sleep $interval
    elapsed=$((elapsed + interval))
done

if [ $elapsed -ge $timeout ]; then
    echo "❌ Services failed to start within $timeout seconds"
    echo "📋 Checking service logs:"
    docker-compose logs --tail=50
    exit 1
fi

# Initialize database with sample data
echo "💾 Initializing database..."
docker-compose exec backend python scripts/setup_database.py
docker-compose exec backend python scripts/populate_sample_data.py

echo "🎉 Deployment completed successfully!"
echo ""
echo "📊 System Status:"
echo "Frontend: http://localhost (or https://localhost for SSL)"
echo "Backend API: http://localhost/api/v1/"
echo "Health Check: http://localhost/health"
echo ""
echo "📋 Next Steps:"
echo "1. Update DNS to point $DOMAIN to this server"
echo "2. Replace self-signed SSL certificates with real ones"
echo "3. Configure environment variables in .env file"
echo "4. Set up monitoring and backups"
echo "5. Configure firewall rules"
echo ""
echo "🔐 Default Login Credentials:"
echo "Admin: admin / admin123"
echo "Recruiter: recruiter / recruiter123"
echo "Student: student / student123"
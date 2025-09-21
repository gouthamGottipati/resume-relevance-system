#!/bin/bash

set -e

# AWS deployment script
echo "☁️ Deploying Resume AI System to AWS..."

# Configuration
AWS_REGION=${AWS_REGION:-us-west-2}
CLUSTER_NAME=${CLUSTER_NAME:-resume-ai-cluster}
SERVICE_NAME=${SERVICE_NAME:-resume-ai-service}
ECR_REPOSITORY=${ECR_REPOSITORY:-resume-ai}

echo "AWS Region: $AWS_REGION"
echo "ECS Cluster: $CLUSTER_NAME"

# Check AWS CLI
if ! command -v aws >/dev/null 2>&1; then
    echo "❌ AWS CLI is not installed. Please install it first."
    exit 1
fi

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY"

echo "AWS Account ID: $AWS_ACCOUNT_ID"
echo "ECR URI: $ECR_URI"

# Create ECR repository if it doesn't exist
echo "📦 Creating ECR repository..."
aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION || \
aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION

# Login to ECR
echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI

# Build and push Docker images
echo "🔨 Building and pushing Docker images..."

# Backend image
docker build -t $ECR_REPOSITORY:backend-latest .
docker tag $ECR_REPOSITORY:backend-latest $ECR_URI:backend-latest
docker push $ECR_URI:backend-latest

echo "✅ Docker images pushed to ECR"

# Create ECS cluster
echo "🏗️ Creating ECS cluster..."
aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $AWS_REGION || echo "Cluster already exists"

# Create task definition (this would be a separate JSON file in practice)
echo "📋 Creating ECS task definition..."

cat > task-definition.json << EOF
{
    "family": "resume-ai-task",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "1024",
    "memory": "2048",
    "executionRoleArn": "arn:aws:iam::$AWS_ACCOUNT_ID:role/ecsTaskExecutionRole",
    "taskRoleArn": "arn:aws:iam::$AWS_ACCOUNT_ID:role/ecsTaskRole",
    "containerDefinitions": [
        {
            "name": "resume-ai-backend",
            "image": "$ECR_URI:backend-latest",
            "portMappings": [
                {
                    "containerPort": 8000,
                    "protocol": "tcp"
                }
            ],
            "environment": [
                {"name": "DATABASE_URL", "value": "postgresql://user:pass@rds-endpoint:5432/resume_ai"},
                {"name": "REDIS_URL", "value": "redis://elasticache-endpoint:6379/0"}
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/resume-ai",
                    "awslogs-region": "$AWS_REGION",
                    "awslogs-stream-prefix": "ecs"
                }
            }
        }
    ]
}
EOF

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json --region $AWS_REGION

# Create service (requires VPC, subnets, security groups to be set up)
echo "🚀 Creating ECS service..."
# This is a simplified version - in practice you'd need to set up VPC, load balancer, etc.

echo "✅ AWS deployment configuration created"
echo "📋 Manual steps required:"
echo "1. Set up RDS PostgreSQL database"
echo "2. Set up ElastiCache Redis cluster"
echo "3. Configure VPC, subnets, and security groups"
echo "4. Set up Application Load Balancer"
echo "5. Configure Route 53 for DNS"
echo "6. Set up CloudWatch for monitoring"

# Clean up
rm -f task-definition.json



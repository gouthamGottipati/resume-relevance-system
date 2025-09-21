# ===== deployment/gcp-deploy.sh =====
#!/bin/bash

set -e

# GCP deployment script
echo "☁️ Deploying Resume AI System to Google Cloud Platform..."

# Configuration
PROJECT_ID=${PROJECT_ID:-resume-ai-project}
REGION=${REGION:-us-central1}
CLUSTER_NAME=${CLUSTER_NAME:-resume-ai-cluster}

echo "GCP Project: $PROJECT_ID"
echo "Region: $REGION"

# Check gcloud CLI
if ! command -v gcloud >/dev/null 2>&1; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required GCP APIs..."
gcloud services enable container.googleapis.com
gcloud services enable cloudsql.googleapis.com
gcloud services enable redis.googleapis.com
gcloud services enable compute.googleapis.com

# Build and push to Container Registry
echo "📦 Building and pushing to Container Registry..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/resume-ai-backend .

# Create GKE cluster
echo "🏗️ Creating GKE cluster..."
gcloud container clusters create $CLUSTER_NAME \
    --region=$REGION \
    --num-nodes=2 \
    --machine-type=e2-standard-2 \
    --enable-autoscaling \
    --min-nodes=1 \
    --max-nodes=5 \
    --enable-autorepair \
    --enable-autoupgrade || echo "Cluster already exists"

# Get credentials
gcloud container clusters get-credentials $CLUSTER_NAME --region=$REGION

# Create Kubernetes configurations
echo "⚙️ Creating Kubernetes configurations..."

# Create namespace
kubectl create namespace resume-ai || echo "Namespace already exists"

# Create deployment
cat > k8s-deployment.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resume-ai-backend
  namespace: resume-ai
spec:
  replicas: 2
  selector:
    matchLabels:
      app: resume-ai-backend
  template:
    metadata:
      labels:
        app: resume-ai-backend
    spec:
      containers:
      - name: backend
        image: gcr.io/$PROJECT_ID/resume-ai-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: resume-ai-secrets
              key: database-url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: resume-ai-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: resume-ai-service
  namespace: resume-ai
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: resume-ai-backend
EOF

# Apply deployment
kubectl apply -f k8s-deployment.yaml

echo "✅ GCP deployment completed"
echo "📋 Manual steps required:"
echo "1. Create Cloud SQL PostgreSQL instance"
echo "2. Create Redis Memorystore instance"
echo "3. Create secrets with database credentials"
echo "4. Set up Cloud DNS for domain"
echo "5. Configure SSL certificates"

# Clean up
rm -f k8s-deployment.yaml

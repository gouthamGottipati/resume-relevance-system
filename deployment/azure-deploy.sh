#!/bin/bash

set -e

# Azure deployment script
echo "☁️ Deploying Resume AI System to Microsoft Azure..."

# Configuration
RESOURCE_GROUP=${RESOURCE_GROUP:-resume-ai-rg}
LOCATION=${LOCATION:-eastus}
ACR_NAME=${ACR_NAME:-resumeaiacr}
AKS_NAME=${AKS_NAME:-resume-ai-aks}

echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"

# Check Azure CLI
if ! command -v az >/dev/null 2>&1; then
    echo "❌ Azure CLI is not installed. Please install it first."
    exit 1
fi

# Login check
az account show > /dev/null || {
    echo "Please login to Azure first: az login"
    exit 1
}

# Create resource group
echo "🏗️ Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Azure Container Registry
echo "📦 Creating Azure Container Registry..."
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic || echo "ACR already exists"

# Build and push to ACR
echo "🔨 Building and pushing to ACR..."
az acr build --registry $ACR_NAME --image resume-ai-backend:latest .

# Create AKS cluster
echo "⚙️ Creating AKS cluster..."
az aks create \
    --resource-group $RESOURCE_GROUP \
    --name $AKS_NAME \
    --node-count 2 \
    --node-vm-size Standard_D2s_v3 \
    --enable-addons monitoring \
    --generate-ssh-keys \
    --attach-acr $ACR_NAME || echo "AKS cluster already exists"

# Get AKS credentials
az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_NAME

echo "✅ Azure deployment infrastructure created"
echo "📋 Manual steps required:"
echo "1. Create Azure Database for PostgreSQL"
echo "2. Create Azure Cache for Redis"
echo "3. Configure networking and security"
echo "4. Deploy Kubernetes manifests"
echo "5. Set up Azure DNS and SSL certificates"
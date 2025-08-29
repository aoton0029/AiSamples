#!/bin/bash

# Set the namespace for production
NAMESPACE="production"

# Apply the namespace configuration
kubectl apply -f ../k8s/production/namespace.yaml

# Deploy all services and deployments in production
kubectl apply -f ../k8s/production/n8n-deployment.yaml
kubectl apply -f ../k8s/production/n8n-service.yaml
kubectl apply -f ../k8s/production/ollama-deployment.yaml
kubectl apply -f ../k8s/production/ollama-service.yaml
kubectl apply -f ../k8s/production/redis-deployment.yaml
kubectl apply -f ../k8s/production/redis-service.yaml
kubectl apply -f ../k8s/production/neo4j-deployment.yaml
kubectl apply -f ../k8s/production/neo4j-service.yaml
kubectl apply -f ../k8s/production/mongodb-deployment.yaml
kubectl apply -f ../k8s/production/mongodb-service.yaml
kubectl apply -f ../k8s/production/milvus-deployment.yaml
kubectl apply -f ../k8s/production/milvus-service.yaml
kubectl apply -f ../k8s/production/fastapi-deployment.yaml
kubectl apply -f ../k8s/production/fastapi-service.yaml

# Apply the ConfigMap for production
kubectl apply -f ../k8s/production/configmap.yaml

echo "Production deployment completed."
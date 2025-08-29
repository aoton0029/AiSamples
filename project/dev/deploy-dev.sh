#!/bin/bash

# Set the namespace for development
NAMESPACE="development"

# Create the namespace if it doesn't exist
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Apply all Kubernetes configurations for the development environment
kubectl apply -f ../k8s/development/namespace.yaml -n $NAMESPACE
kubectl apply -f ../k8s/development/n8n-deployment.yaml -n $NAMESPACE
kubectl apply -f ../k8s/development/n8n-service.yaml -n $NAMESPACE
kubectl apply -f ../k8s/development/ollama-deployment.yaml -n $NAMESPACE
kubectl apply -f ../k8s/development/ollama-service.yaml -n $NAMESPACE
kubectl apply -f ../k8s/development/redis-deployment.yaml -n $NAMESPACE
kubectl apply -f ../k8s/development/redis-service.yaml -n $NAMESPACE
kubectl apply -f ../k8s/development/neo4j-deployment.yaml -n $NAMESPACE
kubectl apply -f ../k8s/development/neo4j-service.yaml -n $NAMESPACE
kubectl apply -f ../k8s/development/mongodb-deployment.yaml -n $NAMESPACE
kubectl apply -f ../k8s/development/mongodb-service.yaml -n $NAMESPACE
kubectl apply -f ../k8s/development/milvus-deployment.yaml -n $NAMESPACE
kubectl apply -f ../k8s/development/milvus-service.yaml -n $NAMESPACE
kubectl apply -f ../k8s/development/fastapi-deployment.yaml -n $NAMESPACE
kubectl apply -f ../k8s/development/fastapi-service.yaml -n $NAMESPACE
kubectl apply -f ../k8s/development/configmap.yaml -n $NAMESPACE

echo "Development environment deployed successfully."
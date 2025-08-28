#!/bin/bash

# Set the namespace
NAMESPACE="k8s-python-ollama"

# Apply the namespace
kubectl apply -f ../k8s/namespace.yaml

# Deploy FastAPI application
kubectl apply -f ../k8s/fastapi/deployment.yaml -n $NAMESPACE
kubectl apply -f ../k8s/fastapi/service.yaml -n $NAMESPACE
kubectl apply -f ../k8s/fastapi/configmap.yaml -n $NAMESPACE

# Deploy Ollama application
kubectl apply -f ../k8s/ollama/deployment.yaml -n $NAMESPACE
kubectl apply -f ../k8s/ollama/service.yaml -n $NAMESPACE
kubectl apply -f ../k8s/ollama/persistent-volume.yaml -n $NAMESPACE

# Apply Ingress configuration
kubectl apply -f ../k8s/ingress.yaml -n $NAMESPACE

echo "Deployment completed successfully!"
#!/bin/bash

# Cleanup script for Kubernetes resources related to FastAPI and Ollama applications

# Define the namespace
NAMESPACE="your-namespace"  # Change this to your actual namespace

# Delete FastAPI resources
kubectl delete deployment fastapi-deployment -n $NAMESPACE
kubectl delete service fastapi-service -n $NAMESPACE
kubectl delete configmap fastapi-config -n $NAMESPACE

# Delete Ollama resources
kubectl delete deployment ollama-deployment -n $NAMESPACE
kubectl delete service ollama-service -n $NAMESPACE
kubectl delete persistentvolumeclaim ollama-pvc -n $NAMESPACE

# Optionally, delete the namespace
# kubectl delete namespace $NAMESPACE

echo "Cleanup completed."
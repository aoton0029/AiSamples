#!/bin/bash

# Set the namespace
NAMESPACE="production"

# Apply the namespace configuration
kubectl apply -f ../k8s/namespaces/production.yaml

# Deploy the application
kubectl apply -f ../k8s/deployments/app-deployment.yaml -n $NAMESPACE
kubectl apply -f ../k8s/deployments/postgres-deployment.yaml -n $NAMESPACE
kubectl apply -f ../k8s/deployments/redis-deployment.yaml -n $NAMESPACE

# Apply services
kubectl apply -f ../k8s/services/app-service.yaml -n $NAMESPACE
kubectl apply -f ../k8s/services/postgres-service.yaml -n $NAMESPACE
kubectl apply -f ../k8s/services/redis-service.yaml -n $NAMESPACE

# Apply configmaps and secrets
kubectl apply -f ../k8s/configmaps/app-config.yaml -n $NAMESPACE
kubectl apply -f ../k8s/secrets/app-secrets.yaml -n $NAMESPACE

# Apply ingress
kubectl apply -f ../k8s/ingress/app-ingress.yaml -n $NAMESPACE

# Apply persistent volumes
kubectl apply -f ../k8s/persistent-volumes/postgres-pv.yaml -n $NAMESPACE
kubectl apply -f ../k8s/persistent-volumes/redis-pv.yaml -n $NAMESPACE

# Wait for all deployments to be ready
kubectl rollout status deployment/app -n $NAMESPACE
kubectl rollout status deployment/postgres -n $NAMESPACE
kubectl rollout status deployment/redis -n $NAMESPACE

echo "Deployment completed successfully."
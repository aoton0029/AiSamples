#!/bin/bash

echo "Deploying to Persistent Data Cluster..."
kubectl config use-context persistent
kubectl apply -f ../persistent-data/milvus-deployment.yaml
kubectl apply -f ../persistent-data/mongodb-deployment.yaml

echo "Deploying to GPU Cluster..."
kubectl config use-context gpu
kubectl apply -f ../gpu-workloads/ollama-deployment.yaml

echo "Deploying to Microservices Cluster..."
kubectl config use-context microservices
kubectl apply -f ../microservices/n8n-deployment.yaml

echo "Applying cross-cluster networking..."
for context in persistent gpu microservices; do
    kubectl config use-context $context
    kubectl apply -f ../networking/cross-cluster-networking.yaml
done

echo "All deployments completed!"

#!/bin/bash

# Deploy all services across clusters
echo "Deploying services across all clusters..."

# Create namespaces on all clusters
echo "Creating namespaces..."
kubectl --kubeconfig ~/.kube/data-cluster apply -f ../manifests/namespace.yaml
kubectl --kubeconfig ~/.kube/gpu-cluster apply -f ../manifests/namespace.yaml  
kubectl --kubeconfig ~/.kube/service-cluster apply -f ../manifests/namespace.yaml

# Deploy to Data Cluster
echo "Deploying to Data Cluster..."
kubectl --kubeconfig ~/.kube/data-cluster apply -f ../manifests/data-cluster/

# Deploy to GPU Cluster
echo "Deploying to GPU Cluster..."
kubectl --kubeconfig ~/.kube/gpu-cluster apply -f ../manifests/gpu-cluster/

# Deploy to Service Cluster
echo "Deploying to Service Cluster..."
kubectl --kubeconfig ~/.kube/service-cluster apply -f ../manifests/service-cluster/

echo "Deployment complete!"
echo "Access services:"
echo "- N8N: http://n8n.local"
echo "- Neo4j: http://DATA_CLUSTER_IP:30474"
echo "- Ollama: http://GPU_CLUSTER_IP:31434"

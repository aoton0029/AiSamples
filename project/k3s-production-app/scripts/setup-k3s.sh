#!/bin/bash

# This script sets up a k3s Kubernetes cluster

# Update the package index
echo "Updating package index..."
sudo apt-get update

# Install k3s
echo "Installing k3s..."
curl -sfL https://get.k3s.io | sh -

# Check the status of k3s
echo "Checking k3s status..."
sudo systemctl status k3s

# Set kubectl context
echo "Setting kubectl context..."
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

# Verify kubectl installation
echo "Verifying kubectl installation..."
kubectl get nodes

# Create the production namespace
echo "Creating production namespace..."
kubectl apply -f ../k8s/namespaces/production.yaml

echo "k3s setup completed successfully."
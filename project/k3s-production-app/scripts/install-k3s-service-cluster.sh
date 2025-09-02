#!/bin/bash

# Install k3s for Service Cluster (PC3)
echo "Installing k3s for Service Cluster..."

# Install k3s server
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server" \
  K3S_CLUSTER_INIT=true \
  K3S_NODE_NAME=service-master \
  sh -s - \
  --cluster-cidr=10.30.0.0/16 \
  --service-cidr=10.31.0.0/16 \
  --disable=traefik \
  --write-kubeconfig-mode=644

# Install Nginx Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/baremetal/deploy.yaml

echo "Service cluster k3s installation complete!"

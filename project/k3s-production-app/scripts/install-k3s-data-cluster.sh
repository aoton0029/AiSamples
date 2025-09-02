#!/bin/bash

# Install k3s for Data Cluster (PC1)
echo "Installing k3s for Data Cluster..."

# Install k3s server with specific configuration
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server" \
  K3S_CLUSTER_INIT=true \
  K3S_NODE_NAME=data-master \
  sh -s - \
  --cluster-cidr=10.10.0.0/16 \
  --service-cidr=10.11.0.0/16 \
  --disable=traefik \
  --write-kubeconfig-mode=644

# Wait for k3s to be ready
sleep 30

# Install local-path provisioner for persistent storage
kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/master/deploy/local-path-storage.yaml

# Set default storage class
kubectl patch storageclass local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'

echo "Data cluster k3s installation complete!"
echo "Node token is stored in /var/lib/rancher/k3s/server/node-token"

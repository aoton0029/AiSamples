#!/bin/bash

# Install k3s for GPU Cluster (PC2)
echo "Installing k3s for GPU Cluster..."

# Install NVIDIA Container Runtime
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure containerd for GPU
sudo nvidia-ctk runtime configure --runtime=containerd --config=/var/lib/rancher/k3s/agent/etc/containerd/config.toml
sudo systemctl restart k3s-agent

# Install k3s server
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server" \
  K3S_CLUSTER_INIT=true \
  K3S_NODE_NAME=gpu-master \
  sh -s - \
  --cluster-cidr=10.20.0.0/16 \
  --service-cidr=10.21.0.0/16 \
  --disable=traefik \
  --write-kubeconfig-mode=644

# Install NVIDIA Device Plugin
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml

echo "GPU cluster k3s installation complete!"

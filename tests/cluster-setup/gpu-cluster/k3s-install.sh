#!/bin/bash

# Install k3s on GPU cluster
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--cluster-init --node-name gpu-master --cluster-cidr 10.52.0.0/16 --service-cidr 10.53.0.0/16" sh -

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart k3s

# Configure firewall
sudo ufw allow 6443/tcp
sudo ufw allow 2379:2380/tcp
sudo ufw allow 10250/tcp
sudo ufw allow 8472/udp

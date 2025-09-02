#!/bin/bash

# Install k3s on persistent data cluster
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--cluster-init --node-name persistent-master --cluster-cidr 10.42.0.0/16 --service-cidr 10.43.0.0/16" sh -

# Get node token for joining other nodes
sudo cat /var/lib/rancher/k3s/server/node-token > /tmp/k3s-token

# Configure firewall for cross-cluster communication
sudo ufw allow 6443/tcp
sudo ufw allow 2379:2380/tcp
sudo ufw allow 10250/tcp
sudo ufw allow 8472/udp

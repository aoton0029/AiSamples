#!/bin/bash

# Install k3s on microservices cluster
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--cluster-init --node-name microservices-master --cluster-cidr 10.62.0.0/16 --service-cidr 10.63.0.0/16" sh -

# Configure firewall
sudo ufw allow 6443/tcp
sudo ufw allow 2379:2380/tcp
sudo ufw allow 10250/tcp
sudo ufw allow 8472/udp

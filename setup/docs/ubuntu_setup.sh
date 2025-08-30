#!/bin/bash
PASSWORD="0418"
COMMIT_ID="6f17636121051a53c88d3e605c491d22af2ba755"

echo $PASSWORD | sudo -S apt update
sudo -S apt upgrade -y
sudo apt-get install \
    ca-certificates \
    curl \
    wget \
    gnupg \
    lsb-release \
    nano \
    openssh-server \
    tar \
    #build-essential

#Docker
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt-get update
sudo groupadd docker
sudo usermod -aG docker $USER
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

#Docker Compose
sudo apt install -y docker-compose-plugin

#nvidia container toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt install -y nvidia-container-toolkit

# git
sudo apt install -y git

# vscode-server
VSCODE_SERVER_DIR="$HOME/.vscode-server/bin/$COMMIT_ID"
mkdir -p "$VSCODE_SERVER_DIR"
cd "$VSCODE_SERVER_DIR"
wget "https://update.code.visualstudio.com/commit:$COMMIT_ID/server-linux-x64/stable" -O vscode-server.tar.gz
tar -xzf vscode-server.tar.gz
rm vscode-server.tar.gz

sudo apt-get install -y uidmap dbus-user-session

# kubernetes
sudo curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644

# kubectl
curl -LO "https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x ./kubectl
sudo mv ./kubectl /usr/local/bin/kubectl

# nerdctl
curl -OL https://github.com/containerd/nerdctl/releases/download/v2.1.1/nerdctl-2.1.1-linux-amd64.tar.gz
sudo tar Cxzvvf /usr/local/bin nerdctl-2.1.1-linux-amd64.tar.gz
containerd-rootless-setuptool.sh install

# CNIプラグイン
curl -OL https://github.com/containernetworking/plugins/releases/download/v1.7.1/cni-plugins-linux-amd64-v1.7.1.tgz
sudo mkdir -p /opt/cni/bin/
sudo tar Cxzvvf /opt/cni/bin cni-plugins-linux-amd64-v1.7.1.tgz

# buildkit
curl -OL https://github.com/moby/buildkit/releases/download/v0.21.1/buildkit-v0.21.1.linux-amd64.tar.gz
sudo tar Cxzvvf /usr/local/ buildkit-v0.21.1.linux-amd64.tar.gz
CONTAINERD_NAMESPACE=default containerd-rootless-setuptool.sh install-buildkit-containerd

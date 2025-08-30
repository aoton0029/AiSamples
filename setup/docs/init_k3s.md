
# k3s, kubectl, and nerdctl Installation Guide

This document provides instructions for installing k3s, kubectl, and nerdctl on Ubuntu.

## Installing k3s

To install k3s, run the following command:

```bash
sudo curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644
```

## Installing kubectl

To install kubectl, you can use the following script:

```bash
# Download the latest release
curl -LO "https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl"

# Make the kubectl binary executable
chmod +x ./kubectl

# Move the binary to your PATH
sudo mv ./kubectl /usr/local/bin/kubectl
```

## Installing nerdctl

To install nerdctl, use the following script:

```bash
# Download the latest release
curl -LO https://github.com/nerdctl/nerdctl/releases/latest/download/nerdctl-$(uname -s)-$(uname -m).tar.gz

# Extract the tarball
tar xzvf nerdctl-*.tar.gz

# Move the binary to your PATH
sudo mv nerdctl /usr/local/bin/
```

## Additional Resources

- [k3s Documentation](https://rancher.com/docs/k3s/latest/en/)
- [kubectl Documentation](https://kubernetes.io/docs/reference/kubectl/overview/)
- [nerdctl Documentation](https://github.com/nerdctl/nerdctl)
- https://qiita.com/t5693_g/items/ff908b84860e0929c6d5
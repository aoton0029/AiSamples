#!/bin/bash

# Configure kubectl contexts for all clusters
kubectl config set-cluster persistent --server=https://PERSISTENT_CLUSTER_IP:6443 --insecure-skip-tls-verify=true
kubectl config set-cluster gpu --server=https://GPU_CLUSTER_IP:6443 --insecure-skip-tls-verify=true
kubectl config set-cluster microservices --server=https://MICROSERVICES_CLUSTER_IP:6443 --insecure-skip-tls-verify=true

# Set credentials (replace with actual tokens)
kubectl config set-credentials persistent-admin --token=PERSISTENT_CLUSTER_TOKEN
kubectl config set-credentials gpu-admin --token=GPU_CLUSTER_TOKEN
kubectl config set-credentials microservices-admin --token=MICROSERVICES_CLUSTER_TOKEN

# Set contexts
kubectl config set-context persistent --cluster=persistent --user=persistent-admin
kubectl config set-context gpu --cluster=gpu --user=gpu-admin
kubectl config set-context microservices --cluster=microservices --user=microservices-admin

# Switch between clusters using:
# kubectl config use-context persistent
# kubectl config use-context gpu
# kubectl config use-context microservices

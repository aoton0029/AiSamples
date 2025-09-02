#!/bin/bash

echo "Setting up monitoring across all clusters..."

# Create monitoring namespace on all clusters
kubectl --kubeconfig ~/.kube/data-cluster create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
kubectl --kubeconfig ~/.kube/gpu-cluster create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
kubectl --kubeconfig ~/.kube/service-cluster create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Deploy node-exporter on all clusters
echo "Deploying node-exporter..."
kubectl --kubeconfig ~/.kube/data-cluster apply -f ../manifests/monitoring/node-exporter-daemonset.yaml
kubectl --kubeconfig ~/.kube/gpu-cluster apply -f ../manifests/monitoring/node-exporter-daemonset.yaml
kubectl --kubeconfig ~/.kube/service-cluster apply -f ../manifests/monitoring/node-exporter-daemonset.yaml

# Deploy Prometheus on service cluster (central monitoring)
echo "Deploying Prometheus..."
kubectl --kubeconfig ~/.kube/service-cluster apply -f ../manifests/monitoring/prometheus-deployment.yaml

# Deploy Grafana
echo "Deploying Grafana..."
kubectl --kubeconfig ~/.kube/service-cluster apply -f ../manifests/monitoring/grafana-deployment.yaml

# Deploy AlertManager
echo "Deploying AlertManager..."
kubectl --kubeconfig ~/.kube/service-cluster apply -f ../manifests/monitoring/alertmanager-deployment.yaml

echo "Monitoring setup complete!"
echo "Access URLs:"
echo "- Grafana: http://SERVICE_CLUSTER_IP:30300 (admin/admin)"
echo "- Prometheus: http://SERVICE_CLUSTER_IP:30090"
echo "- AlertManager: http://SERVICE_CLUSTER_IP:30093"

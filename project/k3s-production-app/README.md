# Project Documentation

## Overview

This project is designed to provide a comprehensive solution for managing AI workloads on Kubernetes. It includes tools for orchestration, monitoring, and data management, ensuring a robust and scalable environment for AI development and production.

## Data Backup & Recovery

### Automated Backups
- Daily backups at 2 AM for all databases
- Redis: RDB snapshots
- MongoDB: mongodump
- Neo4j: Native backup export
- Milvus: MinIO bucket sync

### Manual Backup/Restore
```bash
# Backup all services
./scripts/backup-restore.sh backup all

# Restore specific service
./scripts/backup-restore.sh restore redis 2024-01-15

# List available backups
./scripts/backup-restore.sh list
```

## Monitoring & Alerting

### Components
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization dashboards
- **AlertManager**: Alert routing and notification
- **Node Exporter**: System metrics on all nodes

### Access URLs
- Grafana: http://SERVICE_CLUSTER_IP:30300 (admin/admin)
- Prometheus: http://SERVICE_CLUSTER_IP:30090
- AlertManager: http://SERVICE_CLUSTER_IP:30093

### Setup Monitoring
```bash
./scripts/setup-monitoring.sh
```

### Key Metrics Monitored
- Database availability and performance
- Node resource usage (CPU, Memory, Disk)
- Network connectivity between clusters
- Container health and restart counts
- GPU utilization on AI cluster

### Alert Configurations
- Critical: Database down, disk space < 10%
- Warning: High memory usage > 85%
- Info: Backup job completion status

## Troubleshooting

### Common Issues
- **Database connection errors**: Check if the database service is running and accessible.
- **Insufficient resources**: Ensure the node has enough CPU and memory allocated.
- **Network issues**: Verify the network policies and connectivity between pods.

### Logs
- Application logs: Located in the respective pod's log
- System logs: Accessible via `kubectl logs` command

### Support
For further assistance, please contact the support team or refer to the [Kubernetes documentation](https://kubernetes.io/docs/home/).
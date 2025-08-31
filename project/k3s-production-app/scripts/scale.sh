#!/bin/bash

# Scale the application deployment in Kubernetes

# Usage: ./scale.sh <deployment_name> <replica_count>

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <deployment_name> <replica_count>"
    exit 1
fi

DEPLOYMENT_NAME=$1
REPLICA_COUNT=$2

# Scale the deployment
kubectl scale deployment "$DEPLOYMENT_NAME" --replicas="$REPLICA_COUNT" -n production

# Check the status of the deployment
kubectl rollout status deployment "$DEPLOYMENT_NAME" -n production

echo "Scaled deployment '$DEPLOYMENT_NAME' to $REPLICA_COUNT replicas."
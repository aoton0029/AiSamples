#!/bin/bash

OPERATION=$1
SERVICE=$2
DATE=$3

usage() {
    echo "Usage: $0 [backup|restore|list] [redis|mongodb|neo4j|milvus|all] [YYYY-MM-DD]"
    echo "Examples:"
    echo "  $0 backup all"
    echo "  $0 restore redis 2024-01-15"
    echo "  $0 list"
    exit 1
}

if [ -z "$OPERATION" ]; then
    usage
fi

case $OPERATION in
    "backup")
        if [ -z "$SERVICE" ]; then
            usage
        fi
        
        echo "Starting backup for $SERVICE..."
        kubectl --kubeconfig ~/.kube/data-cluster create job manual-backup-$(date +%s) \
            --from=cronjob/daily-backup -n data-services
        
        echo "Backup job created. Check status with:"
        echo "kubectl --kubeconfig ~/.kube/data-cluster get jobs -n data-services"
        ;;
        
    "restore")
        if [ -z "$SERVICE" ] || [ -z "$DATE" ]; then
            usage
        fi
        
        echo "Restoring $SERVICE from backup date $DATE..."
        echo "WARNING: This will overwrite existing data!"
        read -p "Are you sure? (y/N): " confirm
        
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            kubectl --kubeconfig ~/.kube/data-cluster exec -it \
                $(kubectl --kubeconfig ~/.kube/data-cluster get pod -l app=backup -o jsonpath='{.items[0].metadata.name}' -n data-services) \
                -n data-services -- /scripts/restore-$SERVICE.sh $DATE
        else
            echo "Restore cancelled."
        fi
        ;;
        
    "list")
        echo "Available backups:"
        kubectl --kubeconfig ~/.kube/data-cluster exec -it \
            $(kubectl --kubeconfig ~/.kube/data-cluster get pod -l app=backup -o jsonpath='{.items[0].metadata.name}' -n data-services) \
            -n data-services -- ls -la /backups/
        ;;
        
    *)
        usage
        ;;
esac

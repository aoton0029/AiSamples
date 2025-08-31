
## バックアップ
```
docker compose --profile backup up
```

## 最新のバックアップからリストア
```
docker compose --profile restore up
```

## 特定のファイルからリストア
```
BACKUP_FILE=postgres_backup_20250831_120000.sql docker compose up postgres-restore
BACKUP_DIR=mongodb_backup_20250831_120000 docker compose up mongodb-restore
```

```
mkdir -p backups/{postgres,neo4j,redis,mongodb}
```


# DB
- KV_STORAGE Redis
- GRAPH_STORAGE Neo4J
- VECTOR_STORAGE Milvus
- DOC_STATUS_STORAGE MongoDB
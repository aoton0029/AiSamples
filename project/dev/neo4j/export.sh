docker build -f Dockerfile.neo4j -t neo4j-with-plugins:latest .
docker save neo4j-with-plugins:latest -o neo4j-with-plugins.tar
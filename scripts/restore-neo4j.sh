#!/bin/bash

# Script to restore Neo4j database from backup using official Neo4j documentation method

echo "Starting Neo4j database restore..."

# Check if backup file exists
if [ ! -f "backend/Data/neo4j.dump" ]; then
    echo "Error: Backup file backend/Data/neo4j.dump not found!"
    exit 1
fi

echo "Found backup file: backend/Data/neo4j.dump"

# Get the correct volume name (it should be chatbot-rag_neo4j_data)
VOLUME_NAME=$(docker volume ls | grep "chatbot-rag_neo4j_data" | awk '{print $2}')
if [ -z "$VOLUME_NAME" ]; then
    echo "Error: chatbot-rag_neo4j_data volume not found!"
    echo "Available volumes:"
    docker volume ls
    exit 1
fi

echo "Found Neo4j volume: $VOLUME_NAME"

# Stop the Neo4j container
echo "Stopping Neo4j container..."
docker stop chatbot-neo4j 2>/dev/null || true

# Wait for container to fully stop
sleep 5

# Load database using neo4j-admin 
echo "Loading database from dump file..."
docker run --interactive --tty --rm \
    -e NEO4J_ACCEPT_LICENSE_AGREEMENT=eval \
    --volume="$VOLUME_NAME":/data \
    --volume="$(pwd)/backend/Data":/backups \
    neo4j:2025.07-enterprise \
    neo4j-admin database load neo4j --from-path=/backups --overwrite-destination=true

if [ $? -eq 0 ]; then
    echo "Database load completed successfully!"
else
    echo "Error: Database load failed!"
    exit 1
fi

# Start the Neo4j container
echo "Starting Neo4j container..."
docker start chatbot-neo4j

# Wait for Neo4j to be ready
echo "Waiting for Neo4j to start..."
sleep 15

# Verify the restore
echo "Verifying database restore..."
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if docker exec chatbot-neo4j cypher-shell -u neo4j -p 12345678 "CALL db.ping()" >/dev/null 2>&1; then
        NODE_COUNT=$(docker exec chatbot-neo4j cypher-shell -u neo4j -p 12345678 "MATCH (n) RETURN count(n) as node_count" 2>/dev/null | grep -E '^[0-9]+$' | head -1)
        if [ ! -z "$NODE_COUNT" ] && [ "$NODE_COUNT" -gt 0 ]; then
            echo "Database restore verified successfully! Node count: $NODE_COUNT"
            break
        else
            echo "Database is running but no nodes found. Node count: $NODE_COUNT"
        fi
    fi
    echo "Waiting for Neo4j to be ready... ($counter/$timeout)"
    sleep 5
    counter=$((counter + 5))
done

if [ $counter -ge $timeout ]; then
    echo "Warning: Could not verify database restore within $timeout seconds"
    echo "You can manually check by running:"
    echo "docker exec chatbot-neo4j cypher-shell -u neo4j -p 12345678 \"MATCH (n) RETURN count(n) as node_count\""
fi

echo "Neo4j restore process completed!"

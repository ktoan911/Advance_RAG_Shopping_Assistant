#!/bin/bash

# Script to set up and launch the entire project

echo "=== Starting Chatbot-RAG ==="

# Check Docker and Docker Compose
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed!"
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo "Error: Docker Compose is not installed!"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p backend/logs

# Stop any existing containers and clean up
echo "Cleaning up existing containers..."
docker compose down -v

# Build and start services
echo "Building and starting services..."
docker compose up -d

# Wait for Neo4j to fully start
echo "Waiting for Neo4j to start..."
sleep 30

# Check if Neo4j container is running
echo "Checking Neo4j container status..."
if ! docker ps | grep -q chatbot-neo4j; then
    echo "Error: Neo4j container is not running!"
    echo "Checking logs..."
    docker compose logs neo4j
    exit 1
fi

# Wait for Neo4j to be healthy
echo "Waiting for Neo4j to be healthy..."
timeout=120
counter=0
while [ $counter -lt $timeout ]; do
    if docker exec chatbot-neo4j cypher-shell -u neo4j -p 12345678 "CALL db.ping()" >/dev/null 2>&1; then
        echo "Neo4j is ready!"
        break
    fi
    echo "Waiting for Neo4j to be ready... ($counter/$timeout)"
    sleep 5
    counter=$((counter + 5))
done

if [ $counter -ge $timeout ]; then
    echo "Error: Neo4j did not become ready within $timeout seconds"
    docker compose logs neo4j
    exit 1
fi

# Restore Neo4j data
echo "Restoring Neo4j data..."
chmod +x scripts/restore-neo4j.sh
./scripts/restore-neo4j.sh

echo  "Restart backend"
docker compose restart backend

# Check status of services
echo "Checking status of services..."
docker compose ps

echo ""
echo "=== Project has been successfully started! ==="
echo "Frontend: http://localhost"
echo "Backend API: http://localhost:5000"
echo "Neo4j Browser: http://localhost:7474"
echo "Neo4j credentials: neo4j/12345678"
echo ""
echo "To view logs: docker compose logs -f [service_name]"
echo "To stop: docker compose down"
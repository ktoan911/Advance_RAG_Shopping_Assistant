# Guide to Running Chatbot-RAG with Docker

## System Requirements

- Docker
- Docker Compose
- 4GB free RAM (8GB recommended)
- 10GB disk space

## Usage Instructions

### 1. Preparation

```bash
# Clone project (if not already)
git clone <repository-url>
cd Chatbot-RAG

# Update API keys in the .env file (create this file if it doesn't exist)
cp .env.example .env
# Edit .env with your actual API keys
```

### 2. Automatic Startup (Recommended)

```bash
# Grant execute permission to scripts
chmod +x scripts/*.sh

# Run the auto setup script
./scripts/setup.sh
```

### 3. Manual Startup

```bash
# Build and start services
docker compose up -d --build

# Wait for Neo4j to start (about 1-2 minutes)
docker compose logs -f neo4j

# Restore Neo4j data
./scripts/restore-neo4j.sh
```

## Accessing the Application

- **Frontend**: http://localhost
- **Backend API**: http://localhost:5000
- **Neo4j Browser**: http://localhost:7474
  - Username: `neo4j`
  - Password: `12345678`

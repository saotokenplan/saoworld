#!/bin/bash
set -e

echo "=== Game Server Deployment Script ==="

DEPLOY_DIR="/opt/game-server"
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env"

if [ -z "$1" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

VERSION="$1"
echo "Deploying version: $VERSION"

if [ ! -d "$DEPLOY_DIR" ]; then
    echo "Creating deploy directory..."
    mkdir -p "$DEPLOY_DIR"
    cd "$DEPLOY_DIR"
    git init
    git remote add origin git@github.com:example/game-server.git
    git pull origin main
else
    cd "$DEPLOY_DIR"
    echo "Pulling latest code..."
    git pull origin main
fi

echo "Updating IMAGE_VERSION to $VERSION..."
sed -i "s/IMAGE_VERSION=.*/IMAGE_VERSION=$VERSION/" "$ENV_FILE"

echo "Starting services..."
docker compose -f "$DOCKER_COMPOSE_FILE" up -d

echo "Waiting for services to start..."
sleep 30

echo "Running health checks..."
curl -s http://localhost:8080/api/v1/health || echo "Health check failed"

echo "Deployment completed for version $VERSION"
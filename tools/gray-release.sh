#!/bin/bash
set -e

echo "=== Game Server Gray Release Script ==="

DEPLOY_DIR="/opt/game-server-gray"
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env"
GRAY_SCOPE_FILE="gray_scope.json"

if [ -z "$1" ]; then
    echo "Usage: $0 <version> [region_ids] [player_percent] [player_ids]"
    echo "Example: $0 1.0.0 'region_wasteland_01' 10 ''"
    exit 1
fi

VERSION="$1"
REGION_IDS="${2:-}"
PLAYER_PERCENT="${3:-10}"
PLAYER_IDS="${4:-}"

echo "Deploying version: $VERSION (Gray Release)"

if [ ! -d "$DEPLOY_DIR" ]; then
    echo "Creating gray deploy directory..."
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

echo "Configuring gray scope..."
cat > "$GRAY_SCOPE_FILE" << EOF
{
  "region_ids": ["${REGION_IDS//,/\",\"}"],
  "player_percent": ${PLAYER_PERCENT},
  "player_ids": ["${PLAYER_IDS//,/\",\"}"]
}
EOF

echo "Starting gray services..."
docker compose -f "$DOCKER_COMPOSE_FILE" up -d

echo "Waiting for services to start..."
sleep 30

echo "Running health checks..."
bash tools/health-check.sh

echo "=== Gray release completed for version $VERSION ==="
echo "Gray scope: ${PLAYER_PERCENT}% of players"
if [ -n "$REGION_IDS" ]; then
    echo "Target regions: $REGION_IDS"
fi
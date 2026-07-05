#!/bin/bash
set -e

echo "=== Game Server Rollback Script ==="

DEPLOY_DIR="/opt/game-server"
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env"
ROLLBACK_LOG="rollback_log.txt"

cd "$DEPLOY_DIR"

CURRENT_VERSION=$(grep IMAGE_VERSION "$ENV_FILE" | cut -d'=' -f2)
echo "Current version: $CURRENT_VERSION"

PREV_VERSION=$(git describe --abbrev=0 --tags $(git rev-list --tags --skip=1 --max-count=1))
PREV_VERSION=${PREV_VERSION#v}
echo "Rolling back to: $PREV_VERSION"

echo "=== Recording rollback ==="
cat >> "$ROLLBACK_LOG" << EOF
$(date -u) - Rollback from $CURRENT_VERSION to $PREV_VERSION
EOF

echo "Updating IMAGE_VERSION to $PREV_VERSION..."
sed -i "s/IMAGE_VERSION=.*/IMAGE_VERSION=$PREV_VERSION/" "$ENV_FILE"

echo "Restarting services..."
docker compose -f "$DOCKER_COMPOSE_FILE" up -d

echo "Waiting for services to start..."
sleep 30

echo "Running health checks..."
if bash tools/health-check.sh; then
    echo "Rollback completed successfully to version $PREV_VERSION"
    cat >> "$ROLLBACK_LOG" << EOF
$(date -u) - Rollback successful
EOF
    exit 0
else
    echo "Health checks failed after rollback!"
    cat >> "$ROLLBACK_LOG" << EOF
$(date -u) - Rollback failed - health checks not passing
EOF
    exit 1
fi
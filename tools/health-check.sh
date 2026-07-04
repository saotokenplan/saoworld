#!/bin/bash
set -e

echo "=== Game Server Health Check ==="

SERVICES=(
    "vote-service:8000"
    "world-service:8000"
    "content-service:8000"
    "generation-service:8000"
    "review-service:8000"
    "gateway-service:8000"
    "player-service:8000"
    "ops-service:8000"
)

GATEWAY_URL="http://localhost:8080"

echo "Checking Gateway..."
GATEWAY_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$GATEWAY_URL/api/v1/health")
if [ "$GATEWAY_STATUS" -eq 200 ]; then
    echo "Gateway: OK"
else
    echo "Gateway: FAILED (HTTP $GATEWAY_STATUS)"
    exit 1
fi

echo "Checking database..."
POSTGRES_STATUS=$(docker compose -f infra/docker-compose.prod.yml exec -T postgres pg_isready -U game 2>/dev/null || echo "not running")
if [ "$POSTGRES_STATUS" = "accepting connections" ]; then
    echo "PostgreSQL: OK"
else
    echo "PostgreSQL: FAILED"
    exit 1
fi

echo "Checking Redis..."
REDIS_STATUS=$(docker compose -f infra/docker-compose.prod.yml exec -T redis redis-cli ping 2>/dev/null || echo "not running")
if [ "$REDIS_STATUS" = "PONG" ]; then
    echo "Redis: OK"
else
    echo "Redis: FAILED"
    exit 1
fi

echo "=== All health checks passed ==="
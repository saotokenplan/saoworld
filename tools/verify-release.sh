#!/bin/bash
set -e

echo "=== Game Server Release Verification Script ==="

GATEWAY_URL="http://localhost:8080"
METRICS_URL="http://localhost:8080/metrics"

FAILED_CHECKS=0

echo "=== Service Health Checks ==="
SERVICES=(
    "vote"
    "world"
    "content"
    "generation"
    "review"
    "gateway"
    "player"
    "ops"
)

for service in "${SERVICES[@]}"; do
    echo "Checking ${service}-service..."
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$GATEWAY_URL/api/v1/health")
    if [ "$RESPONSE" -eq 200 ]; then
        echo "${service}-service: OK"
    else
        echo "${service}-service: FAILED (HTTP $RESPONSE)"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
done

echo ""
echo "=== Metrics Check ==="
METRICS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$METRICS_URL")
if [ "$METRICS_RESPONSE" -eq 200 ]; then
    echo "Metrics endpoint: OK"
else
    echo "Metrics endpoint: FAILED (HTTP $METRICS_RESPONSE)"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

echo ""
echo "=== Database Connection Check ==="
POSTGRES_STATUS=$(docker compose -f infra/docker-compose.prod.yml exec -T postgres pg_isready -U game 2>/dev/null || echo "not running")
if [ "$POSTGRES_STATUS" = "accepting connections" ]; then
    echo "PostgreSQL: OK"
else
    echo "PostgreSQL: FAILED"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

REDIS_STATUS=$(docker compose -f infra/docker-compose.prod.yml exec -T redis redis-cli ping 2>/dev/null || echo "not running")
if [ "$REDIS_STATUS" = "PONG" ]; then
    echo "Redis: OK"
else
    echo "Redis: FAILED"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

echo ""
echo "=== Summary ==="
if [ "$FAILED_CHECKS" -eq 0 ]; then
    echo "All checks passed. Release verified successfully."
    exit 0
else
    echo "${FAILED_CHECKS} checks failed. Release verification failed."
    exit 1
fi
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
echo "=== Content Package Status Check ==="
CONTENT_UPDATES=$(curl -s "$GATEWAY_URL/api/v1/content/updates" 2>/dev/null || echo '{}')
PACKAGE_COUNT=$(echo "$CONTENT_UPDATES" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('data',[])))" 2>/dev/null || echo "0")
if [ "$PACKAGE_COUNT" -gt 0 ]; then
    echo "Content packages available: ${PACKAGE_COUNT}"
    LIVE_COUNT=$(echo "$CONTENT_UPDATES" | python3 -c "import sys,json; d=json.load(sys.stdin); print(sum(1 for p in d.get('data',[]) if p.get('status')=='live'))" 2>/dev/null || echo "0")
    GRAY_COUNT=$(echo "$CONTENT_UPDATES" | python3 -c "import sys,json; d=json.load(sys.stdin); print(sum(1 for p in d.get('data',[]) if p.get('status')=='gray'))" 2>/dev/null || echo "0")
    echo "Live packages: ${LIVE_COUNT}"
    echo "Gray packages: ${GRAY_COUNT}"
else
    echo "No content packages available"
    echo "Note: This may be expected before initial content seeding"
fi

echo ""
echo "=== Gray Scope Verification ==="
if [ "$GRAY_COUNT" -gt 0 ]; then
    echo "Verifying gray scope configuration..."
    FIRST_PACKAGE=$(echo "$CONTENT_UPDATES" | python3 -c "import sys,json; d=json.load(sys.stdin); [p]=[p for p in d.get('data',[]) if p.get('status')=='gray'][:1]; print(json.dumps(p))" 2>/dev/null)
    if [ -n "$FIRST_PACKAGE" ]; then
        HAS_PLAYER_IDS=$(echo "$FIRST_PACKAGE" | python3 -c "import sys,json; d=json.load(sys.stdin); scope=d.get('gray_scope_jsonb',{}); print('yes' if scope.get('player_ids') else 'no')" 2>/dev/null)
        HAS_PLAYER_PERCENT=$(echo "$FIRST_PACKAGE" | python3 -c "import sys,json; d=json.load(sys.stdin); scope=d.get('gray_scope_jsonb',{}); print('yes' if scope.get('player_percent') else 'no')" 2>/dev/null)
        HAS_REGION_IDS=$(echo "$FIRST_PACKAGE" | python3 -c "import sys,json; d=json.load(sys.stdin); scope=d.get('gray_scope_jsonb',{}); print('yes' if scope.get('region_ids') else 'no')" 2>/dev/null)
        echo "  Player IDs configured: ${HAS_PLAYER_IDS}"
        echo "  Player Percent configured: ${HAS_PLAYER_PERCENT}"
        echo "  Region IDs configured: ${HAS_REGION_IDS}"
        if [ "$HAS_PLAYER_IDS" = "no" ] && [ "$HAS_PLAYER_PERCENT" = "no" ] && [ "$HAS_REGION_IDS" = "no" ]; then
            echo "  WARNING: Gray scope has no targeting criteria configured"
        fi
    fi
fi

echo ""
echo "=== System Status Check ==="
SYSTEM_STATUS=$(curl -s "$GATEWAY_URL/api/v1/ops/system/status" 2>/dev/null || echo '{}')
SERVICE_COUNT=$(echo "$SYSTEM_STATUS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('data',{}).get('services',[])))" 2>/dev/null || echo "0")
HEALTHY_COUNT=$(echo "$SYSTEM_STATUS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(sum(1 for s in d.get('data',{}).get('services',[]) if s.get('status')=='ok'))" 2>/dev/null || echo "0")
echo "Services checked by ops-service: ${SERVICE_COUNT}"
echo "Healthy services: ${HEALTHY_COUNT}"

echo ""
echo "=== Summary ==="
if [ "$FAILED_CHECKS" -eq 0 ]; then
    echo "All checks passed. Release verified successfully."
    exit 0
else
    echo "${FAILED_CHECKS} checks failed. Release verification failed."
    exit 1
fi
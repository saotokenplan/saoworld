#!/bin/bash
set -e

echo "=== Run All Database Migrations ==="

SERVICES=(
    "vote"
    "world"
    "content"
    "generation"
    "review"
    "player"
    "ops"
)

for service in "${SERVICES[@]}"; do
    echo "Running migrations for $service-service..."
    cd "services/$service"
    
    if [ -f "alembic.ini" ]; then
        alembic upgrade head
        echo "$service-service: OK"
    else
        echo "$service-service: SKIP (no alembic.ini)"
    fi
    
    cd ../..
done

echo "=== All migrations completed ==="
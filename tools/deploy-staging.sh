#!/bin/bash

set -e

echo "=================================="
echo "  Staging 环境部署脚本"
echo "=================================="

STAGE="$1"
if [ -z "$STAGE" ]; then
    STAGE="staging"
fi

echo "部署环境: $STAGE"
echo "当前目录: $(pwd)"

DOCKER_COMPOSE_FILE="infra/docker-compose.prod.yml"

if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    echo "错误: 找不到 $DOCKER_COMPOSE_FILE"
    exit 1
fi

echo ""
echo "步骤 1: 停止现有服务..."
cd "$(dirname "$0")/.."
docker compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans

echo ""
echo "步骤 2: 拉取最新代码..."
git fetch origin
git checkout feature-prd
git pull origin feature-prd

echo ""
echo "步骤 3: 构建服务镜像..."
echo "(注: 生产环境使用预构建镜像, 此步骤仅用于本地构建测试)"

echo ""
echo "步骤 4: 启动服务..."
docker compose -f "$DOCKER_COMPOSE_FILE" up -d

echo ""
echo "步骤 5: 等待服务启动..."
sleep 30

echo ""
echo "步骤 6: 健康检查..."

echo "--- PostgreSQL ---"
if docker compose -f "$DOCKER_COMPOSE_FILE" exec postgres pg_isready -U game; then
    echo "✓ PostgreSQL 健康"
else
    echo "✗ PostgreSQL 不健康"
    exit 1
fi

echo "--- Redis ---"
if docker compose -f "$DOCKER_COMPOSE_FILE" exec redis redis-cli ping | grep -q PONG; then
    echo "✓ Redis 健康"
else
    echo "✗ Redis 不健康"
    exit 1
fi

echo "--- Gateway Service ---"
GATEWAY_STATUS=$(curl -s http://localhost:8080/api/v1/health || echo "{}")
if echo "$GATEWAY_STATUS" | grep -q '"status": "ok"'; then
    echo "✓ Gateway Service 健康"
else
    echo "✗ Gateway Service 不健康"
    echo "响应: $GATEWAY_STATUS"
fi

echo ""
echo "步骤 7: 服务状态汇总..."
docker compose -f "$DOCKER_COMPOSE_FILE" ps

echo ""
echo "=================================="
echo "  部署完成"
echo "=================================="
echo ""
echo "服务访问地址:"
echo "  API Gateway: http://localhost:8080"
echo "  Prometheus: http://localhost:9090"
echo "  Grafana: http://localhost:3000"
echo ""
echo "使用以下命令查看日志:"
echo "  docker compose -f $DOCKER_COMPOSE_FILE logs -f <service-name>"
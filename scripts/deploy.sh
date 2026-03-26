#!/bin/bash
# Nova Test 部署脚本
# 使用方法: ./deploy.sh [environment]

set -e

ENV=${1:-dev}
TAG=${2:-latest}
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "Nova Test 部署脚本"
echo "环境: $ENV"
echo "版本: $TAG"
echo "=========================================="

# 构建 Docker 镜像
echo "[1/4] 构建 Docker 镜像..."
docker build -t nova-test/executor:$TAG ./executor-python

# 推送镜像 (可选)
if [ "$ENV" == "prod" ]; then
    echo "[2/4] 推送镜像..."
    docker tag nova-test/executor:$TAG registry.example.com/nova-test/executor:$TAG
    docker push registry.example.com/nova-test/executor:$TAG
fi

# 启动服务
echo "[3/4] 启动服务..."
docker-compose -f docker-compose.yml up -d

# 健康检查
echo "[4/4] 健康检查..."
sleep 5
curl -f http://localhost:8002/health || exit 1

echo "=========================================="
echo "部署完成!"
echo "Executor: http://localhost:8002"
echo "API 文档: http://localhost:8002/docs"
echo "=========================================="

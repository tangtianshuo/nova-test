#!/bin/bash
# Nova Test 部署脚本
# 使用方法: ./deploy.sh [environment] [tag] [--skip-tests] [--skip-security]

set -e

ENV=${1:-dev}
TAG=${2:-latest}
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$PROJECT_DIR"
EXECUTOR_DIR="$PROJECT_DIR/executor-python"

SKIP_TESTS=false
SKIP_SECURITY=false

for arg in "$@"; do
    case $arg in
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --skip-security)
            SKIP_SECURITY=true
            shift
            ;;
    esac
done

echo "=========================================="
echo "Nova Test 部署脚本"
echo "环境: $ENV"
echo "版本: $TAG"
echo "跳过测试: $SKIP_TESTS"
echo "跳过安全扫描: $SKIP_SECURITY"
echo "=========================================="

check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "错误: 命令 '$1' 未找到"
        exit 1
    fi
}

echo "[0/8] 检查依赖..."
check_command docker
check_command docker-compose
check_command curl

if [ "$SKIP_TESTS" = false ]; then
    echo "[准备] 准备运行测试..."

    if [ -f "$FRONTEND_DIR/package.json" ]; then
        check_command npm
        echo "  - npm 可用 (前端测试)"
    fi

    if [ -f "$EXECUTOR_DIR/pyproject.toml" ]; then
        check_command python3
        echo "  - python3 可用 (后端测试)"
    fi
fi

if [ "$SKIP_SECURITY" = false ]; then
    echo "[准备] 准备运行安全扫描..."

    if [ -f "$EXECUTEND_DIR/package.json" ]; then
        check_command npm
    fi

    if [ -f "$EXECUTOR_DIR/pyproject.toml" ]; then
        check_command python3
    fi
fi

echo "=========================================="
echo "依赖检查完成"
echo "=========================================="

if [ "$SKIP_TESTS" = false ]; then
    echo "[1/8] 运行前端测试 (可选)..."
    if [ -f "$FRONTEND_DIR/package.json" ]; then
        echo "  运行 npm test..."
        cd "$FRONTEND_DIR"
        if npm test -- --run 2>/dev/null; then
            echo "  ✓ 前端测试通过"
        else
            echo "  ! 前端测试失败，继续部署..."
        fi
        cd "$PROJECT_DIR"
    fi

    echo "[2/8] 运行后端测试 (可选)..."
    if [ -f "$EXECUTOR_DIR/pyproject.toml" ]; then
        echo "  运行 pytest..."
        cd "$EXECUTOR_DIR"
        if python3 -m pytest tests/ -v --tb=short 2>/dev/null; then
            echo "  ✓ 后端测试通过"
        else
            echo "  ! 后端测试失败，继续部署..."
        fi
        cd "$PROJECT_DIR"
    fi
else
    echo "[1/8] 跳过测试"
    echo "[2/8] 跳过测试"
fi

if [ "$SKIP_SECURITY" = false ]; then
    echo "[3/8] 运行安全扫描..."

    SECURITY_ISSUES=0

    if [ -f "$FRONTEND_DIR/package.json" ]; then
        echo "  运行 npm audit..."
        cd "$FRONTEND_DIR"
        if npm audit --audit-level=moderate 2>/dev/null; then
            echo "  ✓ npm audit 通过"
        else
            echo "  ! 发现 npm 安全问题"
            SECURITY_ISSUES=$((SECURITY_ISSUES + 1))
        fi
        cd "$PROJECT_DIR"
    fi

    if [ -f "$FRONTEND_DIR/.eslintrc.js" ] || [ -f "$FRONTEND_DIR/eslint.config.js" ]; then
        echo "  运行 ESLint..."
        cd "$FRONTEND_DIR"
        if npm run lint 2>/dev/null; then
            echo "  ✓ ESLint 通过"
        else
            echo "  ! ESLint 发现问题"
            SECURITY_ISSUES=$((SECURITY_ISSUES + 1))
        fi
        cd "$PROJECT_DIR"
    fi

    if [ $SECURITY_ISSUES -gt 0 ]; then
        echo "=========================================="
        echo "警告: 发现 $SECURITY_ISSUES 项安全问题"
        echo "请在修复后重新部署，或使用 --skip-security 跳过"
        echo "=========================================="
        read -p "是否继续部署? (y/N): " confirm
        if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
            echo "部署已取消"
            exit 1
        fi
    fi
else
    echo "[3/8] 跳过安全扫描"
fi

echo "[4/8] 构建前端镜像..."
cd "$FRONTEND_DIR"
docker build -t nova-test/frontend:$TAG .

echo "[5/8] 构建 Executor 镜像..."
cd "$EXECUTOR_DIR"
docker build -t nova-test/executor:$TAG .

cd "$PROJECT_DIR"

echo "[6/8] 推送镜像 (可选)..."
if [ "$ENV" == "prod" ]; then
    echo "  推送前端镜像..."
    docker tag nova-test/frontend:$TAG registry.example.com/nova-test/frontend:$TAG
    docker push registry.example.com/nova-test/frontend:$TAG

    echo "  推送 Executor 镜像..."
    docker tag nova-test/executor:$TAG registry.example.com/nova-test/executor:$TAG
    docker push registry.example.com/nova-test/executor:$TAG
else
    echo "  跳过镜像推送 (非生产环境)"
fi

echo "[7/8] 更新 docker-compose.yml 镜像版本..."
if [ -f "$PROJECT_DIR/docker-compose.yml" ]; then
    sed -i.bak "s|image: nova-test/frontend:.*|image: nova-test/frontend:$TAG|g" "$PROJECT_DIR/docker-compose.yml"
    sed -i.bak "s|image: nova-test/executor:.*|image: nova-test/executor:$TAG|g" "$PROJECT_DIR/docker-compose.yml"
    rm -f "$PROJECT_DIR/docker-compose.yml.bak"
    echo "  ✓ docker-compose.yml 已更新"
fi

echo "[8/8] 启动服务..."
docker-compose -f "$PROJECT_DIR/docker-compose.yml" up -d

echo "=========================================="
echo "等待服务启动..."
echo "=========================================="

sleep 5

echo "=========================================="
echo "健康检查"
echo "=========================================="

check_endpoint() {
    local url=$1
    local name=$2
    local max_retries=5
    local retry=0

    while [ $retry -lt $max_retries ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            echo "  ✓ $name 健康检查通过"
            return 0
        fi
        retry=$((retry + 1))
        echo "  等待 $name 启动... ($retry/$max_retries)"
        sleep 3
    done

    echo "  ✗ $name 健康检查失败"
    return 1
}

HEALTH_CHECK_FAILED=0

FRONTEND_URL="http://localhost:3000"
if curl -sf "$FRONTEND_URL" > /dev/null 2>&1 || curl -sf "http://localhost:5173" > /dev/null 2>&1; then
    check_endpoint "http://localhost:3000" "Frontend"
else
    echo "  ! Frontend 端口未响应 (可能使用不同端口)"
fi

if ! check_endpoint "http://localhost:8002/health" "Executor"; then
    HEALTH_CHECK_FAILED=1
fi

echo "=========================================="
if [ $HEALTH_CHECK_FAILED -eq 1 ]; then
    echo "部署完成，但部分服务健康检查失败"
    echo "请检查服务日志: docker-compose logs"
    exit 1
else
    echo "部署成功!"
    echo "Frontend: http://localhost:3000 (或 http://localhost:5173)"
    echo "Executor: http://localhost:8002"
    echo "API 文档: http://localhost:8002/docs"
fi
echo "=========================================="

echo ""
echo "后续步骤:"
echo "1. 检查日志: docker-compose logs -f"
echo "2. 运行集成测试: npm run test:integration"
echo "3. 查看服务状态: docker-compose ps"
echo ""

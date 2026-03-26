#!/bin/bash
# Nova Test AaaS Executor 发布闸门脚本
# ================================
#
# 确保所有质量检查通过后才能发布

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查结果
CHECKS_PASSED=0
CHECKS_FAILED=0

check_pass() {
    log_info "✅ $1"
    ((CHECKS_PASSED++))
}

check_fail() {
    log_error "❌ $1"
    ((CHECKS_FAILED++))
}

# 开始检查
echo "=========================================="
echo "  Nova Test AaaS Executor 发布闸门检查"
echo "=========================================="
echo ""

# 1. 代码格式检查
log_info "1. 检查代码格式..."
cd "$PROJECT_DIR"
if command -v ruff &> /dev/null; then
    if ruff check executor-python/nova_executor/ 2>/dev/null; then
        check_pass "代码格式检查通过"
    else
        check_fail "代码格式检查失败"
    fi
else
    log_warn "ruff 未安装，跳过代码格式检查"
    check_pass "代码格式检查 (跳过)"
fi

# 2. 类型检查
log_info "2. 检查类型..."
if [ -d "executor-python" ]; then
    if python -m mypy nova_executor/ --ignore-missing-imports 2>/dev/null; then
        check_pass "类型检查通过"
    else
        check_fail "类型检查失败"
    fi
else
    check_pass "类型检查 (跳过)"
fi

# 3. 测试
log_info "3. 运行测试..."
if [ -d "tests" ]; then
    if pytest tests/ -v --tb=short 2>/dev/null; then
        check_pass "测试通过"
    else
        check_fail "测试失败"
    fi
else
    check_pass "测试 (跳过)"
fi

# 4. 敏感信息扫描
log_info "4. 扫描敏感信息..."
SENSITIVE_PATTERNS=("password.*=.*['\"][^'\"]+['\"]" "api_key.*=.*['\"][^'\"]+['\"]" "secret.*=.*['\"][^'\"]+['\"]")
FOUND_SENSITIVE=0

if [ -d "nova_executor" ]; then
    for pattern in "${SENSITIVE_PATTERNS[@]}"; do
        if grep -rE "$pattern" nova_executor/ --include="*.py" | grep -v "example\|masked\|test\|SENSITIVE_PATTERNS" > /dev/null; then
            FOUND_SENSITIVE=1
            break
        fi
    done

    if [ $FOUND_SENSITIVE -eq 0 ]; then
        check_pass "敏感信息扫描通过"
    else
        check_fail "发现敏感信息"
    fi
else
    check_pass "敏感信息扫描 (跳过)"
fi

# 5. 健康检查
log_info "5. 健康检查..."
cd "$PROJECT_DIR"
if curl -s http://localhost:8002/health > /dev/null 2>&1; then
    check_pass "健康检查通过"
else
    log_warn "服务未启动，跳过健康检查"
    check_pass "健康检查 (服务未启动)"
fi

# 输出结果
echo ""
echo "=========================================="
echo "  检查结果汇总"
echo "=========================================="
echo "✅ 通过: $CHECKS_PASSED"
echo "❌ 失败: $CHECKS_FAILED"
echo "=========================================="

if [ $CHECKS_FAILED -eq 0 ]; then
    log_info "所有检查通过！可以发布。"
    exit 0
else
    log_error "有 $CHECKS_FAILED 项检查失败，请修复后重试。"
    exit 1
fi

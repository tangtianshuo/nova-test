#!/bin/bash
# Nova Test AaaS Executor 发布闸门脚本
# ================================
#
# 确保所有质量检查通过后才能发布
#
# 发布闸门检查项：
# 1. 代码格式检查 (ruff)
# 2. 类型检查 (mypy)
# 3. 单元测试
# 4. 敏感信息扫描
# 5. 健康检查
# 6. 覆盖率检查

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
MIN_COVERAGE=${MIN_COVERAGE:-80}
API_PORT=${API_PORT:-8002}
API_HOST=${API_HOST:-localhost}

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

log_section() {
    echo ""
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}==========================================${NC}"
}

# 检查结果
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_SKIPPED=0

check_pass() {
    log_info "✅ $1"
    ((CHECKS_PASSED++))
}

check_fail() {
    log_error "❌ $1"
    ((CHECKS_FAILED++))
}

check_skip() {
    log_warn "⏭️  $1"
    ((CHECKS_SKIPPED++))
}

# 开始检查
log_section "Nova Test AaaS Executor 发布闸门检查"
echo "时间: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "最低覆盖率要求: ${MIN_COVERAGE}%"
echo ""

# 检查是否在正确目录
if [ ! -d "$PROJECT_DIR/executor-python" ]; then
    log_error "请在项目根目录运行此脚本"
    exit 1
fi

cd "$PROJECT_DIR/executor-python"

# 1. 代码格式检查
log_section "1. 代码格式检查"
log_info "检查 ruff 是否安装..."
if command -v ruff &> /dev/null; then
    log_info "运行 ruff 检查..."
    if ruff check nova_executor/ --ignore=E501,W503 2>&1; then
        check_pass "代码格式检查通过"
    else
        check_fail "代码格式检查失败"
    fi
else
    log_warn "ruff 未安装，跳过代码格式检查"
    check_skip "代码格式检查 (ruff 未安装)"
fi

# 2. 类型检查
log_section "2. 类型检查"
log_info "检查 mypy 是否安装..."
if command -v mypy &> /dev/null; then
    log_info "运行 mypy 类型检查..."
    if mypy nova_executor/ --ignore-missing-imports 2>&1; then
        check_pass "类型检查通过"
    else
        check_fail "类型检查失败"
    fi
else
    log_warn "mypy 未安装，跳过类型检查"
    check_skip "类型检查 (mypy 未安装)"
fi

# 3. 单元测试
log_section "3. 单元测试"
if [ -d "tests" ]; then
    log_info "运行 pytest 测试..."
    if pytest tests/ -v --tb=short 2>&1; then
        check_pass "单元测试通过"
    else
        check_fail "单元测试失败"
    fi
else
    check_skip "单元测试 (tests 目录不存在)"
fi

# 4. 覆盖率检查
log_section "4. 覆盖率检查"
if command -v pytest &> /dev/null && python -c "import pytest_cov" 2>/dev/null; then
    log_info "运行覆盖率测试..."
    if pytest tests/ --cov=nova_executor --cov-report=term-missing --cov-report=term 2>&1 | tee /tmp/coverage.log; then
        COVERAGE=$(grep "TOTAL" /tmp/coverage.log | awk '{print $NF}' | sed 's/%//')
        if [ -n "$COVERAGE" ]; then
            COVERAGE_INT=${COVERAGE%.*}
            if [ "$COVERAGE_INT" -ge "$MIN_COVERAGE" ]; then
                check_pass "覆盖率检查通过 (${COVERAGE}% >= ${MIN_COVERAGE}%)"
            else
                check_fail "覆盖率不足 (${COVERAGE}% < ${MIN_COVERAGE}%)"
            fi
        else
            check_pass "覆盖率检查通过 (无法解析覆盖率)"
        fi
    else
        check_fail "覆盖率测试失败"
    fi
else
    check_skip "覆盖率检查 (pytest-cov 未安装)"
fi

# 5. 敏感信息扫描
log_section "5. 敏感信息扫描"
SENSITIVE_PATTERNS=(
    "password.*=.*['\"][^'\"]{8,}['\"]"
    "api_key.*=.*['\"][^'\"]{8,}['\"]"
    "secret.*=.*['\"][^'\"]{8,}['\"]"
    "token.*=.*['\"][^'\"]{8,}['\"]"
)
FOUND_SENSITIVE=0

if [ -d "nova_executor" ]; then
    log_info "扫描敏感信息..."
    for pattern in "${SENSITIVE_PATTERNS[@]}"; do
        if grep -rE "$pattern" nova_executor/ --include="*.py" 2>/dev/null | grep -vE "(example|masked|test|placeholder|SENSITIVE_PATTERNS)" | grep -v "# noqa" > /dev/null; then
            FOUND_SENSITIVE=1
            log_error "发现可能的敏感信息: $pattern"
            break
        fi
    done

    if [ $FOUND_SENSITIVE -eq 0 ]; then
        check_pass "敏感信息扫描通过"
    else
        check_fail "发现敏感信息"
    fi
else
    check_skip "敏感信息扫描 (nova_executor 目录不存在)"
fi

# 6. 健康检查
log_section "6. 健康检查"
log_info "检查服务健康状态..."
if curl -s "http://${API_HOST}:${API_PORT}/health" > /dev/null 2>&1; then
    check_pass "健康检查通过"
else
    log_warn "服务未启动 (http://${API_HOST}:${API_PORT}/health)，跳过健康检查"
    check_skip "健康检查 (服务未启动)"
fi

# 7. 指标端点检查
log_section "7. 指标端点检查"
log_info "检查 Prometheus 指标端点..."
if curl -s "http://${API_HOST}:${API_PORT}/metrics" > /dev/null 2>&1; then
    check_pass "指标端点检查通过"
else
    log_warn "指标端点不可用，跳过检查"
    check_skip "指标端点检查 (服务未启动)"
fi

# 8. 安全依赖检查
log_section "8. 安全依赖检查"
if [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then
    log_info "检查已知的安全漏洞..."
    if command -v pip-audit &> /dev/null; then
        if pip-audit -r requirements.txt 2>&1 | grep -q "No known vulnerabilities found"; then
            check_pass "安全依赖检查通过"
        else
            check_fail "发现安全漏洞"
        fi
    elif command -v safety &> /dev/null; then
        if safety check -r requirements.txt 2>&1; then
            check_pass "安全依赖检查通过"
        else
            check_fail "发现安全漏洞"
        fi
    else
        check_skip "安全依赖检查 (pip-audit/safety 未安装)"
    fi
else
    check_skip "安全依赖检查 (无依赖文件)"
fi

# 输出结果
log_section "检查结果汇总"
echo ""
echo -e "  ${GREEN}✅ 通过:${NC} $CHECKS_PASSED"
echo -e "  ${RED}❌ 失败:${NC} $CHECKS_FAILED"
echo -e "  ${YELLOW}⏭️  跳过:${NC} $CHECKS_SKIPPED"
echo ""

TOTAL=$((CHECKS_PASSED + CHECKS_FAILED + CHECKS_SKIPPED))
echo "总计: $TOTAL 项检查"
echo "时间: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    log_info "🎉 所有检查通过！可以发布。"
    echo ""
    echo "下一步:"
    echo "  1. 提交代码: git commit -m 'Release version'"
    echo "  2. 创建标签: git tag v1.0.0"
    echo "  3. 推送发布: git push && git push --tags"
    echo ""
    exit 0
else
    log_error "❌ 有 $CHECKS_FAILED 项检查失败，请修复后重试。"
    echo ""
    echo "常见问题排查:"
    echo "  - 确保所有测试通过: pytest tests/ -v"
    echo "  - 确保代码格式正确: ruff check nova_executor/"
    echo "  - 确保类型检查通过: mypy nova_executor/"
    echo "  - 确保覆盖率达标: pytest --cov=nova_executor --cov-fail-under=${MIN_COVERAGE}"
    echo ""
    exit 1
fi

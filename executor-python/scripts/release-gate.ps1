"""
发布闸门脚本 (PowerShell)
=====================

Windows PowerShell 版本的发布闸门脚本
"""

param(
    [switch]$SkipTests,
    [switch]$SkipTypeCheck
)

$ErrorActionPreference = "Stop"

# 颜色
function Write-Info { param($msg) Write-Host "[INFO] ✅ $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "[WARN] ⚠️  $msg" -ForegroundColor Yellow }
function Write-Err { param($msg) Write-Host "[ERROR] ❌ $msg" -ForegroundColor Red }

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Nova Test AaaS 发布闸门检查"
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$passed = 0
$failed = 0

# 检查测试
if (-not $SkipTests) {
    Write-Info "1. 运行测试..."
    try {
        pytest tests/ -v --tb=short 2>$null
        Write-Info "测试通过"
        $passed++
    } catch {
        Write-Err "测试失败"
        $failed++
    }
} else {
    Write-Warn "跳过测试"
    $passed++
}

# 类型检查
if (-not $SkipTypeCheck) {
    Write-Info "2. 类型检查..."
    try {
        python -m mypy nova_executor/ --ignore-missing-imports 2>$null
        Write-Info "类型检查通过"
        $passed++
    } catch {
        Write-Err "类型检查失败"
        $failed++
    }
} else {
    Write-Warn "跳过类型检查"
    $passed++
}

Write-Host ""
Write-Host "========================================"
Write-Host "  检查结果: 通过=$passed 失败=$failed"
Write-Host "========================================"

if ($failed -eq 0) {
    Write-Info "所有检查通过！可以发布。"
    exit 0
} else {
    Write-Err "有 $failed 项检查失败，请修复后重试。"
    exit 1
}

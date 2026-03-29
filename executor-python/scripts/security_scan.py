#!/usr/bin/env python3
"""
Nova Executor 安全扫描脚本
集成 bandit、pip-audit 和 safety 工具进行安全扫描
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


PROJECT_ROOT = Path(__file__).parent.parent
EXECUTOR_DIR = PROJECT_ROOT / "nova_executor"


def run_command(
    cmd: List[str],
    description: str,
    cwd: Optional[Path] = None
) -> int:
    """运行命令并输出结果"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"命令: {' '.join(cmd)}")
    print(f"{'='*60}")

    result = subprocess.run(
        cmd,
        cwd=cwd or PROJECT_ROOT,
        capture_output=False
    )

    return result.returncode


def run_bandit() -> int:
    """运行 Bandit 代码安全扫描"""
    print("\n[1/3] 运行 Bandit 代码安全扫描...")

    cmd = [
        "bandit",
        "-r",
        str(EXECUTOR_DIR),
        "-f", "screen",
        "-ll"
    ]

    return run_command(cmd, "Bandit 代码安全扫描")


def run_pip_audit() -> int:
    """运行 pip-audit 依赖漏洞扫描"""
    print("\n[2/3] 运行 pip-audit 依赖漏洞扫描...")

    cmd = [
        "pip-audit",
        "-r",
        str(PROJECT_ROOT / "pyproject.toml"),
        "-f", "columns"
    ]

    return run_command(cmd, "pip-audit 依赖漏洞扫描")


def run_safety() -> int:
    """运行 Safety 依赖安全检查"""
    print("\n[3/3] 运行 Safety 依赖安全检查...")

    cmd = [
        "safety",
        "check",
        "-r", str(PROJECT_ROOT / "requirements.txt"),
        "--full-report"
    ]

    try:
        return run_command(cmd, "Safety 依赖安全检查")
    except FileNotFoundError:
        print("requirements.txt 不存在，跳过 Safety 检查")
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Nova Executor 安全扫描工具"
    )
    parser.add_argument(
        "--skip-bandit",
        action="store_true",
        help="跳过 Bandit 代码扫描"
    )
    parser.add_argument(
        "--skip-pip-audit",
        action="store_true",
        help="跳过 pip-audit 依赖扫描"
    )
    parser.add_argument(
        "--skip-safety",
        action="store_true",
        help="跳过 Safety 依赖检查"
    )
    parser.add_argument(
        "--fail-level",
        choices=["low", "medium", "high", "critical"],
        default="medium",
        help="发现漏洞时的失败级别 (默认: medium)"
    )
    parser.add_argument(
        "--output",
        choices=["screen", "json", "text"],
        default="screen",
        help="输出格式 (默认: screen)"
    )

    args = parser.parse_args()

    print("="*60)
    print("Nova Executor 安全扫描")
    print("="*60)

    results = {}

    if not args.skip_bandit:
        results["bandit"] = run_bandit()
    else:
        print("\n[跳过] Bandit 代码扫描")

    if not args.skip_pip_audit:
        results["pip_audit"] = run_pip_audit()
    else:
        print("\n[跳过] pip-audit 依赖扫描")

    if not args.skip_safety:
        results["safety"] = run_safety()
    else:
        print("\n[跳过] Safety 依赖检查")

    print("\n" + "="*60)
    print("安全扫描结果汇总")
    print("="*60)

    for tool, returncode in results.items():
        status = "通过 ✓" if returncode == 0 else "失败 ✗"
        print(f"{tool}: {status}")

    total_failures = sum(1 for r in results.values() if r != 0)

    if total_failures > 0:
        print(f"\n共发现 {total_failures} 项安全问题")
        print("请查看上述详细信息并修复问题")
        sys.exit(1)
    else:
        print("\n所有安全扫描通过！")
        sys.exit(0)


if __name__ == "__main__":
    main()

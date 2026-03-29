"""
安全配置检查模块
================

提供安全配置基线检查功能：
1. 定义安全基线规范
2. 实现配置检查器
3. 添加违规告警机制
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime


class CheckSeverity(str, Enum):
    """检查严重级别"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class CheckCategory(str, Enum):
    """检查类别"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NETWORK = "network"
    DATA_PROTECTION = "data_protection"
    SESSION = "session"
    LOGGING = "logging"
    ENCRYPTION = "encryption"
    COMPLIANCE = "compliance"


@dataclass
class SecurityBaseline:
    """安全基线定义"""
    id: str
    name: str
    category: CheckCategory
    description: str
    severity: CheckSeverity
    recommended_value: Any
    check_type: str
    check_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfigCheck:
    """配置检查"""
    baseline: SecurityBaseline
    actual_value: Any
    passed: bool
    details: str


@dataclass
class ConfigViolation:
    """配置违规"""
    violation_id: str
    baseline_id: str
    baseline_name: str
    severity: CheckSeverity
    category: CheckCategory
    expected_value: Any
    actual_value: Any
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfigCheckResult:
    """配置检查结果"""
    check_id: str
    check_name: str
    category: CheckCategory
    severity: CheckSeverity
    passed: bool
    expected: Any
    actual: Any
    message: str


SECURITY_BASELINES: List[SecurityBaseline] = [
    SecurityBaseline(
        id="AUTH_001",
        name="密码最小长度",
        category=CheckCategory.AUTHENTICATION,
        description="密码最小长度必须至少8位",
        severity=CheckSeverity.HIGH,
        recommended_value=8,
        check_type="min_length",
        check_params={"min_length": 8},
    ),
    SecurityBaseline(
        id="AUTH_002",
        name="密码必须包含特殊字符",
        category=CheckCategory.AUTHENTICATION,
        description="密码必须包含至少一个特殊字符",
        severity=CheckSeverity.MEDIUM,
        recommended_value=True,
        check_type="regex",
        check_params={"pattern": r"[!@#$%^&*(),.?\":{}|<>]"},
    ),
    SecurityBaseline(
        id="AUTH_003",
        name="MFA 必须启用",
        category=CheckCategory.AUTHENTICATION,
        description="多因素认证必须启用",
        severity=CheckSeverity.CRITICAL,
        recommended_value=True,
        check_type="boolean",
    ),
    SecurityBaseline(
        id="AUTH_004",
        name="会话超时配置",
        category=CheckCategory.SESSION,
        description="会话超时必须不超过30分钟",
        severity=CheckSeverity.HIGH,
        recommended_value=1800,
        check_type="max_value",
        check_params={"max_value": 1800},
    ),
    SecurityBaseline(
        id="AUTH_005",
        name="密码过期策略",
        category=CheckCategory.AUTHENTICATION,
        description="密码过期天数必须设置",
        severity=CheckSeverity.MEDIUM,
        recommended_value=90,
        check_type="range",
        check_params={"min_value": 30, "max_value": 180},
    ),
    SecurityBaseline(
        id="NET_001",
        name="HTTPS 必须启用",
        category=CheckCategory.NETWORK,
        description="所有外部通信必须使用 HTTPS",
        severity=CheckSeverity.CRITICAL,
        recommended_value=True,
        check_type="boolean",
    ),
    SecurityBaseline(
        id="NET_002",
        name="CORS 配置",
        category=CheckCategory.NETWORK,
        description="CORS 必须限制来源",
        severity=CheckSeverity.HIGH,
        recommended_value="strict",
        check_type="cors_config",
    ),
    SecurityBaseline(
        id="NET_003",
        name="API 速率限制",
        category=CheckCategory.NETWORK,
        description="API 必须启用速率限制",
        severity=CheckSeverity.HIGH,
        recommended_value=True,
        check_type="boolean",
    ),
    SecurityBaseline(
        id="DATA_001",
        name="敏感数据加密",
        category=CheckCategory.DATA_PROTECTION,
        description="敏感数据必须加密存储",
        severity=CheckSeverity.CRITICAL,
        recommended_value=True,
        check_type="boolean",
    ),
    SecurityBaseline(
        id="DATA_002",
        name="数据备份加密",
        category=CheckCategory.DATA_PROTECTION,
        description="数据备份必须加密",
        severity=CheckSeverity.HIGH,
        recommended_value=True,
        check_type="boolean",
    ),
    SecurityBaseline(
        id="LOG_001",
        name="安全日志记录",
        category=CheckCategory.LOGGING,
        description="安全相关事件必须记录日志",
        severity=CheckSeverity.HIGH,
        recommended_value=True,
        check_type="boolean",
    ),
    SecurityBaseline(
        id="LOG_002",
        name="日志保留时间",
        category=CheckCategory.LOGGING,
        description="日志必须保留至少90天",
        severity=CheckSeverity.MEDIUM,
        recommended_value=90,
        check_type="min_value",
        check_params={"min_value": 90},
    ),
    SecurityBaseline(
        id="LOG_003",
        name="日志脱敏",
        category=CheckCategory.LOGGING,
        description="日志中必须对敏感信息脱敏",
        severity=CheckSeverity.HIGH,
        recommended_value=True,
        check_type="boolean",
    ),
    SecurityBaseline(
        id="ENC_001",
        name="传输加密",
        category=CheckCategory.ENCRYPTION,
        description="数据传输必须使用 TLS 1.2+",
        severity=CheckSeverity.CRITICAL,
        recommended_value="TLSv1.2",
        check_type="tls_version",
    ),
    SecurityBaseline(
        id="ENC_002",
        name="密钥管理",
        category=CheckCategory.ENCRYPTION,
        description="加密密钥必须使用专用密钥管理服务",
        severity=CheckSeverity.HIGH,
        recommended_value=True,
        check_type="boolean",
    ),
    SecurityBaseline(
        id="AUTHZ_001",
        name="RBAC 必须启用",
        category=CheckCategory.AUTHORIZATION,
        description="必须启用基于角色的访问控制",
        severity=CheckSeverity.CRITICAL,
        recommended_value=True,
        check_type="boolean",
    ),
    SecurityBaseline(
        id="AUTHZ_002",
        name="最小权限原则",
        category=CheckCategory.AUTHORIZATION,
        description="账户必须遵循最小权限原则",
        severity=CheckSeverity.HIGH,
        recommended_value=True,
        check_type="boolean",
    ),
    SecurityBaseline(
        id="COMP_001",
        name="租户隔离",
        category=CheckCategory.COMPLIANCE,
        description="多租户环境必须实现数据隔离",
        severity=CheckSeverity.CRITICAL,
        recommended_value=True,
        check_type="boolean",
    ),
    SecurityBaseline(
        id="COMP_002",
        name="审计日志保留",
        category=CheckCategory.COMPLIANCE,
        description="审计日志必须保留至少1年",
        severity=CheckSeverity.HIGH,
        recommended_value=365,
        check_type="min_value",
        check_params={"min_value": 365},
    ),
]


class ConfigChecker:
    """配置检查器"""

    def __init__(self):
        self.baselines = {b.id: b for b in SECURITY_BASELINES}
        self.violations: List[ConfigViolation] = []
        self.check_results: List[ConfigCheckResult] = []

    def get_baseline(self, baseline_id: str) -> Optional[SecurityBaseline]:
        """获取基线定义"""
        return self.baselines.get(baseline_id)

    def get_baselines_by_category(self, category: CheckCategory) -> List[SecurityBaseline]:
        """按类别获取基线"""
        return [b for b in self.baselines.values() if b.category == category]

    def get_baselines_by_severity(self, severity: CheckSeverity) -> List[SecurityBaseline]:
        """按严重级别获取基线"""
        return [b for b in self.baselines.values() if b.severity == severity]

    def check_boolean(
        self,
        baseline: SecurityBaseline,
        actual_value: Any,
    ) -> ConfigCheck:
        """检查布尔配置"""
        passed = bool(actual_value) == bool(baseline.recommended_value)

        return ConfigCheck(
            baseline=baseline,
            actual_value=actual_value,
            passed=passed,
            details=f"Expected {baseline.recommended_value}, got {actual_value}" if not passed else "OK",
        )

    def check_min_length(
        self,
        baseline: SecurityBaseline,
        actual_value: Any,
    ) -> ConfigCheck:
        """检查最小长度"""
        min_length = baseline.check_params.get("min_length", 8)
        passed = len(str(actual_value)) >= min_length

        return ConfigCheck(
            baseline=baseline,
            actual_value=len(str(actual_value)),
            passed=passed,
            details=f"Minimum length should be at least {min_length}" if not passed else f"Length: {len(str(actual_value))}",
        )

    def check_max_value(
        self,
        baseline: SecurityBaseline,
        actual_value: Any,
    ) -> ConfigCheck:
        """检查最大值"""
        max_value = baseline.check_params.get("max_value")
        if max_value is None:
            max_value = baseline.recommended_value

        try:
            value = int(actual_value)
            passed = value <= max_value
            details = f"Value {value} exceeds maximum {max_value}" if not passed else f"Value: {value}"
        except (ValueError, TypeError):
            passed = False
            details = f"Invalid value: {actual_value}"

        return ConfigCheck(
            baseline=baseline,
            actual_value=actual_value,
            passed=passed,
            details=details,
        )

    def check_min_value(
        self,
        baseline: SecurityBaseline,
        actual_value: Any,
    ) -> ConfigCheck:
        """检查最小值"""
        min_value = baseline.check_params.get("min_value")
        if min_value is None:
            min_value = baseline.recommended_value

        try:
            value = int(actual_value)
            passed = value >= min_value
            details = f"Value {value} below minimum {min_value}" if not passed else f"Value: {value}"
        except (ValueError, TypeError):
            passed = False
            details = f"Invalid value: {actual_value}"

        return ConfigCheck(
            baseline=baseline,
            actual_value=actual_value,
            passed=passed,
            details=details,
        )

    def check_range(
        self,
        baseline: SecurityBaseline,
        actual_value: Any,
    ) -> ConfigCheck:
        """检查范围"""
        min_val = baseline.check_params.get("min_value", 0)
        max_val = baseline.check_params.get("max_value", 999999)

        try:
            value = int(actual_value)
            passed = min_val <= value <= max_val
            details = f"Value {value} outside range [{min_val}, {max_val}]" if not passed else f"Value: {value}"
        except (ValueError, TypeError):
            passed = False
            details = f"Invalid value: {actual_value}"

        return ConfigCheck(
            baseline=baseline,
            actual_value=actual_value,
            passed=passed,
            details=details,
        )

    def check_regex(
        self,
        baseline: SecurityBaseline,
        actual_value: Any,
    ) -> ConfigCheck:
        """检查正则表达式"""
        pattern = baseline.check_params.get("pattern")
        if not pattern:
            pattern = r"[!@#$%^&*(),.?\":{}|<>]"

        try:
            passed = bool(re.search(pattern, str(actual_value)))
            details = f"Value does not match required pattern" if not passed else "OK"
        except Exception as e:
            passed = False
            details = f"Regex check failed: {str(e)}"

        return ConfigCheck(
            baseline=baseline,
            actual_value=actual_value,
            passed=passed,
            details=details,
        )

    def check_config(
        self,
        baseline_id: str,
        actual_value: Any,
    ) -> ConfigCheckResult:
        """
        执行配置检查

        Args:
            baseline_id: 基线 ID
            actual_value: 实际配置值

        Returns:
            ConfigCheckResult 检查结果
        """
        baseline = self.baselines.get(baseline_id)
        if not baseline:
            return ConfigCheckResult(
                check_id=baseline_id,
                check_name="Unknown",
                category=CheckCategory.COMPLIANCE,
                severity=CheckSeverity.INFO,
                passed=False,
                expected=None,
                actual=actual_value,
                message=f"Baseline {baseline_id} not found",
            )

        check_type = baseline.check_type
        check_func_map = {
            "boolean": self.check_boolean,
            "min_length": self.check_min_length,
            "max_value": self.check_max_value,
            "min_value": self.check_min_value,
            "range": self.check_range,
            "regex": self.check_regex,
        }

        check_func = check_func_map.get(check_type, self.check_boolean)
        config_check = check_func(baseline, actual_value)

        result = ConfigCheckResult(
            check_id=baseline.id,
            check_name=baseline.name,
            category=baseline.category,
            severity=baseline.severity,
            passed=config_check.passed,
            expected=baseline.recommended_value,
            actual=config_check.actual_value,
            message=config_check.details,
        )

        self.check_results.append(result)

        if not config_check.passed:
            violation = ConfigViolation(
                violation_id=f"vio_{len(self.violations) + 1}",
                baseline_id=baseline.id,
                baseline_name=baseline.name,
                severity=baseline.severity,
                category=baseline.category,
                expected_value=baseline.recommended_value,
                actual_value=config_check.actual_value,
                details={"check_type": check_type},
            )
            self.violations.append(violation)

        return result

    def check_configs(self, configs: Dict[str, Any]) -> List[ConfigCheckResult]:
        """
        批量检查配置

        Args:
            configs: 配置字典 {baseline_id: value}

        Returns:
            检查结果列表
        """
        results = []
        for baseline_id, value in configs.items():
            result = self.check_config(baseline_id, value)
            results.append(result)
        return results

    def check_all_baselines(
        self,
        get_value_func: Callable[[str], Any],
    ) -> List[ConfigCheckResult]:
        """
        检查所有基线

        Args:
            get_value_func: 获取配置值的函数

        Returns:
            检查结果列表
        """
        results = []
        for baseline in self.baselines.values():
            value = get_value_func(baseline.id)
            result = self.check_config(baseline.id, value)
            results.append(result)
        return results

    def get_summary(self) -> Dict[str, Any]:
        """获取检查摘要"""
        total = len(self.check_results)
        passed = sum(1 for r in self.check_results if r.passed)
        failed = total - passed

        by_category: Dict[str, Dict[str, int]] = {}
        by_severity: Dict[str, Dict[str, int]] = {}

        for result in self.check_results:
            cat = result.category.value
            sev = result.severity.value

            if cat not in by_category:
                by_category[cat] = {"passed": 0, "failed": 0}
            if sev not in by_severity:
                by_severity[sev] = {"passed": 0, "failed": 0}

            if result.passed:
                by_category[cat]["passed"] += 1
                by_severity[sev]["passed"] += 1
            else:
                by_category[cat]["failed"] += 1
                by_severity[sev]["failed"] += 1

        return {
            "total_checks": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0,
            "by_category": by_category,
            "by_severity": by_severity,
        }

    def get_violations_report(
        self,
        min_severity: Optional[CheckSeverity] = None,
        category: Optional[CheckCategory] = None,
    ) -> List[Dict[str, Any]]:
        """获取违规报告"""
        violations = self.violations

        if min_severity:
            severity_order = [
                CheckSeverity.CRITICAL,
                CheckSeverity.HIGH,
                CheckSeverity.MEDIUM,
                CheckSeverity.LOW,
                CheckSeverity.INFO,
            ]
            min_index = severity_order.index(min_severity)
            violations = [
                v for v in violations
                if severity_order.index(v.severity) <= min_index
            ]

        if category:
            violations = [v for v in violations if v.category == category]

        return [
            {
                "violation_id": v.violation_id,
                "baseline_id": v.baseline_id,
                "baseline_name": v.baseline_name,
                "severity": v.severity.value,
                "category": v.category.value,
                "expected_value": v.expected_value,
                "actual_value": v.actual_value,
                "timestamp": v.timestamp.isoformat(),
                "details": v.details,
            }
            for v in violations
        ]

    def generate_baseline_report(self) -> Dict[str, Any]:
        """生成基线报告"""
        return {
            "total_baselines": len(self.baselines),
            "by_category": {
                cat.value: len([b for b in self.baselines.values() if b.category == cat])
                for cat in CheckCategory
            },
            "by_severity": {
                sev.value: len([b for b in self.baselines.values() if b.severity == sev])
                for sev in CheckSeverity
            },
            "critical_checks": len([
                b for b in self.baselines.values()
                if b.severity == CheckSeverity.CRITICAL
            ]),
        }

    def clear_logs(self):
        """清除日志"""
        self.violations.clear()
        self.check_results.clear()


_default_checker: Optional[ConfigChecker] = None


def get_config_checker() -> ConfigChecker:
    """获取配置检查器实例"""
    global _default_checker
    if _default_checker is None:
        _default_checker = ConfigChecker()
    return _default_checker


def check_security_config(
    baseline_id: str,
    actual_value: Any,
) -> ConfigCheckResult:
    """
    便捷函数：检查安全配置

    Args:
        baseline_id: 基线 ID
        actual_value: 实际配置值

    Returns:
        ConfigCheckResult 检查结果
    """
    checker = get_config_checker()
    return checker.check_config(baseline_id, actual_value)


def check_all_security_configs(
    configs: Dict[str, Any],
) -> List[ConfigCheckResult]:
    """
    便捷函数：批量检查安全配置

    Args:
        configs: 配置字典

    Returns:
        检查结果列表
    """
    checker = get_config_checker()
    return checker.check_configs(configs)


def get_security_baselines() -> List[SecurityBaseline]:
    """获取所有安全基线"""
    return SECURITY_BASELINES.copy()

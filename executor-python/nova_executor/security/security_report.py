"""
安全状态报告模块
================

提供安全状态报告生成和导出功能：
1. 设计安全报告模板
2. 实现报告生成器
3. 添加报告导出功能
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from abc import ABC, abstractmethod


class ReportFormat(str, Enum):
    """报告格式"""
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"
    PDF = "pdf"


class SecurityLevel(str, Enum):
    """安全级别"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    PASS = "pass"

    def severity_rank(self) -> int:
        """获取安全级别排名"""
        ranks = {
            SecurityLevel.CRITICAL: 5,
            SecurityLevel.HIGH: 4,
            SecurityLevel.MEDIUM: 3,
            SecurityLevel.LOW: 2,
            SecurityLevel.PASS: 1,
        }
        return ranks.get(self, 0)

    def __ge__(self, other):
        """比较操作符 >= """
        if isinstance(other, SecurityLevel):
            return self.severity_rank() >= other.severity_rank()
        return NotImplemented

    def __gt__(self, other):
        """比较操作符 > """
        if isinstance(other, SecurityLevel):
            return self.severity_rank() > other.severity_rank()
        return NotImplemented

    def __le__(self, other):
        """比较操作符 <= """
        if isinstance(other, SecurityLevel):
            return self.severity_rank() <= other.severity_rank()
        return NotImplemented

    def __lt__(self, other):
        """比较操作符 < """
        if isinstance(other, SecurityLevel):
            return self.severity_rank() < other.severity_rank()
        return NotImplemented


class ReportSection(str, Enum):
    """报告章节"""
    SUMMARY = "summary"
    PERMISSIONS = "permissions"
    ISOLATION = "isolation"
    SENSITIVE_DATA = "sensitive_data"
    CONFIGURATION = "configuration"
    VIOLATIONS = "violations"
    RECOMMENDATIONS = "recommendations"


@dataclass
class SecurityMetric:
    """安全指标"""
    name: str
    value: Any
    unit: Optional[str] = None
    status: SecurityLevel = SecurityLevel.PASS
    trend: Optional[str] = None


@dataclass
class ViolationSummary:
    """违规摘要"""
    total_violations: int
    by_type: Dict[str, int]
    by_severity: Dict[str, int]
    recent_violations: List[Dict[str, Any]]


@dataclass
class PermissionSummary:
    """权限摘要"""
    total_roles: int
    total_permissions: int
    critical_permissions: List[str]
    overprivileged_roles: List[str]


@dataclass
class IsolationSummary:
    """隔离摘要"""
    isolation_level: str
    tests_passed: int
    tests_failed: int
    total_cross_tenant_attempts: int
    blocked_attempts: int


@dataclass
class SensitiveDataSummary:
    """敏感数据摘要"""
    scans_performed: int
    leaks_detected: int
    by_type: Dict[str, int]
    by_severity: Dict[str, int]


@dataclass
class ConfigurationSummary:
    """配置摘要"""
    total_checks: int
    passed_checks: int
    failed_checks: int
    warnings: List[str]


@dataclass
class SecurityReport:
    """安全报告"""
    report_id: str
    title: str
    generated_at: datetime
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    overall_status: SecurityLevel = SecurityLevel.PASS
    summary: Dict[str, Any] = field(default_factory=dict)

    permission_summary: Optional[PermissionSummary] = None
    isolation_summary: Optional[IsolationSummary] = None
    sensitive_data_summary: Optional[SensitiveDataSummary] = None
    configuration_summary: Optional[ConfigurationSummary] = None
    violation_summary: Optional[ViolationSummary] = None

    metrics: List[SecurityMetric] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result["generated_at"] = self.generated_at.isoformat()
        if self.period_start:
            result["period_start"] = self.period_start.isoformat()
        if self.period_end:
            result["period_end"] = self.period_end.isoformat()
        return result


class ReportExporter(ABC):
    """报告导出器基类"""

    @abstractmethod
    def export(self, report: SecurityReport) -> str:
        """导出报告"""
        pass


class JSONExporter(ReportExporter):
    """JSON 导出器"""

    def export(self, report: SecurityReport) -> str:
        """导出为 JSON 格式"""
        return json.dumps(report.to_dict(), indent=2, ensure_ascii=False)


class MarkdownExporter(ReportExporter):
    """Markdown 导出器"""

    def export(self, report: SecurityReport) -> str:
        """导出为 Markdown 格式"""
        lines = []

        lines.append(f"# {report.title}")
        lines.append("")
        lines.append(f"**报告 ID**: {report.report_id}")
        lines.append(f"**生成时间**: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")

        if report.period_start and report.period_end:
            lines.append(f"**报告周期**: {report.period_start.strftime('%Y-%m-%d')} - {report.period_end.strftime('%Y-%m-%d')}")

        lines.append("")
        lines.append(f"**总体状态**: {self._status_badge(report.overall_status)}")
        lines.append("")

        if report.summary:
            lines.append("## 摘要")
            lines.append("")
            for key, value in report.summary.items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")

        if report.permission_summary:
            lines.append("## 权限分析")
            lines.append("")
            lines.append(f"- 角色总数: {report.permission_summary.total_roles}")
            lines.append(f"- 权限总数: {report.permission_summary.total_permissions}")
            if report.permission_summary.critical_permissions:
                lines.append("- 关键权限:")
                for perm in report.permission_summary.critical_permissions:
                    lines.append(f"  - {perm}")
            lines.append("")

        if report.isolation_summary:
            lines.append("## 租户隔离")
            lines.append("")
            lines.append(f"- 隔离级别: {report.isolation_summary.isolation_level}")
            lines.append(f"- 测试通过: {report.isolation_summary.tests_passed}")
            lines.append(f"- 测试失败: {report.isolation_summary.tests_failed}")
            lines.append(f"- 跨租户尝试: {report.isolation_summary.total_cross_tenant_attempts}")
            lines.append("")

        if report.violation_summary:
            lines.append("## 违规统计")
            lines.append("")
            lines.append(f"- 总违规数: {report.violation_summary.total_violations}")
            for severity, count in report.violation_summary.by_severity.items():
                lines.append(f"  - {severity}: {count}")
            lines.append("")

        if report.recommendations:
            lines.append("## 建议")
            lines.append("")
            for i, rec in enumerate(report.recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")

        return "\n".join(lines)

    def _status_badge(self, status: SecurityLevel) -> str:
        """生成状态徽章"""
        badges = {
            SecurityLevel.CRITICAL: "🔴 CRITICAL",
            SecurityLevel.HIGH: "🟠 HIGH",
            SecurityLevel.MEDIUM: "🟡 MEDIUM",
            SecurityLevel.LOW: "🔵 LOW",
            SecurityLevel.PASS: "🟢 PASS",
        }
        return badges.get(status, str(status))


class HTMLExporter(ReportExporter):
    """HTML 导出器"""

    def export(self, report: SecurityReport) -> str:
        """导出为 HTML 格式"""
        status_colors = {
            SecurityLevel.CRITICAL: "#dc2626",
            SecurityLevel.HIGH: "#ea580c",
            SecurityLevel.MEDIUM: "#ca8a04",
            SecurityLevel.LOW: "#0284c7",
            SecurityLevel.PASS: "#16a34a",
        }

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report.title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .status {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 4px;
            color: white;
            font-weight: bold;
        }}
        .section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .metric {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }}
        .metric:last-child {{
            border-bottom: none;
        }}
        .metric-name {{
            color: #666;
        }}
        .metric-value {{
            font-weight: bold;
        }}
        .critical {{ color: {status_colors[SecurityLevel.CRITICAL]}; }}
        .high {{ color: {status_colors[SecurityLevel.HIGH]}; }}
        .medium {{ color: {status_colors[SecurityLevel.MEDIUM]}; }}
        .low {{ color: {status_colors[SecurityLevel.LOW]}; }}
        .pass {{ color: {status_colors[SecurityLevel.PASS]}; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{report.title}</h1>
        <p><strong>报告 ID:</strong> {report.report_id}</p>
        <p><strong>生成时间:</strong> {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <span class="status" style="background: {status_colors[report.overall_status]};">
            {report.overall_status.value.upper()}
        </span>
    </div>
"""

        if report.summary:
            html += """
    <div class="section">
        <h2>摘要</h2>
"""
            for key, value in report.summary.items():
                html += f"""
        <div class="metric">
            <span class="metric-name">{key}</span>
            <span class="metric-value">{value}</span>
        </div>
"""
            html += "    </div>\n"

        if report.violation_summary:
            html += f"""
    <div class="section">
        <h2>违规统计</h2>
        <div class="metric">
            <span class="metric-name">总违规数</span>
            <span class="metric-value">{report.violation_summary.total_violations}</span>
        </div>
"""
            for severity, count in report.violation_summary.by_severity.items():
                color_class = severity.lower()
                html += f"""
        <div class="metric">
            <span class="metric-name">{severity}</span>
            <span class="metric-value {color_class}">{count}</span>
        </div>
"""
            html += "    </div>\n"

        if report.recommendations:
            html += """
    <div class="section">
        <h2>建议</h2>
        <ul>
"""
            for rec in report.recommendations:
                html += f"            <li>{rec}</li>\n"
            html += """
        </ul>
    </div>
"""

        html += """
</body>
</html>
"""
        return html


class SecurityReportGenerator:
    """安全报告生成器"""

    def __init__(self):
        self.exporters: Dict[ReportFormat, ReportExporter] = {
            ReportFormat.JSON: JSONExporter(),
            ReportFormat.MARKDOWN: MarkdownExporter(),
            ReportFormat.HTML: HTMLExporter(),
        }

    def generate_report(
        self,
        title: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        permission_data: Optional[Dict[str, Any]] = None,
        isolation_data: Optional[Dict[str, Any]] = None,
        sensitive_data: Optional[Dict[str, Any]] = None,
        configuration_data: Optional[Dict[str, Any]] = None,
        violations: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SecurityReport:
        """
        生成安全报告

        Args:
            title: 报告标题
            period_start: 报告周期开始
            period_end: 报告周期结束
            permission_data: 权限数据
            isolation_data: 隔离数据
            sensitive_data: 敏感数据扫描结果
            configuration_data: 配置检查结果
            violations: 违规记录列表
            metadata: 额外元数据

        Returns:
            SecurityReport 安全报告
        """
        report_id = f"sec_report_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        report = SecurityReport(
            report_id=report_id,
            title=title,
            generated_at=datetime.now(),
            period_start=period_start,
            period_end=period_end,
            metadata=metadata or {},
        )

        summary_data = {}
        overall_status = SecurityLevel.PASS

        if permission_data:
            report.permission_summary = PermissionSummary(
                total_roles=permission_data.get("total_roles", 0),
                total_permissions=permission_data.get("total_permissions", 0),
                critical_permissions=permission_data.get("critical_permissions", []),
                overprivileged_roles=permission_data.get("overprivileged_roles", []),
            )
            summary_data["总角色数"] = permission_data.get("total_roles", 0)
            summary_data["总权限数"] = permission_data.get("total_permissions", 0)

        if isolation_data:
            report.isolation_summary = IsolationSummary(
                isolation_level=isolation_data.get("isolation_level", "unknown"),
                tests_passed=isolation_data.get("tests_passed", 0),
                tests_failed=isolation_data.get("tests_failed", 0),
                total_cross_tenant_attempts=isolation_data.get("total_cross_tenant_attempts", 0),
                blocked_attempts=isolation_data.get("blocked_attempts", 0),
            )
            summary_data["隔离级别"] = isolation_data.get("isolation_level", "unknown")
            summary_data["隔离测试通过"] = f"{isolation_data.get('tests_passed', 0)}/{isolation_data.get('tests_passed', 0) + isolation_data.get('tests_failed', 0)}"

            if isolation_data.get("tests_failed", 0) > 0:
                overall_status = max(overall_status, SecurityLevel.HIGH)

        if sensitive_data:
            report.sensitive_data_summary = SensitiveDataSummary(
                scans_performed=sensitive_data.get("scans_performed", 0),
                leaks_detected=sensitive_data.get("leaks_detected", 0),
                by_type=sensitive_data.get("by_type", {}),
                by_severity=sensitive_data.get("by_severity", {}),
            )
            summary_data["敏感数据扫描次数"] = sensitive_data.get("scans_performed", 0)
            summary_data["敏感数据泄露检测"] = sensitive_data.get("leaks_detected", 0)

            if sensitive_data.get("leaks_detected", 0) > 0:
                overall_status = SecurityLevel.HIGH

        if configuration_data:
            report.configuration_summary = ConfigurationSummary(
                total_checks=configuration_data.get("total_checks", 0),
                passed_checks=configuration_data.get("passed_checks", 0),
                failed_checks=configuration_data.get("failed_checks", 0),
                warnings=configuration_data.get("warnings", []),
            )
            summary_data["配置检查通过"] = f"{configuration_data.get('passed_checks', 0)}/{configuration_data.get('total_checks', 0)}"

            if configuration_data.get("failed_checks", 0) > 0:
                overall_status = max(overall_status, SecurityLevel.MEDIUM)

        if violations:
            by_type: Dict[str, int] = {}
            by_severity: Dict[str, int] = {}

            for v in violations:
                vtype = v.get("violation_type", "unknown")
                severity = v.get("severity", "low")
                by_type[vtype] = by_type.get(vtype, 0) + 1
                by_severity[severity] = by_severity.get(severity, 0) + 1

            report.violation_summary = ViolationSummary(
                total_violations=len(violations),
                by_type=by_type,
                by_severity=by_severity,
                recent_violations=violations[:10],
            )
            summary_data["总违规数"] = len(violations)

            if "critical" in by_severity:
                overall_status = SecurityLevel.CRITICAL
            elif "high" in by_severity:
                overall_status = max(overall_status, SecurityLevel.HIGH)

        report.overall_status = overall_status
        report.summary = summary_data

        self._generate_recommendations(report)

        return report

    def _generate_recommendations(self, report: SecurityReport):
        """生成建议"""
        recommendations = []

        if report.permission_summary and report.permission_summary.overprivileged_roles:
            recommendations.append(
                f"审查以下角色的权限配置: {', '.join(report.permission_summary.overprivileged_roles)}"
            )

        if report.isolation_summary and report.isolation_summary.tests_failed > 0:
            recommendations.append(
                f"修复 {report.isolation_summary.tests_failed} 个租户隔离测试失败项"
            )

        if report.sensitive_data_summary and report.sensitive_data_summary.leaks_detected > 0:
            recommendations.append(
                "立即处理检测到的敏感信息泄露"
            )

        if report.configuration_summary and report.configuration_summary.failed_checks > 0:
            recommendations.append(
                f"修复 {report.configuration_summary.failed_checks} 个安全配置问题"
            )

        if report.violation_summary and report.violation_summary.total_violations > 0:
            recommendations.append(
                "审查最近的违规记录并采取纠正措施"
            )

        if not recommendations:
            recommendations.append("继续监控系统安全状态")
            recommendations.append("定期执行安全审计")

        report.recommendations = recommendations

    def export_report(
        self,
        report: SecurityReport,
        format: ReportFormat = ReportFormat.JSON,
    ) -> str:
        """
        导出报告

        Args:
            report: 安全报告
            format: 导出格式

        Returns:
            导出的报告内容
        """
        exporter = self.exporters.get(format)
        if not exporter:
            raise ValueError(f"Unsupported format: {format}")

        return exporter.export(report)

    def save_report(
        self,
        report: SecurityReport,
        file_path: str,
        format: ReportFormat = ReportFormat.JSON,
    ) -> bool:
        """
        保存报告到文件

        Args:
            report: 安全报告
            file_path: 文件路径
            format: 导出格式

        Returns:
            是否保存成功
        """
        try:
            content = self.export_report(report, format)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception:
            return False


_default_generator: Optional[SecurityReportGenerator] = None


def get_report_generator() -> SecurityReportGenerator:
    """获取报告生成器实例"""
    global _default_generator
    if _default_generator is None:
        _default_generator = SecurityReportGenerator()
    return _default_generator


def generate_security_report(
    title: str,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
    **kwargs,
) -> SecurityReport:
    """
    便捷函数：生成安全报告

    Args:
        title: 报告标题
        period_start: 报告周期开始
        period_end: 报告周期结束
        **kwargs: 其他数据

    Returns:
        SecurityReport 安全报告
    """
    generator = get_report_generator()
    return generator.generate_report(title, period_start, period_end, **kwargs)


def export_security_report(
    report: SecurityReport,
    format: ReportFormat = ReportFormat.JSON,
) -> str:
    """
    便捷函数：导出安全报告

    Args:
        report: 安全报告
        format: 导出格式

    Returns:
        导出的报告内容
    """
    generator = get_report_generator()
    return generator.export_report(report, format)

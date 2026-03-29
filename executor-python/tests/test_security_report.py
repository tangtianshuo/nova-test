"""
安全报告模块测试
================

测试安全状态报告生成和导出功能
"""

import pytest
import json
from datetime import datetime
from nova_executor.security.security_report import (
    ReportFormat,
    SecurityLevel,
    ReportSection,
    SecurityMetric,
    ViolationSummary,
    PermissionSummary,
    IsolationSummary,
    SensitiveDataSummary,
    ConfigurationSummary,
    SecurityReport,
    ReportExporter,
    JSONExporter,
    MarkdownExporter,
    HTMLExporter,
    SecurityReportGenerator,
    get_report_generator,
    generate_security_report,
    export_security_report,
)


class TestReportEnums:
    """测试报告枚举"""

    def test_report_format_values(self):
        """测试报告格式枚举值"""
        assert ReportFormat.JSON.value == "json"
        assert ReportFormat.HTML.value == "html"
        assert ReportFormat.MARKDOWN.value == "markdown"
        assert ReportFormat.PDF.value == "pdf"

    def test_security_level_values(self):
        """测试安全级别枚举值"""
        assert SecurityLevel.CRITICAL.value == "critical"
        assert SecurityLevel.HIGH.value == "high"
        assert SecurityLevel.MEDIUM.value == "medium"
        assert SecurityLevel.LOW.value == "low"
        assert SecurityLevel.PASS.value == "pass"


class TestSecurityReport:
    """测试安全报告"""

    def test_report_creation(self):
        """测试报告创建"""
        report = SecurityReport(
            report_id="test_001",
            title="Test Report",
            generated_at=datetime.now(),
        )

        assert report.report_id == "test_001"
        assert report.title == "Test Report"
        assert report.overall_status == SecurityLevel.PASS

    def test_report_to_dict(self):
        """测试报告转字典"""
        report = SecurityReport(
            report_id="test_001",
            title="Test Report",
            generated_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        result = report.to_dict()

        assert "report_id" in result
        assert "title" in result
        assert "generated_at" in result
        assert result["generated_at"] == "2024-01-01T12:00:00"

    def test_report_with_summaries(self):
        """测试带摘要的报告"""
        report = SecurityReport(
            report_id="test_001",
            title="Test Report",
            generated_at=datetime.now(),
            permission_summary=PermissionSummary(
                total_roles=5,
                total_permissions=30,
                critical_permissions=["admin:write"],
                overprivileged_roles=["super_admin"],
            ),
        )

        assert report.permission_summary is not None
        assert report.permission_summary.total_roles == 5


class TestJSONExporter:
    """测试 JSON 导出器"""

    def test_export_json(self):
        """测试导出 JSON 格式"""
        exporter = JSONExporter()
        report = SecurityReport(
            report_id="test_001",
            title="Test Report",
            generated_at=datetime(2024, 1, 1, 12, 0, 0),
            overall_status=SecurityLevel.PASS,
        )

        result = exporter.export(report)

        assert result is not None
        assert '"report_id": "test_001"' in result
        assert '"title": "Test Report"' in result

    def test_export_json_with_data(self):
        """测试导出带数据的 JSON"""
        exporter = JSONExporter()
        report = SecurityReport(
            report_id="test_001",
            title="Test Report",
            generated_at=datetime.now(),
            summary={"total_violations": 5, "tests_passed": 10},
            permission_summary=PermissionSummary(
                total_roles=5,
                total_permissions=30,
                critical_permissions=[],
                overprivileged_roles=[],
            ),
        )

        result = exporter.export(report)
        data = json.loads(result)

        assert data["summary"]["total_violations"] == 5
        assert data["permission_summary"]["total_roles"] == 5


class TestMarkdownExporter:
    """测试 Markdown 导出器"""

    def test_export_markdown(self):
        """测试导出 Markdown 格式"""
        exporter = MarkdownExporter()
        report = SecurityReport(
            report_id="test_001",
            title="Test Report",
            generated_at=datetime(2024, 1, 1, 12, 0, 0),
            overall_status=SecurityLevel.PASS,
        )

        result = exporter.export(report)

        assert "# Test Report" in result
        assert "**报告 ID**: test_001" in result
        assert "🟢 PASS" in result

    def test_export_markdown_with_violations(self):
        """测试导出带违规的 Markdown"""
        exporter = MarkdownExporter()
        report = SecurityReport(
            report_id="test_001",
            title="Test Report",
            generated_at=datetime.now(),
            overall_status=SecurityLevel.HIGH,
            violation_summary=ViolationSummary(
                total_violations=5,
                by_type={"CROSS_TENANT_ACCESS": 3},
                by_severity={"high": 3, "medium": 2},
                recent_violations=[],
            ),
        )

        result = exporter.export(report)

        assert "🟠 HIGH" in result
        assert "## 违规统计" in result
        assert "总违规数: 5" in result


class TestHTMLExporter:
    """测试 HTML 导出器"""

    def test_export_html(self):
        """测试导出 HTML 格式"""
        exporter = HTMLExporter()
        report = SecurityReport(
            report_id="test_001",
            title="Test Report",
            generated_at=datetime(2024, 1, 1, 12, 0, 0),
            overall_status=SecurityLevel.PASS,
        )

        result = exporter.export(report)

        assert "<!DOCTYPE html>" in result
        assert "<title>Test Report</title>" in result
        assert "Test Report" in result
        assert "PASS" in result

    def test_export_html_with_metrics(self):
        """测试导出带指标的 HTML"""
        exporter = HTMLExporter()
        report = SecurityReport(
            report_id="test_001",
            title="Test Report",
            generated_at=datetime.now(),
            overall_status=SecurityLevel.HIGH,
            summary={"总违规数": 10},
        )

        result = exporter.export(report)

        assert "总违规数" in result
        assert "10" in result


class TestSecurityReportGenerator:
    """测试安全报告生成器"""

    def test_generator_initialization(self):
        """测试生成器初始化"""
        generator = SecurityReportGenerator()
        assert generator is not None
        assert len(generator.exporters) == 3

    def test_generate_report_basic(self):
        """测试生成基础报告"""
        generator = SecurityReportGenerator()
        report = generator.generate_report(title="Test Security Report")

        assert report.report_id.startswith("sec_report_")
        assert report.title == "Test Security Report"
        assert report.generated_at is not None

    def test_generate_report_with_permission_data(self):
        """测试生成带权限数据的报告"""
        generator = SecurityReportGenerator()
        report = generator.generate_report(
            title="Test Report",
            permission_data={
                "total_roles": 5,
                "total_permissions": 30,
                "critical_permissions": ["admin:write"],
                "overprivileged_roles": [],
            },
        )

        assert report.permission_summary is not None
        assert report.permission_summary.total_roles == 5
        assert "总角色数" in report.summary

    def test_generate_report_with_isolation_data(self):
        """测试生成带隔离数据的报告"""
        generator = SecurityReportGenerator()
        report = generator.generate_report(
            title="Test Report",
            isolation_data={
                "isolation_level": "strict",
                "tests_passed": 10,
                "tests_failed": 2,
                "total_cross_tenant_attempts": 5,
                "blocked_attempts": 5,
            },
        )

        assert report.isolation_summary is not None
        assert report.isolation_summary.tests_passed == 10
        assert report.isolation_summary.tests_failed == 2
        assert report.overall_status == SecurityLevel.HIGH

    def test_generate_report_with_violations(self):
        """测试生成带违规的报告"""
        generator = SecurityReportGenerator()
        report = generator.generate_report(
            title="Test Report",
            violations=[
                {
                    "violation_type": "CROSS_TENANT_ACCESS",
                    "severity": "high",
                },
                {
                    "violation_type": "MISSING_TENANT_FILTER",
                    "severity": "medium",
                },
            ],
        )

        assert report.violation_summary is not None
        assert report.violation_summary.total_violations == 2
        assert report.overall_status == SecurityLevel.HIGH

    def test_generate_report_with_critical_violations(self):
        """测试生成带严重违规的报告"""
        generator = SecurityReportGenerator()
        report = generator.generate_report(
            title="Test Report",
            violations=[
                {
                    "violation_type": "CRITICAL_ISSUE",
                    "severity": "critical",
                },
            ],
        )

        assert report.overall_status == SecurityLevel.CRITICAL

    def test_generate_report_with_configuration_data(self):
        """测试生成带配置数据的报告"""
        generator = SecurityReportGenerator()
        report = generator.generate_report(
            title="Test Report",
            configuration_data={
                "total_checks": 20,
                "passed_checks": 18,
                "failed_checks": 2,
                "warnings": ["Check AUTH_001 failed"],
            },
        )

        assert report.configuration_summary is not None
        assert report.configuration_summary.failed_checks == 2
        assert report.overall_status == SecurityLevel.MEDIUM

    def test_export_report_json(self):
        """测试导出报告为 JSON"""
        generator = SecurityReportGenerator()
        report = generator.generate_report(title="Test Report")

        result = generator.export_report(report, ReportFormat.JSON)

        assert '"report_id"' in result
        assert '"title": "Test Report"' in result

    def test_export_report_markdown(self):
        """测试导出报告为 Markdown"""
        generator = SecurityReportGenerator()
        report = generator.generate_report(title="Test Report")

        result = generator.export_report(report, ReportFormat.MARKDOWN)

        assert "# Test Report" in result

    def test_export_report_html(self):
        """测试导出报告为 HTML"""
        generator = SecurityReportGenerator()
        report = generator.generate_report(title="Test Report")

        result = generator.export_report(report, ReportFormat.HTML)

        assert "<!DOCTYPE html>" in result
        assert "<title>Test Report</title>" in result

    def test_generate_recommendations_with_issues(self):
        """测试生成带问题的建议"""
        generator = SecurityReportGenerator()
        report = generator.generate_report(
            title="Test Report",
            isolation_data={
                "tests_failed": 5,
                "tests_passed": 10,
            },
            sensitive_data={
                "scans_performed": 10,
                "leaks_detected": 3,
                "by_type": {},
                "by_severity": {},
            },
        )

        assert len(report.recommendations) > 0
        assert any("隔离测试" in rec for rec in report.recommendations)
        assert any("敏感信息" in rec for rec in report.recommendations)

    def test_generate_recommendations_all_pass(self):
        """测试全部通过时的建议"""
        generator = SecurityReportGenerator()
        report = generator.generate_report(
            title="Test Report",
            isolation_data={
                "tests_failed": 0,
                "tests_passed": 15,
            },
        )

        assert len(report.recommendations) > 0
        assert any("监控" in rec or "审计" in rec for rec in report.recommendations)

    def test_save_report(self, tmp_path):
        """测试保存报告到文件"""
        generator = SecurityReportGenerator()
        report = generator.generate_report(title="Test Report")

        file_path = tmp_path / "report.json"
        result = generator.save_report(report, str(file_path), ReportFormat.JSON)

        assert result is True
        assert file_path.exists()

        content = file_path.read_text(encoding="utf-8")
        assert '"title": "Test Report"' in content


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_get_report_generator(self):
        """测试获取报告生成器"""
        generator = get_report_generator()
        assert generator is not None

        generator2 = get_report_generator()
        assert generator is generator2

    def test_generate_security_report(self):
        """测试便捷报告生成"""
        report = generate_security_report(
            title="Test Report",
            permission_data={
                "total_roles": 5,
                "total_permissions": 30,
                "critical_permissions": [],
                "overprivileged_roles": [],
            },
        )

        assert report.title == "Test Report"
        assert report.permission_summary is not None

    def test_export_security_report(self):
        """测试便捷报告导出"""
        report = generate_security_report(title="Test Report")

        result = export_security_report(report, ReportFormat.JSON)

        assert '"title": "Test Report"' in result


class TestReportIntegration:
    """测试报告集成"""

    def test_full_report_workflow(self):
        """测试完整报告工作流"""
        generator = SecurityReportGenerator()

        report = generator.generate_report(
            title="Monthly Security Report",
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
            permission_data={
                "total_roles": 6,
                "total_permissions": 35,
                "critical_permissions": ["admin:write", "instance:delete"],
                "overprivileged_roles": [],
            },
            isolation_data={
                "isolation_level": "strict",
                "tests_passed": 25,
                "tests_failed": 1,
                "total_cross_tenant_attempts": 10,
                "blocked_attempts": 10,
            },
            sensitive_data={
                "scans_performed": 100,
                "leaks_detected": 2,
                "by_type": {"token": 1, "password": 1},
                "by_severity": {"high": 2},
            },
            configuration_data={
                "total_checks": 19,
                "passed_checks": 18,
                "failed_checks": 1,
                "warnings": ["MFA configuration needed"],
            },
            violations=[
                {
                    "violation_type": "CROSS_TENANT_ACCESS",
                    "severity": "high",
                },
            ],
            metadata={
                "generated_by": "security_harness",
                "version": "1.0",
            },
        )

        assert report.title == "Monthly Security Report"
        assert report.period_start is not None
        assert report.period_end is not None
        assert report.permission_summary is not None
        assert report.isolation_summary is not None
        assert report.sensitive_data_summary is not None
        assert report.configuration_summary is not None
        assert report.violation_summary is not None
        assert report.overall_status == SecurityLevel.HIGH

        json_output = generator.export_report(report, ReportFormat.JSON)
        data = json.loads(json_output)
        assert data["summary"]["总角色数"] == 6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

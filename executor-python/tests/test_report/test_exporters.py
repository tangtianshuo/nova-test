"""
导出器测试
==========

验证 JSON/HTML/PDF 导出逻辑
"""

import pytest
from nova_executor.report.generator import ReportGenerator
from nova_executor.report.types import ReportStatus, StepRecord, ExportFormat
from nova_executor.report.exporters import JsonExporter, HtmlExporter, PdfExporter


@pytest.fixture
def sample_report():
    """创建样本报告"""
    import asyncio

    async def create_report():
        generator = ReportGenerator()
        steps = [
            StepRecord(
                step_number=1,
                node_name="init",
                action_type="screenshot",
                timestamp="2024-01-01T10:00:00",
            ),
            StepRecord(
                step_number=2,
                node_name="explore",
                action_type="click",
                action_target={"selector": "#submit"},
                confidence=0.9,
                timestamp="2024-01-01T10:00:05",
            ),
            StepRecord(
                step_number=3,
                node_name="execute",
                error="Element not found",
                is_defect=True,
                timestamp="2024-01-01T10:00:10",
            ),
        ]
        return await generator.generate(
            instance_id="test-instance",
            tenant_id="test-tenant",
            task_id="test-task",
            steps=steps,
        )

    return asyncio.run(create_report())


class TestJsonExporter:
    """JSON 导出器测试"""

    @pytest.mark.asyncio
    async def test_export_json(self, sample_report):
        """验证导出 JSON"""
        exporter = JsonExporter()
        result = await exporter.export(sample_report)

        assert isinstance(result, bytes)
        assert b'"instance_id"' in result
        assert b'"test-instance"' in result
        assert b'"summary"' in result
        assert b'"steps"' in result

    @pytest.mark.asyncio
    async def test_export_json_mask_sensitive_data(self, sample_report):
        """验证 JSON 脱敏"""
        exporter = JsonExporter()

        # 添加敏感信息到步骤
        sample_report.steps[0].action_params = {
            "password": "secret123",
            "token": "bearer_token",
        }

        result = await exporter.export(sample_report)
        result_str = result.decode("utf-8")

        assert "secret123" not in result_str
        assert "bearer_token" not in result_str
        assert "***MASKED***" in result_str


class TestHtmlExporter:
    """HTML 导出器测试"""

    @pytest.mark.asyncio
    async def test_export_html(self, sample_report):
        """验证导出 HTML"""
        exporter = HtmlExporter()
        result = await exporter.export(sample_report)

        assert isinstance(result, bytes)
        html_str = result.decode("utf-8")

        assert "<html" in html_str
        assert "<body>" in html_str
        assert "测试执行报告" in html_str
        assert sample_report.instance_id in html_str

    @pytest.mark.asyncio
    async def test_html_includes_metrics(self, sample_report):
        """验证 HTML 包含指标"""
        exporter = HtmlExporter()
        result = await exporter.export(sample_report)

        html_str = result.decode("utf-8")

        assert str(sample_report.summary.total_steps) in html_str
        assert str(sample_report.summary.total_defects) in html_str


class TestPdfExporter:
    """PDF 导出器测试"""

    @pytest.mark.asyncio
    async def test_export_pdf_returns_html_fallback(self, sample_report):
        """验证 PDF 返回 HTML 降级"""
        exporter = PdfExporter()
        result = await exporter.export(sample_report)

        # PDF 导出当前返回 HTML
        assert isinstance(result, bytes)
        html_str = result.decode("utf-8")
        assert "<html>" in html_str


class TestSensitiveDataMasking:
    """敏感信息脱敏测试"""

    @pytest.mark.asyncio
    async def test_mask_password(self, sample_report):
        """验证密码脱敏"""
        exporter = JsonExporter()
        sample_report.steps[0].action_params = {"password": "mysecretpassword"}

        result = await exporter.export(sample_report)
        result_str = result.decode("utf-8")

        assert "mysecretpassword" not in result_str

    @pytest.mark.asyncio
    async def test_mask_api_key(self, sample_report):
        """验证 API Key 脱敏"""
        exporter = JsonExporter()
        sample_report.steps[0].action_params = {"api_key": "sk-1234567890"}

        result = await exporter.export(sample_report)
        result_str = result.decode("utf-8")

        assert "sk-1234567890" not in result_str

    @pytest.mark.asyncio
    async def test_scan_sensitive_patterns(self, sample_report):
        """验证敏感信息扫描"""
        exporter = JsonExporter()

        # 测试扫描敏感信息
        test_data = 'token: "bearer_abc123"'
        findings = exporter.scan_sensitive_data(test_data)

        assert len(findings) >= 1
        assert any(f["type"] == "bearer_token" for f in findings)

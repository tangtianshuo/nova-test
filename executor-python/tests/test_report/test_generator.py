"""
报告生成器测试
==============

验证报告生成逻辑
"""

import pytest
from nova_executor.report.generator import ReportGenerator
from nova_executor.report.types import ReportStatus, StepRecord, HilRecord


@pytest.fixture
def generator():
    """创建报告生成器"""
    return ReportGenerator()


class TestReportGenerator:
    """报告生成器测试"""

    @pytest.mark.asyncio
    async def test_generate_report_with_steps(self, generator):
        """验证生成带步骤的报告"""
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
                action_target={"selector": "#btn"},
                confidence=0.9,
                timestamp="2024-01-01T10:00:05",
            ),
            StepRecord(
                step_number=3,
                node_name="execute",
                action_type="click",
                error="Element not found",
                is_defect=True,
                timestamp="2024-01-01T10:00:10",
            ),
        ]

        report = await generator.generate(
            instance_id="test-instance",
            tenant_id="test-tenant",
            task_id="test-task",
            steps=steps,
        )

        assert report.instance_id == "test-instance"
        assert report.status == ReportStatus.COMPLETED
        assert len(report.steps) == 3
        assert report.summary.total_steps == 3
        assert report.summary.successful_steps == 2
        assert report.summary.failed_steps == 1
        assert report.summary.total_defects >= 1

    @pytest.mark.asyncio
    async def test_generate_report_with_hil(self, generator):
        """验证生成带 HIL 记录的报告"""
        steps = [
            StepRecord(
                step_number=1,
                node_name="init",
                action_type="screenshot",
                timestamp="2024-01-01T10:00:00",
            ),
            StepRecord(
                step_number=2,
                node_name="check_hil",
                action_type="click",
                confidence=0.5,
                timestamp="2024-01-01T10:00:05",
            ),
        ]

        hil_records = [
            HilRecord(
                ticket_id="ticket-1",
                step_number=2,
                reason="Low confidence",
                risk_level="MEDIUM",
                decision="APPROVED",
                human_feedback="Looks safe",
                resolved_at="2024-01-01T10:00:10",
            ),
        ]

        report = await generator.generate(
            instance_id="test-instance",
            tenant_id="test-tenant",
            task_id="test-task",
            steps=steps,
            hil_records=hil_records,
        )

        assert len(report.hil_records) == 1
        assert report.summary.hil_count == 1

    @pytest.mark.asyncio
    async def test_generate_summary_only(self, generator):
        """验证仅生成摘要"""
        steps = [
            StepRecord(
                step_number=1,
                node_name="init",
                timestamp="2024-01-01T10:00:00",
            ),
            StepRecord(
                step_number=2,
                node_name="verify",
                timestamp="2024-01-01T10:00:10",
            ),
        ]

        summary = await generator.generate_summary_only(steps)

        assert summary.total_steps == 2
        assert summary.success_rate == 1.0


class TestSummaryBuilder:
    """摘要构建器测试"""

    def test_calculate_success_rate(self):
        """验证计算成功率"""
        from nova_executor.report.summary_builder import SummaryBuilder

        builder = SummaryBuilder()
        builder.add_step(StepRecord(step_number=1, node_name="test", timestamp="2024-01-01T10:00:00"))
        builder.add_step(StepRecord(step_number=2, node_name="test", timestamp="2024-01-01T10:00:05"))
        builder.add_step(StepRecord(step_number=3, node_name="test", error="Failed", timestamp="2024-01-01T10:00:10"))

        summary = builder.build()

        assert summary.total_steps == 3
        assert summary.successful_steps == 2
        assert summary.failed_steps == 1
        assert summary.success_rate == pytest.approx(2 / 3, rel=0.01)


class TestDefectAggregator:
    """缺陷聚合器测试"""

    def test_extract_defect_from_error(self):
        """验证从错误提取缺陷"""
        from nova_executor.report.defect_aggregator import DefectAggregator

        aggregator = DefectAggregator()
        step = StepRecord(
            step_number=1,
            node_name="execute",
            error="Element #btn not found",
            timestamp="2024-01-01T10:00:00",
        )

        aggregator.add_step(step)
        defects = aggregator.build()

        assert len(defects) == 1
        assert defects[0]["error_type"] == "element_not_found"

    def test_classify_timeout_error(self):
        """验证分类超时错误"""
        from nova_executor.report.defect_aggregator import DefectAggregator

        aggregator = DefectAggregator()
        step = StepRecord(
            step_number=1,
            node_name="execute",
            error="Timeout waiting for element",
            timestamp="2024-01-01T10:00:00",
        )

        aggregator.add_step(step)
        defects = aggregator.build()

        assert len(defects) == 1
        assert defects[0]["error_type"] == "timeout"
        assert defects[0]["severity"] == "MEDIUM"

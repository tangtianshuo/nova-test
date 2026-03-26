"""
报告生成器
==========

从执行数据生成完整报告

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求
"""

import logging
import uuid
from typing import List, Optional
from datetime import datetime

from nova_executor.report.types import (
    Report,
    ReportStatus,
    StepRecord,
    HilRecord,
    ReportSummary,
)
from nova_executor.report.summary_builder import SummaryBuilder
from nova_executor.report.defect_aggregator import DefectAggregator

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    报告生成器

    功能：
    1. 聚合步骤数据
    2. 构建摘要
    3. 聚合缺陷
    4. 关联 HIL 记录
    5. 生成完整报告
    """

    def __init__(self):
        self.summary_builder = SummaryBuilder()
        self.defect_aggregator = DefectAggregator()

    async def generate(
        self,
        instance_id: str,
        tenant_id: str,
        task_id: str,
        steps: List[StepRecord],
        hil_records: Optional[List[HilRecord]] = None,
    ) -> Report:
        """
        生成报告

        Args:
            instance_id: 实例 ID
            tenant_id: 租户 ID
            task_id: 任务 ID
            steps: 步骤记录列表
            hil_records: HIL 决策记录列表

        Returns:
            完整报告
        """
        logger.info(f"[Report] 生成报告: instance={instance_id}, steps={len(steps)}")

        # 重置聚合器
        self.summary_builder.reset()
        self.defect_aggregator.reset()

        # 添加步骤并提取缺陷
        for step in steps:
            self.summary_builder.add_step(step)
            self.defect_aggregator.add_step(step)

        # 添加 HIL 计数
        if hil_records:
            self.summary_builder.add_hil_count(len(hil_records))

        # 构建摘要
        summary = self.summary_builder.build()

        # 聚合缺陷
        defects = self.defect_aggregator.build()

        # 更新严重缺陷数
        summary.total_defects = len(defects)
        summary.critical_defects = sum(1 for d in defects if d.get("severity") == "CRITICAL")

        # 创建报告
        report = Report(
            report_id=str(uuid.uuid4()),
            instance_id=instance_id,
            tenant_id=tenant_id,
            task_id=task_id,
            status=ReportStatus.COMPLETED,
            summary=summary,
            steps=steps,
            hil_records=hil_records or [],
            defects=defects,
        )

        logger.info(
            f"[Report] 报告生成完成: report={report.report_id}, "
            f"defects={summary.total_defects}, "
            f"hil={summary.hil_count}"
        )

        return report

    async def generate_summary_only(
        self,
        steps: List[StepRecord],
    ) -> ReportSummary:
        """
        仅生成摘要（轻量级）

        Args:
            steps: 步骤记录列表

        Returns:
            报告摘要
        """
        self.summary_builder.reset()

        for step in steps:
            self.summary_builder.add_step(step)

        return self.summary_builder.build()

"""
摘要构建器
==========

从执行数据构建报告摘要

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求
"""

import logging
from typing import List, Optional
from datetime import datetime

from nova_executor.report.types import StepRecord, ReportSummary

logger = logging.getLogger(__name__)


class SummaryBuilder:
    """
    报告摘要构建器

    功能：
    1. 计算执行统计
    2. 聚合步骤结果
    3. 生成成功率等指标
    """

    def __init__(self):
        self.total_steps = 0
        self.successful_steps = 0
        self.failed_steps = 0
        self.hil_count = 0
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None

    def reset(self):
        """重置计数器"""
        self.total_steps = 0
        self.successful_steps = 0
        self.failed_steps = 0
        self.hil_count = 0
        self.started_at = None
        self.completed_at = None

    def add_step(self, step: StepRecord):
        """
        添加步骤

        Args:
            step: 步骤记录
        """
        self.total_steps += 1

        # 判断成功/失败
        if step.error:
            self.failed_steps += 1
        else:
            self.successful_steps += 1

        # 更新开始时间
        if step.timestamp and not self.started_at:
            self.started_at = step.timestamp

        # 更新结束时间
        if step.timestamp:
            self.completed_at = step.timestamp

    def add_hil_count(self, count: int = 1):
        """添加 HIL 计数"""
        self.hil_count += count

    def calculate_success_rate(self) -> float:
        """计算成功率"""
        if self.total_steps == 0:
            return 0.0
        return round(self.successful_steps / self.total_steps, 2)

    def calculate_duration(self) -> float:
        """计算执行时长（秒）"""
        if not self.started_at or not self.completed_at:
            return 0.0

        try:
            start = datetime.fromisoformat(self.started_at)
            end = datetime.fromisoformat(self.completed_at)
            return (end - start).total_seconds()
        except Exception:
            return 0.0

    def build(self) -> ReportSummary:
        """
        构建报告摘要

        Returns:
            报告摘要对象
        """
        duration = self.calculate_duration()
        success_rate = self.calculate_success_rate()

        summary = ReportSummary(
            total_steps=self.total_steps,
            successful_steps=self.successful_steps,
            failed_steps=self.failed_steps,
            total_defects=self.failed_steps,
            critical_defects=0,  # TODO: 根据缺陷严重程度计算
            hil_count=self.hil_count,
            execution_duration_seconds=duration,
            success_rate=success_rate,
            started_at=self.started_at,
            completed_at=self.completed_at,
        )

        logger.info(
            f"[Summary] 构建摘要: steps={self.total_steps}, "
            f"success={self.successful_steps}, "
            f"failed={self.failed_steps}, "
            f"rate={success_rate}"
        )

        return summary

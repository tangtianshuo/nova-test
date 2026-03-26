"""
缺陷聚合器
==========

从步骤记录聚合缺陷信息

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求
"""

import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from nova_executor.report.types import StepRecord

logger = logging.getLogger(__name__)


@dataclass
class Defect:
    """
    缺陷信息

    属性:
        step_number: 步骤编号
        node_name: 节点名称
        error_type: 错误类型
        error_message: 错误消息
        screenshot_url: 截图 URL
        severity: 严重程度 (LOW, MEDIUM, HIGH, CRITICAL)
    """
    step_number: int
    node_name: str
    error_type: str
    error_message: str
    screenshot_url: Optional[str] = None
    severity: str = "MEDIUM"


class DefectSummary:
    """
    缺陷汇总

    属性:
        total: 总数
        critical: 严重
        high: 高
        medium: 中
        low: 低
        defects: 缺陷列表
    """
    total: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    defects: List[Defect] = None

    def __post_init__(self):
        if self.defects is None:
            self.defects = []


class DefectAggregator:
    """
    缺陷聚合器

    功能：
    1. 从步骤记录提取缺陷
    2. 分类缺陷严重程度
    3. 生成缺陷汇总
    """

    # 错误类型到严重程度的映射
    ERROR_SEVERITY_MAP = {
        "element_not_found": "HIGH",
        "timeout": "MEDIUM",
        "navigation_error": "HIGH",
        "assertion_failed": "LOW",
        "unknown_element": "MEDIUM",
        "execution_failed": "CRITICAL",
        "parse_error": "MEDIUM",
        "network_error": "HIGH",
    }

    def __init__(self):
        self.defects: List[Defect] = []

    def reset(self):
        """重置"""
        self.defects = []

    def add_step(self, step: StepRecord):
        """
        添加步骤并提取缺陷

        Args:
            step: 步骤记录
        """
        if step.error:
            defect = self._extract_defect(step)
            if defect:
                self.defects.append(defect)
                logger.info(
                    f"[Defect] 提取缺陷: step={step.step_number}, "
                    f"type={defect.error_type}, severity={defect.severity}"
                )

    def _extract_defect(self, step: StepRecord) -> Optional[Defect]:
        """
        从步骤提取缺陷

        Args:
            step: 步骤记录

        Returns:
            缺陷信息或 None
        """
        if not step.error:
            return None

        # 解析错误类型
        error_type = self._classify_error(step.error)
        severity = self.ERROR_SEVERITY_MAP.get(error_type, "MEDIUM")

        # 检查是否标记为缺陷
        if step.is_defect:
            severity = "HIGH"

        return Defect(
            step_number=step.step_number,
            node_name=step.node_name,
            error_type=error_type,
            error_message=step.error,
            screenshot_url=step.screenshot_url,
            severity=severity,
        )

    def _classify_error(self, error: str) -> str:
        """
        分类错误类型

        Args:
            error: 错误消息

        Returns:
            错误类型
        """
        error_lower = error.lower()

        if "not found" in error_lower or "no such element" in error_lower:
            return "element_not_found"
        if "timeout" in error_lower:
            return "timeout"
        if "navigation" in error_lower or "failed to navigate" in error_lower:
            return "navigation_error"
        if "assert" in error_lower or "assertion" in error_lower:
            return "assertion_failed"
        if "unknown" in error_lower or "unrecognized" in error_lower:
            return "unknown_element"
        if "network" in error_lower or "connection" in error_lower:
            return "network_error"
        if "parse" in error_lower or "json" in error_lower:
            return "parse_error"

        return "execution_failed"

    def build(self) -> List[Dict[str, Any]]:
        """
        构建缺陷汇总

        Returns:
            缺陷汇总列表
        """
        summary = DefectSummary(defects=self.defects)
        summary.total = len(self.defects)

        for defect in self.defects:
            if defect.severity == "CRITICAL":
                summary.critical += 1
            elif defect.severity == "HIGH":
                summary.high += 1
            elif defect.severity == "MEDIUM":
                summary.medium += 1
            else:
                summary.low += 1

        logger.info(
            f"[Defect] 聚合完成: total={summary.total}, "
            f"critical={summary.critical}, high={summary.high}, "
            f"medium={summary.medium}, low={summary.low}"
        )

        return [
            {
                "step_number": d.step_number,
                "node_name": d.node_name,
                "error_type": d.error_type,
                "error_message": d.error_message,
                "screenshot_url": d.screenshot_url,
                "severity": d.severity,
            }
            for d in self.defects
        ]


from typing import Optional

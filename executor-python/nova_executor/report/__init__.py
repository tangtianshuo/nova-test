"""
报告模块
========

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求
"""

from nova_executor.report.generator import ReportGenerator, Report
from nova_executor.report.summary_builder import SummaryBuilder, ReportSummary
from nova_executor.report.defect_aggregator import DefectAggregator, Defect, DefectSummary
from nova_executor.report.exporters.base import Exporter, ExportFormat

__all__ = [
    "ReportGenerator",
    "Report",
    "SummaryBuilder",
    "ReportSummary",
    "DefectAggregator",
    "Defect",
    "DefectSummary",
    "Exporter",
    "ExportFormat",
]

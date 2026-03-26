"""
JSON 导出器
============

导出符合 ReportSchema 的 JSON 格式

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求
"""

import logging
from typing import Optional

from nova_executor.report.types import Report, ExportFormat
from nova_executor.report.exporters.base import Exporter

logger = logging.getLogger(__name__)


class JsonExporter(Exporter):
    """
    JSON 导出器

    输出符合 ReportSchema 的 JSON 格式
    """

    def get_format(self) -> ExportFormat:
        return ExportFormat.JSON

    async def export(self, report: Report) -> bytes:
        """
        导出 JSON 格式报告

        Args:
            report: 报告对象

        Returns:
            JSON 字节数据
        """
        logger.info(f"[JsonExporter] 导出报告: {report.report_id}")

        # 转换为字典
        data = report.model_dump()

        # 添加 schema 版本
        data["schema_version"] = report.schema_version

        # 序列化 JSON
        import json
        json_str = json.dumps(data, indent=2, ensure_ascii=False)

        # 脱敏处理
        json_str = self.mask_sensitive_data(json_str)

        # 验证敏感信息已被脱敏
        findings = self.scan_sensitive_data(json_str)
        if findings:
            logger.warning(
                f"[JsonExporter] 发现 {len(findings)} 处敏感信息未完全脱敏: "
                f"{[f['type'] for f in findings]}"
            )

        return json_str.encode("utf-8")

    async def export_with_validation(self, report: Report) -> tuple[bytes, bool]:
        """
        导出 JSON 并验证

        Args:
            report: 报告对象

        Returns:
            (JSON 字节数据, 是否有效)
        """
        data = report.model_dump()
        json_str = self.mask_sensitive_data(data)

        # 检查敏感信息
        findings = self.scan_sensitive_data(json_str)
        is_valid = len(findings) == 0

        return json_str.encode("utf-8"), is_valid

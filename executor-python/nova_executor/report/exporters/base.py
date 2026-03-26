"""
导出器基类和接口
================

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求

导出器采用接口隔离原则（ISP），每种格式有独立实现
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import Optional

from nova_executor.report.types import Report, ExportFormat

logger = logging.getLogger(__name__)


# 敏感信息模式
SENSITIVE_PATTERNS = [
    (r'password["\']?\s*[:=]\s*["\']?[^"\']+["\']?', "password"),
    (r'token["\']?\s*[:=]\s*["\']?[^"\']+["\']?', "token"),
    (r'api[_-]?key["\']?\s*[:=]\s*["\']?[^"\']+["\']?', "api_key"),
    (r'secret["\']?\s*[:=]\s*["\']?[^"\']+["\']?', "secret"),
    (r'bearer\s+[a-zA-Z0-9\-_.~+/]+=*', "bearer_token"),
    (r'aws[_-]?access[_-]?key[_-]?id["\']?\s*[:=]\s*["\']?[^"\']+["\']?', "aws_key"),
    (r'Authorization["\']?\s*[:=]\s*["\']?[^"\']+["\']?', "authorization"),
]


class Exporter(ABC):
    """
    导出器基类

    导出器遵循单一职责原则（SRP），每种格式独立实现
    """

    @abstractmethod
    async def export(self, report: Report) -> bytes:
        """
        导出报告

        Args:
            report: 报告对象

        Returns:
            导出的字节数据
        """
        pass

    @abstractmethod
    def get_format(self) -> ExportFormat:
        """获取导出格式"""
        pass

    def scan_sensitive_data(self, data: str) -> list[dict]:
        """
        扫描敏感信息

        Args:
            data: 待扫描的字符串

        Returns:
            敏感信息列表
        """
        findings = []

        for pattern, field_type in SENSITIVE_PATTERNS:
            matches = re.finditer(pattern, data, re.IGNORECASE)
            for match in matches:
                findings.append({
                    "type": field_type,
                    "match": match.group(),
                    "position": match.start(),
                })

        return findings

    def mask_sensitive_data(self, data: str) -> str:
        """
        脱敏敏感信息

        Args:
            data: 待脱敏的字符串

        Returns:
            脱敏后的字符串
        """
        result = data

        # 掩码 token、password、api_key 等
        for pattern, field_type in SENSITIVE_PATTERNS:
            # 掩码敏感字段值
            if field_type in ["password", "token", "api_key", "secret", "aws_key"]:
                result = re.sub(
                    pattern,
                    f'{field_type}: "***MASKED***"',
                    result,
                    flags=re.IGNORECASE
                )

        return result


class ExporterFactory:
    """导出器工厂"""

    _exporters = {
        ExportFormat.JSON: None,
        ExportFormat.HTML: None,
        ExportFormat.PDF: None,
    }

    @classmethod
    def get_exporter(cls, format: ExportFormat) -> Exporter:
        """获取导出器实例"""
        if cls._exporters.get(format) is None:
            if format == ExportFormat.JSON:
                cls._exporters[format] = JsonExporter()
            elif format == ExportFormat.HTML:
                cls._exporters[format] = HtmlExporter()
            elif format == ExportFormat.PDF:
                cls._exporters[format] = PdfExporter()

        return cls._exporters[format]

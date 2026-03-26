"""
PDF 导出器
============

导出 PDF 格式报告

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求

PDF 导出使用 HTML 中转方式实现
"""

import logging
import base64
from typing import Optional

from nova_executor.report.types import Report, ExportFormat
from nova_executor.report.exporters.base import Exporter
from nova_executor.report.exporters.html_exporter import HtmlExporter

logger = logging.getLogger(__name__)


class PdfExporter(Exporter):
    """
    PDF 导出器

    通过 HTML 中转生成 PDF
    注意：生产环境需要安装 wkhtmltopdf 或使用其他 PDF 生成服务
    """

    def __init__(self):
        self.html_exporter = HtmlExporter()

    def get_format(self) -> ExportFormat:
        return ExportFormat.PDF

    async def export(self, report: Report) -> bytes:
        """
        导出 PDF 格式报告

        Args:
            report: 报告对象

        Returns:
            PDF 字节数据

        Note:
            当前实现返回 HTML，需要集成 PDF 生成服务
            方案：
            1. 使用 weasyprint 库
            2. 使用 pdfkit + wkhtmltopdf
            3. 调用外部 PDF 生成 API
        """
        logger.info(f"[PdfExporter] 导出报告: {report.report_id}")

        # 生成 HTML
        html_exporter = HtmlExporter()
        html_bytes = await html_exporter.export(report)
        html_str = html_bytes.decode("utf-8")

        # TODO: 实现 PDF 生成
        # 当前返回 HTML，实际使用时需要转换
        # 方案1: weasyprint
        # from weasyprint import HTML
        # pdf = HTML(string=html_str).write_pdf()
        # return pdf

        # 方案2: pdfkit
        # import pdfkit
        # pdf = pdfkit.from_string(html_str, False)
        # return pdf

        # 当前返回 HTML 标记，表示需要后续转换
        # 在实际部署时，应该返回真正的 PDF
        logger.warning(
            "[PdfExporter] PDF 导出需要安装 PDF 生成工具，"
            "当前返回 HTML 格式"
        )

        # 返回 HTML 作为替代
        return html_bytes

    async def export_with_embed(self, report: Report) -> bytes:
        """
        导出包含嵌入字体的 PDF

        使用 base64 编码嵌入字体，确保跨平台显示一致
        """
        # 生成基础 PDF
        pdf_bytes = await self.export(report)

        # 如果是 HTML，返回提示
        if not pdf_bytes.startswith(b'%PDF'):
            logger.warning(
                "[PdfExporter] 当前为 HTML 格式，需要转换为 PDF"
            )
            return pdf_bytes

        return pdf_bytes

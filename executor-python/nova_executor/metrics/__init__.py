"""
指标模块
==========

Prometheus 指标采集

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求
"""

from nova_executor.metrics.collector import MetricsCollector, metrics

__all__ = ["MetricsCollector", "metrics"]

"""
指标收集器
============

Prometheus 指标采集

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求
"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """指标类型"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


@dataclass
class Metric:
    """指标定义"""
    name: str
    description: str
    metric_type: MetricType
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """
    指标收集器

    采集并暴露系统指标

    指标定义：
    - nova_instances_total: 实例总数
    - nova_instances_running: 运行中实例数
    - nova_instances_completed: 已完成实例数
    - nova_instances_failed: 失败实例数
    - nova_hil_tickets_total: HIL 工单总数
    - nova_task_execution_seconds: 任务执行时长
    - nova_api_requests_total: API 请求总数
    - nova_api_request_duration_seconds: API 请求延迟
    """

    def __init__(self):
        self._metrics: Dict[str, Metric] = {}
        self._init_metrics()

    def _init_metrics(self):
        """初始化指标"""
        self._metrics = {
            "instances_total": Metric(
                name="nova_instances_total",
                description="实例总数",
                metric_type=MetricType.COUNTER,
            ),
            "instances_running": Metric(
                name="nova_instances_running",
                description="运行中实例数",
                metric_type=MetricType.GAUGE,
            ),
            "instances_completed": Metric(
                name="nova_instances_completed",
                description="已完成实例数",
                metric_type=MetricType.COUNTER,
            ),
            "instances_failed": Metric(
                name="nova_instances_failed",
                description="失败实例数",
                metric_type=MetricType.COUNTER,
            ),
            "hil_tickets_total": Metric(
                name="nova_hil_tickets_total",
                description="HIL 工单总数",
                metric_type=MetricType.COUNTER,
            ),
            "task_execution_seconds": Metric(
                name="nova_task_execution_seconds",
                description="任务执行时长 Histogram",
                metric_type=MetricType.HISTOGRAM,
            ),
            "api_requests_total": Metric(
                name="nova_api_requests_total",
                description="API 请求总数",
                metric_type=MetricType.COUNTER,
            ),
            "api_request_duration_seconds": Metric(
                name="nova_api_request_duration_seconds",
                description="API 请求延迟",
                metric_type=MetricType.HISTOGRAM,
            ),
        }
        logger.info("[Metrics] 指标收集器已初始化")

    def inc(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """
        增加计数器

        Args:
            name: 指标名称
            value: 增加的值
            labels: 标签
        """
        if name not in self._metrics:
            logger.warning(f"[Metrics] 未知指标: {name}")
            return

        metric = self._metrics[name]
        metric.value += value
        metric.labels = labels or {}
        logger.debug(f"[Metrics] {name} += {value}")

    def set(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        设置 Gauge 值

        Args:
            name: 指标名称
            value: 设置的值
            labels: 标签
        """
        if name not in self._metrics:
            logger.warning(f"[Metrics] 未知指标: {name}")
            return

        metric = self._metrics[name]
        metric.value = value
        metric.labels = labels or {}
        logger.debug(f"[Metrics] {name} = {value}")

    def observe(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        观察 Histogram 值

        Args:
            name: 指标名称
            value: 观察的值
            labels: 标签
        """
        if name not in self._metrics:
            logger.warning(f"[Metrics] 未知指标: {name}")
            return

        metric = self._metrics[name]
        metric.value = value
        metric.labels = labels or {}
        logger.debug(f"[Metrics] {name} observed: {value}")

    def get_metrics(self) -> str:
        """
        获取 Prometheus 格式的指标

        Returns:
            Prometheus 格式的指标文本
        """
        lines = []

        for metric in self._metrics.values():
            # HELP 行
            lines.append(f"# HELP {metric.name} {metric.description}")

            # TYPE 行
            lines.append(f"# TYPE {metric.name} {metric.metric_type.value}")

            # 指标值
            labels_str = ",".join(
                f'{k}="{v}"' for k, v in metric.labels.items()
            )
            if labels_str:
                lines.append(f"{metric.name}{{{labels_str}}} {metric.value}")
            else:
                lines.append(f"{metric.name} {metric.value}")

        return "\n".join(lines) + "\n"

    def reset(self):
        """重置所有指标"""
        for metric in self._metrics.values():
            metric.value = 0.0
            metric.labels = {}
        logger.info("[Metrics] 指标已重置")


# 全局指标收集器实例
metrics = MetricsCollector()


# 便捷函数
def inc_instance():
    """实例数 +1"""
    metrics.inc("instances_total")


def set_running_instances(count: int):
    """设置运行中实例数"""
    metrics.set("instances_running", count)


def inc_completed():
    """已完成实例 +1"""
    metrics.inc("instances_completed")


def inc_failed():
    """失败实例 +1"""
    metrics.inc("instances_failed")


def inc_hil_ticket():
    """HIL 工单 +1"""
    metrics.inc("hil_tickets_total")


def observe_execution_duration(seconds: float):
    """观察执行时长"""
    metrics.observe("task_execution_seconds", seconds)


def inc_api_request(labels: Optional[Dict[str, str]] = None):
    """API 请求 +1"""
    metrics.inc("api_requests_total", labels=labels)


def observe_request_duration(seconds: float, labels: Optional[Dict[str, str]] = None):
    """观察请求延迟"""
    metrics.observe("api_request_duration_seconds", seconds, labels=labels)

"""
指标收集器
============

Prometheus 指标采集

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求
"""

import logging
from typing import Dict, Optional
from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST

logger = logging.getLogger(__name__)


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

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._registry = registry or CollectorRegistry()
        self._init_metrics()

    def _init_metrics(self):
        """初始化指标"""
        self._counters = {
            "instances_total": Counter(
                "nova_instances_total",
                "实例总数",
                registry=self._registry,
            ),
            "instances_completed": Counter(
                "nova_instances_completed",
                "已完成实例数",
                registry=self._registry,
            ),
            "instances_failed": Counter(
                "nova_instances_failed",
                "失败实例数",
                registry=self._registry,
            ),
            "hil_tickets_total": Counter(
                "nova_hil_tickets_total",
                "HIL 工单总数",
                registry=self._registry,
            ),
            "api_requests_total": Counter(
                "nova_api_requests_total",
                "API 请求总数",
                ["method", "endpoint", "status"],
                registry=self._registry,
            ),
        }

        self._gauges = {
            "instances_running": Gauge(
                "nova_instances_running",
                "运行中实例数",
                registry=self._registry,
            ),
        }

        self._histograms = {
            "task_execution_seconds": Histogram(
                "nova_task_execution_seconds",
                "任务执行时长",
                buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0),
                registry=self._registry,
            ),
            "api_request_duration_seconds": Histogram(
                "nova_api_request_duration_seconds",
                "API 请求延迟",
                ["method", "endpoint"],
                buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
                registry=self._registry,
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
        if name not in self._counters:
            logger.warning(f"[Metrics] 未知计数器指标: {name}")
            return

        if labels:
            self._counters[name].labels(**labels).inc(value)
        else:
            self._counters[name].inc(value)

        logger.debug(f"[Metrics] {name} += {value}")

    def set(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        设置 Gauge 值

        Args:
            name: 指标名称
            value: 设置的值
            labels: 标签
        """
        if name not in self._gauges:
            logger.warning(f"[Metrics] 未知 Gauge 指标: {name}")
            return

        if labels:
            self._gauges[name].labels(**labels).set(value)
        else:
            self._gauges[name].set(value)

        logger.debug(f"[Metrics] {name} = {value}")

    def observe(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        观察 Histogram 值

        Args:
            name: 指标名称
            value: 观察的值
            labels: 标签
        """
        if name not in self._histograms:
            logger.warning(f"[Metrics] 未知 Histogram 指标: {name}")
            return

        if labels:
            self._histograms[name].labels(**labels).observe(value)
        else:
            self._histograms[name].observe(value)

        logger.debug(f"[Metrics] {name} observed: {value}")

    def get_metrics(self) -> bytes:
        """
        获取 Prometheus 格式的指标

        Returns:
            Prometheus 格式的指标字节
        """
        return generate_latest(self._registry)

    def get_metrics_text(self) -> str:
        """
        获取 Prometheus 格式的指标文本

        Returns:
            Prometheus 格式的指标文本
        """
        return self.get_metrics().decode("utf-8")

    def get_content_type(self) -> str:
        """
        获取 Prometheus 内容类型

        Returns:
            Content-Type
        """
        return CONTENT_TYPE_LATEST

    def reset(self):
        """重置所有指标"""
        for counter in self._counters.values():
            if hasattr(counter, "_metrics"):
                counter._metrics.clear()

        for gauge in self._gauges.values():
            gauge._metrics.clear()

        logger.info("[Metrics] 指标已重置")

    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """别名：增加计数器"""
        self.inc(name, value, labels)

    def get_counter(self, name: str) -> float:
        """获取计数器值（仅用于测试）"""
        if name not in self._counters:
            return 0.0
        return 0.0

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """别名：设置 Gauge"""
        self.set(name, value, labels)

    def get_gauge(self, name: str) -> float:
        """获取 Gauge 值（仅用于测试）"""
        if name not in self._gauges:
            return 0.0
        return 0.0

    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """别名：观察直方图"""
        self.observe(name, value, labels)

    def get_histogram(self, name: str) -> list:
        """获取直方图值（仅用于测试）"""
        return []


class Timer:
    """计时器上下文管理器"""

    def __init__(self, collector: MetricsCollector, name: str, labels: Optional[Dict[str, str]] = None):
        self.collector = collector
        self.name = name
        self.labels = labels
        self.start_time = None

    def __enter__(self):
        import time
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        import time
        duration = time.time() - self.start_time
        self.collector.observe(self.name, duration, self.labels)

    def get_duration(self) -> float:
        """获取持续时间"""
        import time
        return time.time() - self.start_time if self.start_time else 0.0


def timer(self, name: str, labels: Optional[Dict[str, str]] = None) -> Timer:
    """创建计时器"""
    return Timer(self, name, labels)


MetricsCollector.timer = timer


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

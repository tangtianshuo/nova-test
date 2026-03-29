"""
指标收集测试
============

验证指标收集和导出
"""

import pytest
from prometheus_client import CollectorRegistry
from nova_executor.metrics.collector import MetricsCollector, Timer


@pytest.fixture
def metrics_collector():
    """创建独立的指标收集器"""
    return MetricsCollector(CollectorRegistry())


class TestMetricsCollector:
    """指标收集器测试"""

    def test_create_collector(self, metrics_collector):
        """验证创建收集器"""
        assert metrics_collector is not None
        assert hasattr(metrics_collector, "_counters")
        assert hasattr(metrics_collector, "_gauges")
        assert hasattr(metrics_collector, "_histograms")

    def test_increment_counter(self, metrics_collector):
        """验证增加计数器"""
        metrics_collector.increment_counter("instances_total")
        metrics_collector.increment_counter("instances_total", 5)

    def test_set_gauge(self, metrics_collector):
        """验证设置计量器"""
        metrics_collector.set_gauge("instances_running", 10)
        metrics_collector.set_gauge("instances_running", 5)

    def test_observe_histogram(self, metrics_collector):
        """验证观察直方图"""
        metrics_collector.observe_histogram("task_execution_seconds", 100)
        metrics_collector.observe_histogram("task_execution_seconds", 200)
        metrics_collector.observe_histogram("task_execution_seconds", 150)

    def test_get_metrics_text(self, metrics_collector):
        """验证获取指标文本"""
        metrics_collector.increment_counter("instances_total")
        metrics_collector.set_gauge("instances_running", 10)
        metrics_collector.observe_histogram("task_execution_seconds", 100)
        metrics_text = metrics_collector.get_metrics_text()
        assert isinstance(metrics_text, str)
        assert "nova_instances_total" in metrics_text
        assert "nova_instances_running" in metrics_text
        assert "nova_task_execution_seconds" in metrics_text

    def test_get_metrics_bytes(self, metrics_collector):
        """验证获取指标字节"""
        metrics_bytes = metrics_collector.get_metrics()
        assert isinstance(metrics_bytes, bytes)

    def test_get_content_type(self, metrics_collector):
        """验证获取内容类型"""
        content_type = metrics_collector.get_content_type()
        assert isinstance(content_type, str)
        assert "text/plain" in content_type or "openmetrics" in content_type

    def test_increment_counter_with_labels(self, metrics_collector):
        """验证带标签的计数器增加"""
        metrics_collector.increment_counter("api_requests_total", labels={"method": "GET", "endpoint": "/health", "status": "200"})

    def test_set_gauge_with_labels(self, metrics_collector):
        """验证带标签的 Gauge 设置"""
        metrics_collector.set_gauge("instances_running", 10)

    def test_observe_histogram_with_labels(self, metrics_collector):
        """验证带标签的直方图观察"""
        metrics_collector.observe_histogram("api_request_duration_seconds", 0.5, labels={"method": "GET", "endpoint": "/health"})

    def test_timer_context(self, metrics_collector):
        """验证计时器上下文"""
        with metrics_collector.timer("test_operation"):
            metrics_collector.increment_counter("instances_total")
        metrics_text = metrics_collector.get_metrics_text()
        assert "nova_task_execution_seconds" in metrics_text

    def test_timer_records_duration(self, metrics_collector):
        """验证计时器记录持续时间"""
        import time
        with metrics_collector.timer("slow_operation") as timer:
            time.sleep(0.01)
        duration = timer.get_duration()
        assert duration is not None
        assert duration >= 0.01

    def test_unknown_counter_warning(self, metrics_collector, caplog):
        """验证未知计数器会记录警告"""
        metrics_collector.increment_counter("unknown_counter")
        assert "未知计数器指标" in caplog.text

    def test_unknown_gauge_warning(self, metrics_collector, caplog):
        """验证未知 Gauge 会记录警告"""
        metrics_collector.set_gauge("unknown_gauge", 10)
        assert "未知 Gauge 指标" in caplog.text

    def test_unknown_histogram_warning(self, metrics_collector, caplog):
        """验证未知 Histogram 会记录警告"""
        metrics_collector.observe_histogram("unknown_histogram", 100)
        assert "未知 Histogram 指标" in caplog.text


class TestTimer:
    """计时器测试"""

    def test_timer_initialization(self, metrics_collector):
        """验证计时器初始化"""
        timer = metrics_collector.timer("test_timer")
        assert timer.name == "test_timer"
        assert timer.collector is metrics_collector
        assert timer.start_time is None

    def test_timer_with_labels(self, metrics_collector):
        """验证带标签的计时器"""
        timer = metrics_collector.timer("test_timer", {"method": "GET"})
        assert timer.labels == {"method": "GET"}

    def test_timer_get_duration_before_start(self, metrics_collector):
        """验证计时器未启动时返回 0"""
        timer = metrics_collector.timer("test_timer")
        duration = timer.get_duration()
        assert duration == 0.0

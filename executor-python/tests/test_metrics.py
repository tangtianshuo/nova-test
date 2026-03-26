"""
指标收集测试
============

验证指标收集和导出
"""

import pytest
from unittest.mock import MagicMock, patch
from nova_executor.metrics.collector import MetricsCollector


class TestMetricsCollector:
    """指标收集器测试"""

    def test_create_collector(self):
        """验证创建收集器"""
        collector = MetricsCollector()
        assert collector is not None
    def test_increment_counter(self):
        """验证增加计数器"""
        collector = MetricsCollector()
        collector.increment_counter("tasks_started")
        assert collector.get_counter("tasks_started") == 1
        collector.increment_counter("tasks_started", 5)
        assert collector.get_counter("tasks_started") == 6
    def test_set_gauge(self):
        """验证设置计量器"""
        collector = MetricsCollector()
        collector.set_gauge("active_instances", 10)
        assert collector.get_gauge("active_instances") == 10
        collector.set_gauge("active_instances", 5)
        assert collector.get_gauge("active_instances") == 5
    def test_observe_histogram(self):
        """验证观察直方图"""
        collector = MetricsCollector()
        collector.observe_histogram("execution_time", 100)
        collector.observe_histogram("execution_time", 200)
        collector.observe_histogram("execution_time", 150)
        assert len(collector.get_histogram("execution_time")) == 3
    def test_get_metrics(self):
        """验证获取指标"""
        collector = MetricsCollector()
        collector.increment_counter("test_counter")
        collector.set_gauge("test_gauge", 42)
        collector.observe_histogram("test_histogram", 100)
        metrics = collector.get_metrics()
        assert "test_counter" in metrics
        assert metrics["test_counter"] == 1
        assert metrics["test_gauge"] == 42
    def test_timer_context(self):
        """验证计时器上下文"""
        collector = MetricsCollector()
        with collector.timer("operation"):
            collector.increment_counter("operations")
        assert collector.get_counter("operations") == 1
    def test_timer_records_duration(self):
        """验证计时器记录持续时间"""
        collector = MetricsCollector()
        import time
        with collector.timer("slow_operation"):
            time.sleep(0.01)
        duration = collector.get_timer_duration("slow_operation")
        assert duration is not None
        assert duration > 0

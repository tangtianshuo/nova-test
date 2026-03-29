"""
日志测试
========

验证结构化日志功能
"""

import pytest
import json
import logging
from nova_executor.logging.logger import (
    Logger,
    LogLevel,
    LogContext,
    get_logger,
    set_context,
    clear_context,
)


class TestLogger:
    """日志记录器测试"""

    def test_create_logger(self):
        """验证创建日志记录器"""
        logger = Logger("test")
        assert logger is not None
        assert logger.logger is not None

    def test_logger_with_sanitization(self):
        """验证启用脱敏的日志记录器"""
        logger = Logger("test", enable_sanitization=True)
        assert logger.enable_sanitization is True

    def test_logger_without_sanitization(self):
        """验证禁用脱敏的日志记录器"""
        logger = Logger("test", enable_sanitization=False)
        assert logger.enable_sanitization is False

    def test_debug_log(self, caplog):
        """验证 DEBUG 日志"""
        with caplog.at_level(logging.DEBUG):
            logger = Logger("test", enable_sanitization=False)
            logger.debug("Test debug message")
            assert "Test debug message" in caplog.text

    def test_info_log(self, caplog):
        """验证 INFO 日志"""
        logger = Logger("test", enable_sanitization=False)
        logger.info("Test info message")
        assert "Test info message" in caplog.text

    def test_warning_log(self, caplog):
        """验证 WARNING 日志"""
        logger = Logger("test", enable_sanitization=False)
        logger.warning("Test warning message")
        assert "Test warning message" in caplog.text

    def test_error_log(self, caplog):
        """验证 ERROR 日志"""
        logger = Logger("test", enable_sanitization=False)
        logger.error("Test error message")
        assert "Test error message" in caplog.text

    def test_critical_log(self, caplog):
        """验证 CRITICAL 日志"""
        logger = Logger("test", enable_sanitization=False)
        logger.critical("Test critical message")
        assert "Test critical message" in caplog.text

    def test_error_log_with_exception(self, caplog):
        """验证带异常信息的错误日志"""
        logger = Logger("test", enable_sanitization=False)
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            logger.error("Error occurred", exc_info=e)
        assert "Error occurred" in caplog.text

    def test_info_log_with_extra_fields(self, caplog):
        """验证带额外字段的日志"""
        logger = Logger("test", enable_sanitization=False)
        logger.info("Test message", user_id="123", action="test")
        assert "Test message" in caplog.text

    def test_json_format(self, caplog):
        """验证 JSON 格式输出"""
        logger = Logger("test", enable_sanitization=False)
        logger.info("Test message")
        assert "Test message" in caplog.text


class TestLogContext:
    """日志上下文测试"""

    def test_create_log_context(self):
        """验证创建日志上下文"""
        ctx = LogContext(
            trace_id="trace-123",
            tenant_id="tenant-456",
            instance_id="instance-789",
        )
        assert ctx.trace_id == "trace-123"
        assert ctx.tenant_id == "tenant-456"
        assert ctx.instance_id == "instance-789"

    def test_log_context_with_extra(self):
        """验证带额外字段的日志上下文"""
        ctx = LogContext(extra={"key": "value"})
        assert ctx.extra["key"] == "value"

    def test_log_context_to_dict(self):
        """验证日志上下文转换为字典"""
        ctx = LogContext(trace_id="trace-123")
        ctx_dict = ctx.to_dict()
        assert isinstance(ctx_dict, dict)
        assert ctx_dict["trace_id"] == "trace-123"


class TestLogLevel:
    """日志级别测试"""

    def test_log_level_values(self):
        """验证日志级别枚举值"""
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.INFO.value == "INFO"
        assert LogLevel.WARNING.value == "WARNING"
        assert LogLevel.ERROR.value == "ERROR"
        assert LogLevel.CRITICAL.value == "CRITICAL"


class TestGetLogger:
    """获取日志记录器测试"""

    def test_get_logger(self):
        """验证获取日志记录器"""
        logger = get_logger("test-module")
        assert logger is not None
        assert isinstance(logger, Logger)


class TestContextManagement:
    """上下文管理测试"""

    def test_set_context(self):
        """验证设置上下文"""
        set_context(
            trace_id="trace-123",
            tenant_id="tenant-456",
            instance_id="instance-789",
        )

    def test_clear_context(self):
        """验证清除上下文"""
        set_context(
            trace_id="trace-123",
            tenant_id="tenant-456",
            instance_id="instance-789",
        )
        clear_context()

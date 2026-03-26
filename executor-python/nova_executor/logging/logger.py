"""
结构化日志记录器
================

提供统一格式的日志接口，支持上下文追踪

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求
"""

import logging
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from contextvars import ContextVar
from dataclasses import dataclass, field
from enum import Enum

# 上下文变量
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
tenant_id_var: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)
instance_id_var: ContextVar[Optional[str]] = ContextVar("instance_id", default=None)


class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogContext:
    """
    日志上下文

    用于在日志中添加额外上下文信息
    """
    trace_id: Optional[str] = None
    tenant_id: Optional[str] = None
    instance_id: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            k: v
            for k, v in {
                "trace_id": self.trace_id or trace_id_var.get(),
                "tenant_id": self.tenant_id or tenant_id_var.get(),
                "instance_id": self.instance_id or instance_id_var.get(),
                **self.extra,
            }.items()
            if v is not None
        }


class JSONFormatter(logging.Formatter):
    """
    JSON 格式化器

    输出结构化 JSON 格式日志
    """

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加上下文
        context = {
            "trace_id": trace_id_var.get(),
            "tenant_id": tenant_id_var.get(),
            "instance_id": instance_id_var.get(),
        }
        log_data["context"] = {k: v for k, v in context.items() if v}

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加额外字段
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data, ensure_ascii=False)


class Logger:
    """
    结构化日志记录器

    支持：
    1. JSON 格式输出
    2. 上下文追踪 (trace_id, tenant_id, instance_id)
    3. 多级别日志
    """

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # 添加 JSON 格式化处理器
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(JSONFormatter())
            self.logger.addHandler(handler)

    def _log(
        self,
        level: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None,
    ):
        """内部日志方法"""
        extra_fields = {"extra_fields": extra} if extra else {}
        self.logger.log(
            getattr(logging, level.upper()),
            message,
            extra=extra_fields,
            exc_info=exc_info,
        )

    def debug(self, message: str, **kwargs):
        """DEBUG 级别日志"""
        self._log("DEBUG", message, kwargs)

    def info(self, message: str, **kwargs):
        """INFO 级别日志"""
        self._log("INFO", message, kwargs)

    def warning(self, message: str, **kwargs):
        """WARNING 级别日志"""
        self._log("WARNING", message, kwargs)

    def error(self, message: str, exc_info: Optional[Exception] = None, **kwargs):
        """ERROR 级别日志"""
        self._log("ERROR", message, kwargs, exc_info=exc_info)

    def critical(self, message: str, exc_info: Optional[Exception] = None, **kwargs):
        """CRITICAL 级别日志"""
        self._log("CRITICAL", message, kwargs, exc_info=exc_info)


# 全局获取日志记录器的工厂函数
def get_logger(name: str) -> Logger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        Logger 实例
    """
    return Logger(name)


# 设置全局上下文
def set_context(
    trace_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    instance_id: Optional[str] = None,
):
    """
    设置全局日志上下文

    Args:
        trace_id: 链路追踪 ID
        tenant_id: 租户 ID
        instance_id: 实例 ID
    """
    if trace_id:
        trace_id_var.set(trace_id)
    if tenant_id:
        tenant_id_var.set(tenant_id)
    if instance_id:
        instance_id_var.set(instance_id)


def clear_context():
    """清除全局上下文"""
    trace_id_var.set(None)
    tenant_id_var.set(None)
    instance_id_var.set(None)

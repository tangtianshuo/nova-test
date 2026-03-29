"""
审计日志记录器
==============

实现安全合规所需的审计日志功能

严格遵循：
1. 审计字段规范 - 用户操作、时间戳、资源、操作类型等
2. 结构化输出 - JSON 格式便于日志收集和分析
3. 上下文追踪 - 支持 trace_id、tenant_id 等
4. 持久化支持 - 可选文件/数据库存储
"""

import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from pathlib import Path
import threading
from contextvars import ContextVar

from nova_executor.audit.audit_event_types import (
    AuditEventType,
    AuditSeverity,
    AuditCategory,
    AuditOutcome,
    AUDIT_FIELD_SPECIFICATION,
)

audit_trace_id_var: ContextVar[Optional[str]] = ContextVar("audit_trace_id", default=None)
audit_tenant_id_var: ContextVar[Optional[str]] = ContextVar("audit_tenant_id", default=None)
audit_user_id_var: ContextVar[Optional[str]] = ContextVar("audit_user_id", default=None)


@dataclass
class AuditContext:
    """
    审计上下文

    用于在审计日志中添加额外上下文信息
    """
    trace_id: Optional[str] = None
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    instance_id: Optional[str] = None
    task_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            k: v
            for k, v in {
                "trace_id": self.trace_id or audit_trace_id_var.get(),
                "tenant_id": self.tenant_id or audit_tenant_id_var.get(),
                "user_id": self.user_id or audit_user_id_var.get(),
                "instance_id": self.instance_id,
                "task_id": self.task_id,
                "ip_address": self.ip_address,
                "user_agent": self.user_agent,
                **self.extra,
            }.items()
            if v is not None
        }


@dataclass
class AuditEvent:
    """
    审计事件

    记录单个审计事件的所有信息
    """
    event_id: str
    timestamp: str
    event_type: str
    category: str
    severity: str
    outcome: str
    description: str
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    instance_id: Optional[str] = None
    task_id: Optional[str] = None
    action_type: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    trace_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            k: v
            for k, v in asdict(self).items()
            if v is not None
        }

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class AuditLogger:
    """
    审计日志记录器

    特性：
    1. 结构化 JSON 输出
    2. 审计字段规范完整
    3. 上下文追踪支持
    4. 多级别严重性
    5. 可选文件持久化
    """

    def __init__(
        self,
        name: str = "audit",
        log_file: Optional[str] = None,
        enable_console: bool = True,
    ):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        if enable_console and not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(handler)

        self._file_handler: Optional[logging.FileHandler] = None
        if log_file:
            self._setup_file_handler(log_file)

        self._lock = threading.Lock()

    def _setup_file_handler(self, log_file: str):
        """设置文件处理器"""
        try:
            path = Path(log_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            self._file_handler = logging.FileHandler(log_file, encoding="utf-8")
            self._file_handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(self._file_handler)
        except Exception as e:
            self.logger.warning(f"无法创建审计日志文件: {e}")

    def _create_event(
        self,
        event_type: AuditEventType,
        outcome: AuditOutcome = AuditOutcome.SUCCESS,
        description: Optional[str] = None,
        severity: Optional[AuditSeverity] = None,
        context: Optional[AuditContext] = None,
        action_type: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> AuditEvent:
        """创建审计事件"""
        if context is None:
            context = AuditContext()

        ctx_data = context.to_dict()

        return AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type.value,
            category=event_type.category.value,
            severity=(severity or event_type.default_severity).value,
            outcome=outcome.value,
            description=description or event_type.description,
            tenant_id=ctx_data.get("tenant_id"),
            user_id=ctx_data.get("user_id"),
            instance_id=ctx_data.get("instance_id"),
            task_id=ctx_data.get("task_id"),
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            trace_id=ctx_data.get("trace_id"),
            ip_address=ctx_data.get("ip_address"),
            user_agent=ctx_data.get("user_agent"),
            error_message=error_message,
            metadata=metadata or kwargs,
        )

    def _log_event(self, event: AuditEvent):
        """记录审计事件"""
        with self._lock:
            self.logger.info(event.to_json())

    def log(
        self,
        event_type: AuditEventType,
        outcome: AuditOutcome = AuditOutcome.SUCCESS,
        description: Optional[str] = None,
        severity: Optional[AuditSeverity] = None,
        context: Optional[AuditContext] = None,
        action_type: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """
        记录审计事件

        Args:
            event_type: 事件类型
            outcome: 操作结果
            description: 事件描述
            severity: 严重级别
            context: 审计上下文
            action_type: 动作类型
            resource_type: 资源类型
            resource_id: 资源标识符
            error_message: 错误信息
            metadata: 额外元数据
        """
        event = self._create_event(
            event_type=event_type,
            outcome=outcome,
            description=description,
            severity=severity,
            context=context,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            error_message=error_message,
            metadata=metadata,
            **kwargs,
        )
        self._log_event(event)
        return event

    def log_task_event(
        self,
        event_type: AuditEventType,
        instance_id: str,
        task_id: str,
        tenant_id: str,
        outcome: AuditOutcome = AuditOutcome.SUCCESS,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """记录任务相关事件"""
        context = AuditContext(
            instance_id=instance_id,
            task_id=task_id,
            tenant_id=tenant_id,
        )
        return self.log(
            event_type=event_type,
            outcome=outcome,
            context=context,
            resource_type="TASK",
            resource_id=instance_id,
            error_message=error_message,
            metadata=metadata,
        )

    def log_hil_event(
        self,
        event_type: AuditEventType,
        ticket_id: str,
        instance_id: str,
        user_id: str,
        tenant_id: str,
        decision: Optional[str] = None,
        outcome: AuditOutcome = AuditOutcome.SUCCESS,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """记录 HIL 决策事件"""
        context = AuditContext(
            instance_id=instance_id,
            user_id=user_id,
            tenant_id=tenant_id,
        )
        return self.log(
            event_type=event_type,
            outcome=outcome,
            context=context,
            resource_type="HIL_TICKET",
            resource_id=ticket_id,
            error_message=error_message,
            metadata={**(metadata or {}), "decision": decision},
        )

    def log_action_event(
        self,
        action_type: str,
        instance_id: str,
        tenant_id: str,
        success: bool,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """记录动作执行事件"""
        event_type = AuditEventType.ACTION_EXECUTED if success else AuditEventType.ACTION_FAILED
        context = AuditContext(
            instance_id=instance_id,
            tenant_id=tenant_id,
        )
        return self.log(
            event_type=event_type,
            outcome=AuditOutcome.SUCCESS if success else AuditOutcome.FAILURE,
            context=context,
            action_type=action_type,
            resource_type="ACTION",
            error_message=error_message,
            metadata=metadata,
        )

    def log_api_event(
        self,
        endpoint: str,
        method: str,
        user_id: Optional[str],
        tenant_id: str,
        status_code: int,
        duration_ms: Optional[float] = None,
        error_message: Optional[str] = None,
    ):
        """记录 API 调用事件"""
        outcome = AuditOutcome.SUCCESS if status_code < 400 else AuditOutcome.FAILURE
        event_type = AuditEventType.API_CALLED
        if status_code == 401 or status_code == 403:
            event_type = AuditEventType.API_AUTH_FAILED
            outcome = AuditOutcome.FAILURE

        context = AuditContext(
            user_id=user_id,
            tenant_id=tenant_id,
        )
        return self.log(
            event_type=event_type,
            outcome=outcome,
            context=context,
            error_message=error_message,
            metadata={
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "duration_ms": duration_ms,
            },
        )

    def log_security_event(
        self,
        event_type: AuditEventType,
        description: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.HIGH,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """记录安全相关事件"""
        context = AuditContext(
            user_id=user_id,
            tenant_id=tenant_id,
            ip_address=ip_address,
        )
        return self.log(
            event_type=event_type,
            outcome=AuditOutcome.FAILURE,
            description=description,
            severity=severity,
            context=context,
            metadata=metadata,
        )

    def close(self):
        """关闭日志记录器"""
        if self._file_handler:
            self._file_handler.close()
            self.logger.removeHandler(self._file_handler)


_audit_logger: Optional[AuditLogger] = None
_audit_logger_lock = threading.Lock()


def get_audit_logger(
    name: str = "audit",
    log_file: Optional[str] = None,
    enable_console: bool = True,
) -> AuditLogger:
    """
    获取全局审计日志记录器单例

    Args:
        name: 日志记录器名称
        log_file: 审计日志文件路径
        enable_console: 是否输出到控制台

    Returns:
        AuditLogger 实例
    """
    global _audit_logger

    if _audit_logger is None:
        with _audit_logger_lock:
            if _audit_logger is None:
                _audit_logger = AuditLogger(
                    name=name,
                    log_file=log_file,
                    enable_console=enable_console,
                )

    return _audit_logger


def set_audit_context(
    trace_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
):
    """
    设置全局审计上下文

    Args:
        trace_id: 链路追踪 ID
        tenant_id: 租户 ID
        user_id: 用户 ID
    """
    if trace_id:
        audit_trace_id_var.set(trace_id)
    if tenant_id:
        audit_tenant_id_var.set(tenant_id)
    if user_id:
        audit_user_id_var.set(user_id)


def clear_audit_context():
    """清除全局审计上下文"""
    audit_trace_id_var.set(None)
    audit_tenant_id_var.set(None)
    audit_user_id_var.set(None)

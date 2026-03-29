"""
审计日志测试
============

测试审计日志功能：
1. 审计事件类型定义
2. 审计日志记录器
3. 上下文追踪
4. 事件记录功能
"""

import json
import pytest
import logging
from datetime import datetime
from io import StringIO
from unittest.mock import patch, MagicMock

from nova_executor.audit.audit_event_types import (
    AuditEventType,
    AuditSeverity,
    AuditCategory,
    AuditOutcome,
    AuditEventSchema,
    AUDIT_FIELD_SPECIFICATION,
)

from nova_executor.audit.audit_logger import (
    AuditLogger,
    AuditContext,
    AuditEvent,
    get_audit_logger,
    set_audit_context,
    clear_audit_context,
)


class TestAuditEventTypes:
    """测试审计事件类型"""

    def test_event_type_values(self):
        """测试事件类型枚举值"""
        assert AuditEventType.TASK_CREATED.value == "TASK_CREATED"
        assert AuditEventType.TASK_STARTED.value == "TASK_STARTED"
        assert AuditEventType.TASK_COMPLETED.value == "TASK_COMPLETED"
        assert AuditEventType.TASK_FAILED.value == "TASK_FAILED"
        assert AuditEventType.HIL_TICKET_APPROVED.value == "HIL_TICKET_APPROVED"
        assert AuditEventType.HIL_TICKET_REJECTED.value == "HIL_TICKET_REJECTED"
        assert AuditEventType.HIL_TICKET_MODIFIED.value == "HIL_TICKET_MODIFIED"

    def test_audit_category_values(self):
        """测试审计分类枚举值"""
        assert AuditCategory.TASK_MANAGEMENT.value == "TASK_MANAGEMENT"
        assert AuditCategory.HIL_DECISION.value == "HIL_DECISION"
        assert AuditCategory.AUTHENTICATION.value == "AUTHENTICATION"
        assert AuditCategory.EXECUTION.value == "EXECUTION"

    def test_audit_severity_values(self):
        """测试审计严重级别枚举值"""
        assert AuditSeverity.LOW.value == "LOW"
        assert AuditSeverity.MEDIUM.value == "MEDIUM"
        assert AuditSeverity.HIGH.value == "HIGH"
        assert AuditSeverity.CRITICAL.value == "CRITICAL"

    def test_audit_outcome_values(self):
        """测试审计结果枚举值"""
        assert AuditOutcome.SUCCESS.value == "SUCCESS"
        assert AuditOutcome.FAILURE.value == "FAILURE"
        assert AuditOutcome.PARTIAL.value == "PARTIAL"
        assert AuditOutcome.PENDING.value == "PENDING"

    def test_event_category_mapping(self):
        """测试事件类型到分类的映射"""
        assert AuditEventType.TASK_CREATED.category == AuditCategory.TASK_MANAGEMENT
        assert AuditEventType.HIL_TICKET_APPROVED.category == AuditCategory.HIL_DECISION
        assert AuditEventType.USER_LOGIN.category == AuditCategory.AUTHENTICATION

    def test_event_default_severity(self):
        """测试事件默认严重级别"""
        assert AuditEventType.TASK_CREATED.default_severity == AuditSeverity.LOW
        assert AuditEventType.TASK_FAILED.default_severity == AuditSeverity.MEDIUM
        assert AuditEventType.SECURITY_VIOLATION.default_severity == AuditSeverity.CRITICAL

    def test_event_requires_user_context(self):
        """测试需要用户上下文的事件"""
        assert AuditEventType.USER_LOGIN.requires_user_context is True
        assert AuditEventType.HIL_TICKET_APPROVED.requires_user_context is True
        assert AuditEventType.TASK_CREATED.requires_user_context is False

    def test_event_descriptions(self):
        """测试事件描述"""
        assert len(AuditEventType.TASK_CREATED.description) > 0
        assert len(AuditEventType.HIL_TICKET_APPROVED.description) > 0
        assert AuditEventType.TASK_CREATED.description == "任务被创建"

    def test_audit_field_specification(self):
        """测试审计字段规范"""
        assert "event_id" in AUDIT_FIELD_SPECIFICATION
        assert "timestamp" in AUDIT_FIELD_SPECIFICATION
        assert "event_type" in AUDIT_FIELD_SPECIFICATION
        assert "tenant_id" in AUDIT_FIELD_SPECIFICATION
        assert "outcome" in AUDIT_FIELD_SPECIFICATION


class TestAuditEvent:
    """测试审计事件数据类"""

    def test_audit_event_creation(self):
        """测试审计事件创建"""
        event = AuditEvent(
            event_id="test-event-001",
            timestamp="2024-01-01T10:00:00Z",
            event_type="TASK_CREATED",
            category="TASK_MANAGEMENT",
            severity="LOW",
            outcome="SUCCESS",
            description="任务被创建",
            tenant_id="tenant-001",
        )

        assert event.event_id == "test-event-001"
        assert event.event_type == "TASK_CREATED"
        assert event.tenant_id == "tenant-001"

    def test_audit_event_to_dict(self):
        """测试审计事件转换为字典"""
        event = AuditEvent(
            event_id="test-event-001",
            timestamp="2024-01-01T10:00:00Z",
            event_type="TASK_CREATED",
            category="TASK_MANAGEMENT",
            severity="LOW",
            outcome="SUCCESS",
            description="任务被创建",
            tenant_id="tenant-001",
            user_id="user-001",
        )

        data = event.to_dict()

        assert "event_id" in data
        assert "timestamp" in data
        assert "event_type" in data
        assert data["tenant_id"] == "tenant-001"
        assert data["user_id"] == "user-001"

    def test_audit_event_to_json(self):
        """测试审计事件转换为 JSON"""
        event = AuditEvent(
            event_id="test-event-001",
            timestamp="2024-01-01T10:00:00Z",
            event_type="TASK_CREATED",
            category="TASK_MANAGEMENT",
            severity="LOW",
            outcome="SUCCESS",
            description="任务被创建",
        )

        json_str = event.to_json()
        data = json.loads(json_str)

        assert data["event_id"] == "test-event-001"
        assert data["event_type"] == "TASK_CREATED"

    def test_audit_event_optional_fields_omitted(self):
        """测试可选字段不输出到字典"""
        event = AuditEvent(
            event_id="test-event-001",
            timestamp="2024-01-01T10:00:00Z",
            event_type="TASK_CREATED",
            category="TASK_MANAGEMENT",
            severity="LOW",
            outcome="SUCCESS",
            description="任务被创建",
        )

        data = event.to_dict()

        assert "user_id" not in data
        assert "instance_id" not in data
        assert "error_message" not in data


class TestAuditContext:
    """测试审计上下文"""

    def test_audit_context_creation(self):
        """测试审计上下文创建"""
        context = AuditContext(
            trace_id="trace-001",
            tenant_id="tenant-001",
            user_id="user-001",
            instance_id="instance-001",
        )

        assert context.trace_id == "trace-001"
        assert context.tenant_id == "tenant-001"
        assert context.user_id == "user-001"
        assert context.instance_id == "instance-001"

    def test_audit_context_to_dict(self):
        """测试审计上下文转换为字典"""
        context = AuditContext(
            trace_id="trace-001",
            tenant_id="tenant-001",
            user_id="user-001",
        )

        data = context.to_dict()

        assert data["trace_id"] == "trace-001"
        assert data["tenant_id"] == "tenant-001"
        assert data["user_id"] == "user-001"

    def test_audit_context_extra_fields(self):
        """测试审计上下文额外字段"""
        context = AuditContext(
            tenant_id="tenant-001",
            extra={"custom_field": "custom_value"},
        )

        data = context.to_dict()

        assert data["custom_field"] == "custom_value"


class TestAuditLogger:
    """测试审计日志记录器"""

    def test_audit_logger_creation(self):
        """测试审计日志记录器创建"""
        logger = AuditLogger(name="test_audit", enable_console=True)

        assert logger.name == "test_audit"
        assert logger.logger is not None

    def test_audit_logger_log_basic_event(self):
        """测试记录基本审计事件"""
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(logging.Formatter("%(message)s"))

        test_logger = logging.getLogger("test_basic")
        test_logger.setLevel(logging.INFO)
        test_logger.addHandler(handler)

        logger = AuditLogger(name="test_basic", enable_console=False)
        logger.logger = test_logger

        event = logger.log(
            event_type=AuditEventType.TASK_CREATED,
            outcome=AuditOutcome.SUCCESS,
            context=AuditContext(tenant_id="tenant-001"),
        )

        assert event is not None
        assert event.event_type == "TASK_CREATED"
        assert event.outcome == "SUCCESS"

    def test_audit_logger_log_task_event(self):
        """测试记录任务事件"""
        logger = AuditLogger(name="test_task", enable_console=False)

        event = logger.log_task_event(
            event_type=AuditEventType.TASK_STARTED,
            instance_id="instance-001",
            task_id="task-001",
            tenant_id="tenant-001",
            outcome=AuditOutcome.SUCCESS,
        )

        assert event is not None
        assert event.resource_type == "TASK"
        assert event.resource_id == "instance-001"
        assert event.instance_id == "instance-001"
        assert event.task_id == "task-001"

    def test_audit_logger_log_hil_event(self):
        """测试记录 HIL 决策事件"""
        logger = AuditLogger(name="test_hil", enable_console=False)

        event = logger.log_hil_event(
            event_type=AuditEventType.HIL_TICKET_APPROVED,
            ticket_id="ticket-001",
            instance_id="instance-001",
            user_id="user-001",
            tenant_id="tenant-001",
            decision="APPROVED",
            outcome=AuditOutcome.SUCCESS,
        )

        assert event is not None
        assert event.resource_type == "HIL_TICKET"
        assert event.resource_id == "ticket-001"
        assert event.user_id == "user-001"
        assert event.instance_id == "instance-001"

    def test_audit_logger_log_action_event_success(self):
        """测试记录动作执行成功事件"""
        logger = AuditLogger(name="test_action", enable_console=False)

        event = logger.log_action_event(
            action_type="CLICK",
            instance_id="instance-001",
            tenant_id="tenant-001",
            success=True,
            metadata={"selector": "#btn"},
        )

        assert event is not None
        assert event.event_type == "ACTION_EXECUTED"
        assert event.outcome == "SUCCESS"
        assert event.action_type == "CLICK"

    def test_audit_logger_log_action_event_failure(self):
        """测试记录动作执行失败事件"""
        logger = AuditLogger(name="test_action_fail", enable_console=False)

        event = logger.log_action_event(
            action_type="CLICK",
            instance_id="instance-001",
            tenant_id="tenant-001",
            success=False,
            error_message="Element not found",
        )

        assert event is not None
        assert event.event_type == "ACTION_FAILED"
        assert event.outcome == "FAILURE"
        assert event.error_message == "Element not found"

    def test_audit_logger_log_api_event(self):
        """测试记录 API 调用事件"""
        logger = AuditLogger(name="test_api", enable_console=False)

        event = logger.log_api_event(
            endpoint="/api/v1/tasks/start",
            method="POST",
            user_id="user-001",
            tenant_id="tenant-001",
            status_code=200,
            duration_ms=150.5,
        )

        assert event is not None
        assert event.event_type == "API_CALLED"
        assert event.outcome == "SUCCESS"
        assert event.metadata["endpoint"] == "/api/v1/tasks/start"
        assert event.metadata["status_code"] == 200

    def test_audit_logger_log_api_event_auth_failure(self):
        """测试记录 API 认证失败事件"""
        logger = AuditLogger(name="test_api_auth", enable_console=False)

        event = logger.log_api_event(
            endpoint="/api/v1/tasks/start",
            method="POST",
            user_id="invalid-user",
            tenant_id="tenant-001",
            status_code=401,
        )

        assert event is not None
        assert event.event_type == "API_AUTH_FAILED"
        assert event.outcome == "FAILURE"

    def test_audit_logger_log_security_event(self):
        """测试记录安全事件"""
        logger = AuditLogger(name="test_security", enable_console=False)

        event = logger.log_security_event(
            event_type=AuditEventType.SECURITY_VIOLATION,
            description="可疑访问尝试",
            tenant_id="tenant-001",
            user_id="user-001",
            ip_address="192.168.1.100",
            severity=AuditSeverity.HIGH,
        )

        assert event is not None
        assert event.event_type == "SECURITY_VIOLATION"
        assert event.severity == "HIGH"
        assert event.outcome == "FAILURE"
        assert event.ip_address == "192.168.1.100"


class TestAuditContextVariables:
    """测试审计上下文变量"""

    def test_set_and_get_context(self):
        """测试设置和获取上下文"""
        set_audit_context(
            trace_id="trace-001",
            tenant_id="tenant-001",
            user_id="user-001",
        )

        from nova_executor.audit.audit_logger import (
            audit_trace_id_var,
            audit_tenant_id_var,
            audit_user_id_var,
        )

        assert audit_trace_id_var.get() == "trace-001"
        assert audit_tenant_id_var.get() == "tenant-001"
        assert audit_user_id_var.get() == "user-001"

        clear_audit_context()

        assert audit_trace_id_var.get() is None
        assert audit_tenant_id_var.get() is None
        assert audit_user_id_var.get() is None

    def test_context_in_event(self):
        """测试上下文在事件中生效"""
        set_audit_context(
            trace_id="trace-002",
            tenant_id="tenant-002",
        )

        logger = AuditLogger(name="test_context_event", enable_console=False)

        context = AuditContext()
        event = logger.log(
            event_type=AuditEventType.TASK_CREATED,
            outcome=AuditOutcome.SUCCESS,
            context=context,
        )

        assert event.trace_id == "trace-002"
        assert event.tenant_id == "tenant-002"

        clear_audit_context()


class TestGetAuditLoggerSingleton:
    """测试审计日志记录器单例"""

    def test_get_audit_logger_singleton(self):
        """测试获取单例"""
        logger1 = get_audit_logger(name="singleton_test", enable_console=False)
        logger2 = get_audit_logger(name="singleton_test", enable_console=False)

        assert logger1 is logger2

    def test_get_audit_logger_different_names(self):
        """测试不同名称返回不同实例"""
        from nova_executor.audit import audit_logger as audit_module
        original_logger = audit_module._audit_logger

        audit_module._audit_logger = None

        logger1 = get_audit_logger(name="test1", enable_console=False)
        logger2 = get_audit_logger(name="test2", enable_console=False)

        assert logger1.name == "test1"
        assert logger2.name == "test1"
        assert logger1 is logger2

        audit_module._audit_logger = original_logger


class TestAuditEventSchema:
    """测试审计事件模式验证"""

    def test_audit_event_schema_validation(self):
        """测试审计事件模式验证"""
        schema = AuditEventSchema(
            event_type=AuditEventType.TASK_CREATED,
            required_fields=["event_id", "timestamp", "event_type"],
            optional_fields=["tenant_id", "user_id"],
            description="任务被创建",
            category=AuditCategory.TASK_MANAGEMENT,
            severity=AuditSeverity.LOW,
        )

        valid_data = {
            "event_id": "test-001",
            "timestamp": "2024-01-01T10:00:00Z",
            "event_type": "TASK_CREATED",
        }
        assert schema.validate(valid_data) is True

        invalid_data = {
            "event_id": "test-001",
        }
        assert schema.validate(invalid_data) is False


class TestAuditIntegration:
    """审计日志集成测试"""

    def test_complete_audit_workflow(self):
        """测试完整审计工作流"""
        logger = AuditLogger(name="test_workflow", enable_console=False)

        task_started = logger.log_task_event(
            event_type=AuditEventType.TASK_STARTED,
            instance_id="instance-001",
            task_id="task-001",
            tenant_id="tenant-001",
            outcome=AuditOutcome.SUCCESS,
        )

        action_executed = logger.log_action_event(
            action_type="CLICK",
            instance_id="instance-001",
            tenant_id="tenant-001",
            success=True,
        )

        hil_approved = logger.log_hil_event(
            event_type=AuditEventType.HIL_TICKET_APPROVED,
            ticket_id="ticket-001",
            instance_id="instance-001",
            user_id="user-001",
            tenant_id="tenant-001",
            decision="APPROVED",
            outcome=AuditOutcome.SUCCESS,
        )

        task_completed = logger.log_task_event(
            event_type=AuditEventType.TASK_COMPLETED,
            instance_id="instance-001",
            task_id="task-001",
            tenant_id="tenant-001",
            outcome=AuditOutcome.SUCCESS,
        )

        assert task_started.event_type == "TASK_STARTED"
        assert action_executed.event_type == "ACTION_EXECUTED"
        assert hil_approved.event_type == "HIL_TICKET_APPROVED"
        assert task_completed.event_type == "TASK_COMPLETED"

        all_events = [task_started, action_executed, hil_approved, task_completed]
        assert all(e.outcome == "SUCCESS" for e in all_events)

    def test_audit_event_json_parsing(self):
        """测试审计事件 JSON 解析"""
        logger = AuditLogger(name="test_json_parse", enable_console=False)

        event = logger.log_task_event(
            event_type=AuditEventType.TASK_FAILED,
            instance_id="instance-001",
            task_id="task-001",
            tenant_id="tenant-001",
            outcome=AuditOutcome.FAILURE,
            error_message="执行超时",
        )

        json_str = event.to_json()
        parsed = json.loads(json_str)

        assert parsed["event_type"] == "TASK_FAILED"
        assert parsed["outcome"] == "FAILURE"
        assert parsed["error_message"] == "执行超时"
        assert "event_id" in parsed
        assert "timestamp" in parsed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

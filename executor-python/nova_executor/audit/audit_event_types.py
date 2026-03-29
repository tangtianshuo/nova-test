"""
审计事件类型定义
================

定义所有可审计的事件类型及其元数据

严格遵循安全合规要求，记录关键操作
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass


class AuditCategory(str, Enum):
    """审计事件分类"""
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    TASK_MANAGEMENT = "TASK_MANAGEMENT"
    HIL_DECISION = "HIL_DECISION"
    RESOURCE_ACCESS = "RESOURCE_ACCESS"
    CONFIGURATION = "CONFIGURATION"
    SECURITY = "SECURITY"
    EXECUTION = "EXECUTION"


class AuditSeverity(str, Enum):
    """审计事件严重级别"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AuditOutcome(str, Enum):
    """审计结果"""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PARTIAL = "PARTIAL"
    PENDING = "PENDING"


class AuditEventType(str, Enum):
    """审计事件类型枚举"""

    TASK_CREATED = "TASK_CREATED"
    TASK_STARTED = "TASK_STARTED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"
    TASK_TERMINATED = "TASK_TERMINATED"
    TASK_RESUMED = "TASK_RESUMED"

    HIL_TICKET_CREATED = "HIL_TICKET_CREATED"
    HIL_TICKET_APPROVED = "HIL_TICKET_APPROVED"
    HIL_TICKET_REJECTED = "HIL_TICKET_REJECTED"
    HIL_TICKET_MODIFIED = "HIL_TICKET_MODIFIED"
    HIL_TICKET_EXPIRED = "HIL_TICKET_EXPIRED"

    ACTION_EXECUTED = "ACTION_EXECUTED"
    ACTION_FAILED = "ACTION_FAILED"

    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    USER_ACCESS_DENIED = "USER_ACCESS_DENIED"

    API_CALLED = "API_CALLED"
    API_AUTH_FAILED = "API_AUTH_FAILED"

    CONFIG_CHANGED = "CONFIG_CHANGED"
    SECRET_ACCESSED = "SECRET_ACCESSED"

    RESOURCE_CREATED = "RESOURCE_CREATED"
    RESOURCE_DELETED = "RESOURCE_DELETED"
    RESOURCE_MODIFIED = "RESOURCE_MODIFIED"

    SANDBOX_CREATED = "SANDBOX_CREATED"
    SANDBOX_DESTROYED = "SANDBOX_DESTROYED"

    ERROR_OCCURRED = "ERROR_OCCURRED"
    SECURITY_VIOLATION = "SECURITY_VIOLATION"

    @property
    def category(self) -> AuditCategory:
        """获取事件所属类别"""
        category_map: Dict[AuditEventType, AuditCategory] = {
            AuditEventType.TASK_CREATED: AuditCategory.TASK_MANAGEMENT,
            AuditEventType.TASK_STARTED: AuditCategory.TASK_MANAGEMENT,
            AuditEventType.TASK_COMPLETED: AuditCategory.TASK_MANAGEMENT,
            AuditEventType.TASK_FAILED: AuditCategory.TASK_MANAGEMENT,
            AuditEventType.TASK_TERMINATED: AuditCategory.TASK_MANAGEMENT,
            AuditEventType.TASK_RESUMED: AuditCategory.TASK_MANAGEMENT,
            AuditEventType.HIL_TICKET_CREATED: AuditCategory.HIL_DECISION,
            AuditEventType.HIL_TICKET_APPROVED: AuditCategory.HIL_DECISION,
            AuditEventType.HIL_TICKET_REJECTED: AuditCategory.HIL_DECISION,
            AuditEventType.HIL_TICKET_MODIFIED: AuditCategory.HIL_DECISION,
            AuditEventType.HIL_TICKET_EXPIRED: AuditCategory.HIL_DECISION,
            AuditEventType.ACTION_EXECUTED: AuditCategory.EXECUTION,
            AuditEventType.ACTION_FAILED: AuditCategory.EXECUTION,
            AuditEventType.USER_LOGIN: AuditCategory.AUTHENTICATION,
            AuditEventType.USER_LOGOUT: AuditCategory.AUTHENTICATION,
            AuditEventType.USER_ACCESS_DENIED: AuditCategory.AUTHORIZATION,
            AuditEventType.API_CALLED: AuditCategory.EXECUTION,
            AuditEventType.API_AUTH_FAILED: AuditCategory.AUTHENTICATION,
            AuditEventType.CONFIG_CHANGED: AuditCategory.CONFIGURATION,
            AuditEventType.SECRET_ACCESSED: AuditCategory.SECURITY,
            AuditEventType.RESOURCE_CREATED: AuditCategory.RESOURCE_ACCESS,
            AuditEventType.RESOURCE_DELETED: AuditCategory.RESOURCE_ACCESS,
            AuditEventType.RESOURCE_MODIFIED: AuditCategory.RESOURCE_ACCESS,
            AuditEventType.SANDBOX_CREATED: AuditCategory.RESOURCE_ACCESS,
            AuditEventType.SANDBOX_DESTROYED: AuditCategory.RESOURCE_ACCESS,
            AuditEventType.ERROR_OCCURRED: AuditCategory.SECURITY,
            AuditEventType.SECURITY_VIOLATION: AuditCategory.SECURITY,
        }
        return category_map.get(self, AuditCategory.EXECUTION)

    @property
    def default_severity(self) -> AuditSeverity:
        """获取默认严重级别"""
        severity_map: Dict[AuditEventType, AuditSeverity] = {
            AuditEventType.TASK_CREATED: AuditSeverity.LOW,
            AuditEventType.TASK_STARTED: AuditSeverity.LOW,
            AuditEventType.TASK_COMPLETED: AuditSeverity.LOW,
            AuditEventType.TASK_FAILED: AuditSeverity.MEDIUM,
            AuditEventType.TASK_TERMINATED: AuditSeverity.MEDIUM,
            AuditEventType.TASK_RESUMED: AuditSeverity.LOW,
            AuditEventType.HIL_TICKET_CREATED: AuditSeverity.MEDIUM,
            AuditEventType.HIL_TICKET_APPROVED: AuditSeverity.MEDIUM,
            AuditEventType.HIL_TICKET_REJECTED: AuditSeverity.MEDIUM,
            AuditEventType.HIL_TICKET_MODIFIED: AuditSeverity.MEDIUM,
            AuditEventType.HIL_TICKET_EXPIRED: AuditSeverity.LOW,
            AuditEventType.ACTION_EXECUTED: AuditSeverity.LOW,
            AuditEventType.ACTION_FAILED: AuditSeverity.MEDIUM,
            AuditEventType.USER_LOGIN: AuditSeverity.MEDIUM,
            AuditEventType.USER_LOGOUT: AuditSeverity.LOW,
            AuditEventType.USER_ACCESS_DENIED: AuditSeverity.HIGH,
            AuditEventType.API_CALLED: AuditSeverity.LOW,
            AuditEventType.API_AUTH_FAILED: AuditSeverity.HIGH,
            AuditEventType.CONFIG_CHANGED: AuditSeverity.HIGH,
            AuditEventType.SECRET_ACCESSED: AuditSeverity.CRITICAL,
            AuditEventType.RESOURCE_CREATED: AuditSeverity.LOW,
            AuditEventType.RESOURCE_DELETED: AuditSeverity.HIGH,
            AuditEventType.RESOURCE_MODIFIED: AuditSeverity.MEDIUM,
            AuditEventType.SANDBOX_CREATED: AuditSeverity.LOW,
            AuditEventType.SANDBOX_DESTROYED: AuditSeverity.LOW,
            AuditEventType.ERROR_OCCURRED: AuditSeverity.MEDIUM,
            AuditEventType.SECURITY_VIOLATION: AuditSeverity.CRITICAL,
        }
        return severity_map.get(self, AuditSeverity.MEDIUM)

    @property
    def requires_user_context(self) -> bool:
        """是否需要用户上下文"""
        return self in [
            AuditEventType.USER_LOGIN,
            AuditEventType.USER_LOGOUT,
            AuditEventType.USER_ACCESS_DENIED,
            AuditEventType.HIL_TICKET_APPROVED,
            AuditEventType.HIL_TICKET_REJECTED,
            AuditEventType.HIL_TICKET_MODIFIED,
            AuditEventType.CONFIG_CHANGED,
        ]

    @property
    def description(self) -> str:
        """获取事件描述"""
        descriptions: Dict[AuditEventType, str] = {
            AuditEventType.TASK_CREATED: "任务被创建",
            AuditEventType.TASK_STARTED: "任务开始执行",
            AuditEventType.TASK_COMPLETED: "任务成功完成",
            AuditEventType.TASK_FAILED: "任务执行失败",
            AuditEventType.TASK_TERMINATED: "任务被终止",
            AuditEventType.TASK_RESUMED: "任务恢复执行",
            AuditEventType.HIL_TICKET_CREATED: "HIL工单创建",
            AuditEventType.HIL_TICKET_APPROVED: "HIL工单被批准",
            AuditEventType.HIL_TICKET_REJECTED: "HIL工单被拒绝",
            AuditEventType.HIL_TICKET_MODIFIED: "HIL工单被修改",
            AuditEventType.HIL_TICKET_EXPIRED: "HIL工单已过期",
            AuditEventType.ACTION_EXECUTED: "动作被执行",
            AuditEventType.ACTION_FAILED: "动作执行失败",
            AuditEventType.USER_LOGIN: "用户登录",
            AuditEventType.USER_LOGOUT: "用户登出",
            AuditEventType.USER_ACCESS_DENIED: "用户访问被拒绝",
            AuditEventType.API_CALLED: "API被调用",
            AuditEventType.API_AUTH_FAILED: "API认证失败",
            AuditEventType.CONFIG_CHANGED: "配置被修改",
            AuditEventType.SECRET_ACCESSED: "密钥被访问",
            AuditEventType.RESOURCE_CREATED: "资源被创建",
            AuditEventType.RESOURCE_DELETED: "资源被删除",
            AuditEventType.RESOURCE_MODIFIED: "资源被修改",
            AuditEventType.SANDBOX_CREATED: "沙箱被创建",
            AuditEventType.SANDBOX_DESTROYED: "沙箱被销毁",
            AuditEventType.ERROR_OCCURRED: "错误发生",
            AuditEventType.SECURITY_VIOLATION: "安全违规",
        }
        return descriptions.get(self, self.value)


@dataclass
class AuditEventSchema:
    """审计事件结构定义"""
    event_type: AuditEventType
    required_fields: List[str]
    optional_fields: List[str]
    description: str
    category: AuditCategory
    severity: AuditSeverity

    def validate(self, data: Dict) -> bool:
        """验证审计事件数据"""
        return all(field in data for field in self.required_fields)


AUDIT_FIELD_SPECIFICATION: Dict[str, str] = {
    "event_id": "唯一事件标识符 (UUID)",
    "timestamp": "事件发生时间 (ISO 8601)",
    "event_type": "事件类型 (枚举值)",
    "tenant_id": "租户标识符",
    "user_id": "用户标识符 (可选)",
    "instance_id": "实例标识符 (可选)",
    "task_id": "任务标识符 (可选)",
    "action_type": "动作类型 (可选)",
    "resource_type": "资源类型 (可选)",
    "resource_id": "资源标识符 (可选)",
    "outcome": "操作结果 (SUCCESS/FAILURE)",
    "severity": "严重级别 (LOW/MEDIUM/HIGH/CRITICAL)",
    "category": "事件分类",
    "description": "事件描述",
    "ip_address": "IP地址 (可选)",
    "user_agent": "用户代理 (可选)",
    "metadata": "额外元数据 (可选)",
    "error_message": "错误信息 (可选)",
    "trace_id": "链路追踪ID (可选)",
}

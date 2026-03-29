"""
RBAC 权限矩阵验证模块
=====================

提供基于角色的访问控制 (Role-Based Access Control) 验证功能：
1. 定义权限矩阵规范
2. 实现权限边界测试
3. 添加越权操作拦截
4. 权限验证引擎
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Callable
from datetime import datetime


class Permission(str, Enum):
    """权限枚举"""
    # 任务权限
    TASK_CREATE = "task:create"
    TASK_READ = "task:read"
    TASK_UPDATE = "task:update"
    TASK_DELETE = "task:delete"
    TASK_LIST = "task:list"
    TASK_EXECUTE = "task:execute"

    # 实例权限
    INSTANCE_CREATE = "instance:create"
    INSTANCE_READ = "instance:read"
    INSTANCE_UPDATE = "instance:update"
    INSTANCE_DELETE = "instance:delete"
    INSTANCE_LIST = "instance:list"
    INSTANCE_TERMINATE = "instance:terminate"

    # HIL 工单权限
    HIL_CREATE = "hil:create"
    HIL_READ = "hil:read"
    HIL_APPROVE = "hil:approve"
    HIL_REJECT = "hil:reject"
    HIL_MODIFY = "hil:modify"

    # 报告权限
    REPORT_READ = "report:read"
    REPORT_EXPORT = "report:export"
    REPORT_DELETE = "report:delete"

    # 存储权限
    STORAGE_READ = "storage:read"
    STORAGE_WRITE = "storage:write"
    STORAGE_DELETE = "storage:delete"

    # 管理员权限
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
    ADMIN_USERS = "admin:users"
    ADMIN_TENANT = "admin:tenant"
    ADMIN_AUDIT = "admin:audit"

    # 安全权限
    SECURITY_VIEW = "security:view"
    SECURITY_SCAN = "security:scan"
    SECURITY_CONFIG = "security:config"


class Role(str, Enum):
    """角色枚举"""
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
    AUDITOR = "auditor"
    SERVICE = "service"


@dataclass
class RolePermission:
    """角色权限定义"""
    role: Role
    permissions: Set[Permission]
    description: str
    inherit_from: Optional[Role] = None


@dataclass
class PermissionContext:
    """权限上下文"""
    user_id: str
    tenant_id: str
    role: Role
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AccessRequest:
    """访问请求"""
    permission: Permission
    resource_type: str
    resource_id: Optional[str] = None
    tenant_id: Optional[str] = None
    context: Optional[PermissionContext] = None


@dataclass
class AccessDecision:
    """访问决策"""
    allowed: bool
    reason: str
    permission: Permission
    role: Role
    requires_mfa: bool = False
    audit_required: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PermissionViolation:
    """权限违规"""
    user_id: str
    tenant_id: str
    attempted_permission: Permission
    user_role: Role
    resource_type: str
    resource_id: Optional[str]
    violation_type: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)


PERMISSION_MATRIX: Dict[Role, Set[Permission]] = {
    Role.SUPER_ADMIN: {
        # 全部权限
        Permission.TASK_CREATE,
        Permission.TASK_READ,
        Permission.TASK_UPDATE,
        Permission.TASK_DELETE,
        Permission.TASK_LIST,
        Permission.TASK_EXECUTE,
        Permission.INSTANCE_CREATE,
        Permission.INSTANCE_READ,
        Permission.INSTANCE_UPDATE,
        Permission.INSTANCE_DELETE,
        Permission.INSTANCE_LIST,
        Permission.INSTANCE_TERMINATE,
        Permission.HIL_CREATE,
        Permission.HIL_READ,
        Permission.HIL_APPROVE,
        Permission.HIL_REJECT,
        Permission.HIL_MODIFY,
        Permission.REPORT_READ,
        Permission.REPORT_EXPORT,
        Permission.REPORT_DELETE,
        Permission.STORAGE_READ,
        Permission.STORAGE_WRITE,
        Permission.STORAGE_DELETE,
        Permission.ADMIN_READ,
        Permission.ADMIN_WRITE,
        Permission.ADMIN_USERS,
        Permission.ADMIN_TENANT,
        Permission.ADMIN_AUDIT,
        Permission.SECURITY_VIEW,
        Permission.SECURITY_SCAN,
        Permission.SECURITY_CONFIG,
    },
    Role.TENANT_ADMIN: {
        # 租户管理权限
        Permission.TASK_CREATE,
        Permission.TASK_READ,
        Permission.TASK_UPDATE,
        Permission.TASK_DELETE,
        Permission.TASK_LIST,
        Permission.TASK_EXECUTE,
        Permission.INSTANCE_CREATE,
        Permission.INSTANCE_READ,
        Permission.INSTANCE_UPDATE,
        Permission.INSTANCE_DELETE,
        Permission.INSTANCE_LIST,
        Permission.INSTANCE_TERMINATE,
        Permission.HIL_CREATE,
        Permission.HIL_READ,
        Permission.HIL_APPROVE,
        Permission.HIL_REJECT,
        Permission.HIL_MODIFY,
        Permission.REPORT_READ,
        Permission.REPORT_EXPORT,
        Permission.REPORT_DELETE,
        Permission.STORAGE_READ,
        Permission.STORAGE_WRITE,
        Permission.STORAGE_DELETE,
        Permission.ADMIN_READ,
        Permission.ADMIN_USERS,
        Permission.SECURITY_VIEW,
    },
    Role.OPERATOR: {
        # 操作员权限
        Permission.TASK_CREATE,
        Permission.TASK_READ,
        Permission.TASK_UPDATE,
        Permission.TASK_LIST,
        Permission.TASK_EXECUTE,
        Permission.INSTANCE_CREATE,
        Permission.INSTANCE_READ,
        Permission.INSTANCE_UPDATE,
        Permission.INSTANCE_LIST,
        Permission.HIL_CREATE,
        Permission.HIL_READ,
        Permission.REPORT_READ,
        Permission.STORAGE_READ,
    },
    Role.VIEWER: {
        # 查看权限
        Permission.TASK_READ,
        Permission.TASK_LIST,
        Permission.INSTANCE_READ,
        Permission.INSTANCE_LIST,
        Permission.HIL_READ,
        Permission.REPORT_READ,
        Permission.STORAGE_READ,
    },
    Role.AUDITOR: {
        # 审计权限
        Permission.TASK_READ,
        Permission.TASK_LIST,
        Permission.INSTANCE_READ,
        Permission.INSTANCE_LIST,
        Permission.HIL_READ,
        Permission.REPORT_READ,
        Permission.REPORT_EXPORT,
        Permission.ADMIN_AUDIT,
        Permission.SECURITY_VIEW,
    },
    Role.SERVICE: {
        # 服务账号权限
        Permission.TASK_CREATE,
        Permission.TASK_READ,
        Permission.INSTANCE_CREATE,
        Permission.INSTANCE_READ,
        Permission.INSTANCE_UPDATE,
        Permission.HIL_CREATE,
        Permission.HIL_READ,
        Permission.STORAGE_READ,
        Permission.STORAGE_WRITE,
        Permission.SECURITY_SCAN,
    },
}


class PermissionBoundary:
    """权限边界定义"""

    @staticmethod
    def get_tenant_isolation_boundary() -> Set[Permission]:
        """获取需要租户隔离的权限"""
        return {
            Permission.TASK_READ,
            Permission.TASK_UPDATE,
            Permission.TASK_DELETE,
            Permission.INSTANCE_READ,
            Permission.INSTANCE_UPDATE,
            Permission.INSTANCE_DELETE,
            Permission.INSTANCE_TERMINATE,
            Permission.HIL_READ,
            Permission.HIL_APPROVE,
            Permission.HIL_REJECT,
            Permission.HIL_MODIFY,
            Permission.REPORT_READ,
            Permission.STORAGE_READ,
            Permission.STORAGE_WRITE,
            Permission.STORAGE_DELETE,
        }

    @staticmethod
    def get_critical_permissions() -> Set[Permission]:
        """获取高危权限"""
        return {
            Permission.TASK_DELETE,
            Permission.INSTANCE_DELETE,
            Permission.INSTANCE_TERMINATE,
            Permission.REPORT_DELETE,
            Permission.STORAGE_DELETE,
            Permission.ADMIN_WRITE,
            Permission.ADMIN_TENANT,
            Permission.SECURITY_CONFIG,
        }

    @staticmethod
    def get_audit_required_permissions() -> Set[Permission]:
        """获取需要审计的权限"""
        return {
            Permission.TASK_DELETE,
            Permission.INSTANCE_DELETE,
            Permission.INSTANCE_TERMINATE,
            Permission.HIL_APPROVE,
            Permission.HIL_REJECT,
            Permission.HIL_MODIFY,
            Permission.ADMIN_WRITE,
            Permission.ADMIN_TENANT,
            Permission.SECURITY_CONFIG,
        }

    @staticmethod
    def get_mfa_required_permissions() -> Set[Permission]:
        """获取需要 MFA 的权限"""
        return {
            Permission.TASK_DELETE,
            Permission.INSTANCE_DELETE,
            Permission.INSTANCE_TERMINATE,
            Permission.REPORT_DELETE,
            Permission.ADMIN_WRITE,
            Permission.ADMIN_TENANT,
            Permission.SECURITY_CONFIG,
        }


class RBACEngine:
    """RBAC 权限验证引擎"""

    def __init__(self):
        self.permission_matrix = PERMISSION_MATRIX.copy()
        self.violations: List[PermissionViolation] = []
        self.access_logs: List[AccessDecision] = []

    def get_role_permissions(self, role: Role) -> Set[Permission]:
        """获取角色权限"""
        return self.permission_matrix.get(role, set()).copy()

    def has_permission(self, role: Role, permission: Permission) -> bool:
        """检查角色是否拥有指定权限"""
        permissions = self.get_role_permissions(role)
        return permission in permissions

    def check_permission(
        self,
        context: PermissionContext,
        permission: Permission,
        resource_tenant_id: Optional[str] = None,
    ) -> AccessDecision:
        """
        检查权限并返回访问决策

        Args:
            context: 权限上下文
            permission: 请求的权限
            resource_tenant_id: 资源所属租户 ID

        Returns:
            AccessDecision 访问决策
        """
        role = context.role

        if not self.has_permission(role, permission):
            violation = PermissionViolation(
                user_id=context.user_id,
                tenant_id=context.tenant_id,
                attempted_permission=permission,
                user_role=role,
                resource_type="unknown",
                resource_id=None,
                violation_type="PERMISSION_DENIED",
                details={"reason": f"Role {role.value} does not have {permission.value}"},
            )
            self.violations.append(violation)

            decision = AccessDecision(
                allowed=False,
                reason=f"Role {role.value} does not have permission: {permission.value}",
                permission=permission,
                role=role,
            )
            self.access_logs.append(decision)
            return decision

        tenant_boundary = PermissionBoundary.get_tenant_isolation_boundary()
        if permission in tenant_boundary and resource_tenant_id:
            if resource_tenant_id != context.tenant_id:
                violation = PermissionViolation(
                    user_id=context.user_id,
                    tenant_id=context.tenant_id,
                    attempted_permission=permission,
                    user_role=role,
                    resource_type="cross_tenant",
                    resource_id=resource_tenant_id,
                    violation_type="CROSS_TENANT_ACCESS",
                    details={
                        "user_tenant": context.tenant_id,
                        "resource_tenant": resource_tenant_id,
                    },
                )
                self.violations.append(violation)

                decision = AccessDecision(
                    allowed=False,
                    reason=f"Cross-tenant access denied: cannot access resource in tenant {resource_tenant_id}",
                    permission=permission,
                    role=role,
                )
                self.access_logs.append(decision)
                return decision

        requires_mfa = permission in PermissionBoundary.get_mfa_required_permissions()
        audit_required = permission in PermissionBoundary.get_audit_required_permissions()

        decision = AccessDecision(
            allowed=True,
            reason="Permission granted",
            permission=permission,
            role=role,
            requires_mfa=requires_mfa,
            audit_required=audit_required,
        )
        self.access_logs.append(decision)
        return decision

    def validate_permission_matrix(self) -> Dict[str, Any]:
        """
        验证权限矩阵完整性

        Returns:
            验证结果
        """
        all_permissions = set(Permission)
        covered_permissions: Dict[Permission, List[Role]] = {}

        for perm in all_permissions:
            covered_permissions[perm] = []

        for role, perms in self.permission_matrix.items():
            for perm in perms:
                if perm in covered_permissions:
                    covered_permissions[perm].append(role)

        uncovered = [p for p, roles in covered_permissions.items() if len(roles) == 0]

        return {
            "valid": len(uncovered) == 0,
            "total_permissions": len(all_permissions),
            "total_roles": len(self.permission_matrix),
            "uncovered_permissions": [p.value for p in uncovered],
            "permission_coverage": {
                p.value: [r.value for r in roles]
                for p, roles in covered_permissions.items()
            },
        }

    def get_permission_matrix_report(self) -> Dict[str, Any]:
        """生成权限矩阵报告"""
        report = {
            "roles": {},
            "permission_stats": {},
            "high_risk_permissions": [],
        }

        for role, perms in self.permission_matrix.items():
            report["roles"][role.value] = {
                "permission_count": len(perms),
                "permissions": [p.value for p in perms],
                "is_admin": role in (Role.SUPER_ADMIN, Role.TENANT_ADMIN),
            }

        critical_perms = PermissionBoundary.get_critical_permissions()
        for perm in critical_perms:
            roles_with_perm = [
                role.value for role, perms in self.permission_matrix.items()
                if perm in perms
            ]
            report["permission_stats"][perm.value] = {
                "critical": True,
                "assigned_to": roles_with_perm,
            }

        report["high_risk_permissions"] = [p.value for p in critical_perms]

        return report

    def test_permission_boundary(
        self,
        role: Role,
        boundary_permission: Permission,
    ) -> Dict[str, Any]:
        """
        测试权限边界

        Args:
            role: 测试的角色
            boundary_permission: 边界权限

        Returns:
            测试结果
        """
        has_permission = self.has_permission(role, boundary_permission)
        is_critical = boundary_permission in PermissionBoundary.get_critical_permissions()
        requires_mfa = boundary_permission in PermissionBoundary.get_mfa_required_permissions()
        requires_audit = boundary_permission in PermissionBoundary.get_audit_required_permissions()

        if has_permission:
            passes_boundary = True
        else:
            passes_boundary = not is_critical

        return {
            "role": role.value,
            "permission": boundary_permission.value,
            "has_permission": has_permission,
            "is_critical": is_critical,
            "requires_mfa": requires_mfa,
            "requires_audit": requires_audit,
            "passes_boundary": passes_boundary,
        }

    def get_violations_report(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """获取违规报告"""
        violations = self.violations

        if start_time:
            violations = [v for v in violations if v.timestamp >= start_time]
        if end_time:
            violations = [v for v in violations if v.timestamp <= end_time]
        if user_id:
            violations = [v for v in violations if v.user_id == user_id]

        return [
            {
                "user_id": v.user_id,
                "tenant_id": v.tenant_id,
                "attempted_permission": v.attempted_permission.value,
                "user_role": v.user_role.value,
                "violation_type": v.violation_type,
                "timestamp": v.timestamp.isoformat(),
                "details": v.details,
            }
            for v in violations
        ]

    def clear_logs(self):
        """清除日志"""
        self.violations.clear()
        self.access_logs.clear()


_default_engine: Optional[RBACEngine] = None


def get_rbac_engine() -> RBACEngine:
    """获取全局 RBAC 引擎实例"""
    global _default_engine
    if _default_engine is None:
        _default_engine = RBACEngine()
    return _default_engine


def check_permission(
    context: PermissionContext,
    permission: Permission,
    resource_tenant_id: Optional[str] = None,
) -> AccessDecision:
    """
    便捷函数：检查权限

    Args:
        context: 权限上下文
        permission: 请求的权限
        resource_tenant_id: 资源所属租户 ID

    Returns:
        AccessDecision 访问决策
    """
    engine = get_rbac_engine()
    return engine.check_permission(context, permission, resource_tenant_id)


def has_permission(role: Role, permission: Permission) -> bool:
    """
    便捷函数：检查角色是否拥有权限

    Args:
        role: 角色
        permission: 权限

    Returns:
        是否拥有权限
    """
    engine = get_rbac_engine()
    return engine.has_permission(role, permission)


def validate_permission_matrix() -> Dict[str, Any]:
    """
    便捷函数：验证权限矩阵

    Returns:
        验证结果
    """
    engine = get_rbac_engine()
    return engine.validate_permission_matrix()

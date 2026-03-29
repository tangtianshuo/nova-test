"""
RBAC 模块测试
=============

测试 RBAC 权限矩阵验证功能
"""

import pytest
from nova_executor.security.rbac import (
    Permission,
    Role,
    PermissionContext,
    AccessDecision,
    PermissionViolation,
    PermissionBoundary,
    RBACEngine,
    get_rbac_engine,
    check_permission,
    has_permission,
    validate_permission_matrix,
    PERMISSION_MATRIX,
)


class TestPermissionAndRole:
    """测试权限和角色枚举"""

    def test_permission_values(self):
        """测试权限枚举值"""
        assert Permission.TASK_CREATE.value == "task:create"
        assert Permission.INSTANCE_DELETE.value == "instance:delete"
        assert Permission.HIL_APPROVE.value == "hil:approve"
        assert Permission.ADMIN_WRITE.value == "admin:write"

    def test_role_values(self):
        """测试角色枚举值"""
        assert Role.SUPER_ADMIN.value == "super_admin"
        assert Role.TENANT_ADMIN.value == "tenant_admin"
        assert Role.OPERATOR.value == "operator"
        assert Role.VIEWER.value == "viewer"
        assert Role.AUDITOR.value == "auditor"
        assert Role.SERVICE.value == "service"

    def test_permission_count(self):
        """测试权限数量"""
        permissions = list(Permission)
        assert len(permissions) > 20

    def test_role_count(self):
        """测试角色数量"""
        roles = list(Role)
        assert len(roles) == 6


class TestPermissionMatrix:
    """测试权限矩阵"""

    def test_super_admin_has_all_permissions(self):
        """测试超级管理员拥有所有权限"""
        super_admin_perms = PERMISSION_MATRIX[Role.SUPER_ADMIN]
        all_permissions = set(Permission)

        assert super_admin_perms == all_permissions

    def test_viewer_has_minimal_permissions(self):
        """测试查看者拥有最小权限"""
        viewer_perms = PERMISSION_MATRIX[Role.VIEWER]

        assert Permission.TASK_READ in viewer_perms
        assert Permission.INSTANCE_READ in viewer_perms
        assert Permission.TASK_DELETE not in viewer_perms
        assert Permission.INSTANCE_DELETE not in viewer_perms

    def test_operator_can_execute_tasks(self):
        """测试操作员可以执行任务"""
        operator_perms = PERMISSION_MATRIX[Role.OPERATOR]

        assert Permission.TASK_EXECUTE in operator_perms
        assert Permission.INSTANCE_CREATE in operator_perms
        assert Permission.INSTANCE_UPDATE in operator_perms

    def test_service_account_limited_permissions(self):
        """测试服务账号权限受限"""
        service_perms = PERMISSION_MATRIX[Role.SERVICE]

        assert Permission.TASK_CREATE in service_perms
        assert Permission.INSTANCE_CREATE in service_perms
        assert Permission.ADMIN_WRITE not in service_perms
        assert Permission.ADMIN_TENANT not in service_perms


class TestPermissionBoundary:
    """测试权限边界"""

    def test_tenant_isolation_boundary(self):
        """测试租户隔离边界权限"""
        boundary = PermissionBoundary.get_tenant_isolation_boundary()

        assert Permission.TASK_READ in boundary
        assert Permission.INSTANCE_DELETE in boundary
        assert Permission.HIL_APPROVE in boundary
        assert Permission.STORAGE_WRITE in boundary

    def test_critical_permissions(self):
        """测试高危权限"""
        critical = PermissionBoundary.get_critical_permissions()

        assert Permission.INSTANCE_DELETE in critical
        assert Permission.INSTANCE_TERMINATE in critical
        assert Permission.ADMIN_TENANT in critical
        assert Permission.SECURITY_CONFIG in critical

    def test_mfa_required_permissions(self):
        """测试需要 MFA 的权限"""
        mfa_required = PermissionBoundary.get_mfa_required_permissions()

        assert Permission.INSTANCE_TERMINATE in mfa_required
        assert Permission.ADMIN_WRITE in mfa_required
        assert Permission.SECURITY_CONFIG in mfa_required

    def test_audit_required_permissions(self):
        """测试需要审计的权限"""
        audit_required = PermissionBoundary.get_audit_required_permissions()

        assert Permission.INSTANCE_DELETE in audit_required
        assert Permission.HIL_APPROVE in audit_required
        assert Permission.HIL_MODIFY in audit_required


class TestRBACEngine:
    """测试 RBAC 引擎"""

    def test_engine_initialization(self):
        """测试引擎初始化"""
        engine = RBACEngine()
        assert engine is not None
        assert len(engine.permission_matrix) > 0

    def test_get_role_permissions(self):
        """测试获取角色权限"""
        engine = RBACEngine()

        viewer_perms = engine.get_role_permissions(Role.VIEWER)
        assert Permission.TASK_READ in viewer_perms
        assert Permission.INSTANCE_READ in viewer_perms

        admin_perms = engine.get_role_permissions(Role.SUPER_ADMIN)
        assert len(admin_perms) > len(viewer_perms)

    def test_has_permission_true(self):
        """测试角色有所需权限"""
        engine = RBACEngine()

        assert engine.has_permission(Role.SUPER_ADMIN, Permission.TASK_DELETE) is True
        assert engine.has_permission(Role.OPERATOR, Permission.TASK_EXECUTE) is True
        assert engine.has_permission(Role.VIEWER, Permission.TASK_READ) is True

    def test_has_permission_false(self):
        """测试角色无所需权限"""
        engine = RBACEngine()

        assert engine.has_permission(Role.VIEWER, Permission.TASK_DELETE) is False
        assert engine.has_permission(Role.VIEWER, Permission.INSTANCE_DELETE) is False
        assert engine.has_permission(Role.OPERATOR, Permission.ADMIN_WRITE) is False

    def test_check_permission_allowed(self):
        """测试权限检查允许"""
        engine = RBACEngine()
        context = PermissionContext(
            user_id="user_001",
            tenant_id="tenant_a",
            role=Role.OPERATOR,
        )

        decision = engine.check_permission(context, Permission.TASK_EXECUTE)

        assert decision.allowed is True
        assert decision.permission == Permission.TASK_EXECUTE
        assert decision.role == Role.OPERATOR

    def test_check_permission_denied(self):
        """测试权限检查拒绝"""
        engine = RBACEngine()
        context = PermissionContext(
            user_id="user_001",
            tenant_id="tenant_a",
            role=Role.VIEWER,
        )

        decision = engine.check_permission(context, Permission.INSTANCE_DELETE)

        assert decision.allowed is False
        assert "does not have permission" in decision.reason

    def test_check_permission_cross_tenant_blocked(self):
        """测试跨租户访问被阻止"""
        engine = RBACEngine()
        context = PermissionContext(
            user_id="user_001",
            tenant_id="tenant_a",
            role=Role.TENANT_ADMIN,
        )

        decision = engine.check_permission(
            context,
            Permission.INSTANCE_READ,
            resource_tenant_id="tenant_b",
        )

        assert decision.allowed is False
        assert "Cross-tenant access denied" in decision.reason

    def test_check_permission_same_tenant_allowed(self):
        """测试同租户访问允许"""
        engine = RBACEngine()
        context = PermissionContext(
            user_id="user_001",
            tenant_id="tenant_a",
            role=Role.TENANT_ADMIN,
        )

        decision = engine.check_permission(
            context,
            Permission.INSTANCE_READ,
            resource_tenant_id="tenant_a",
        )

        assert decision.allowed is True

    def test_check_permission_mfa_required(self):
        """测试高危权限需要 MFA"""
        engine = RBACEngine()
        context = PermissionContext(
            user_id="user_001",
            tenant_id="tenant_a",
            role=Role.SUPER_ADMIN,
        )

        decision = engine.check_permission(context, Permission.INSTANCE_TERMINATE)

        assert decision.allowed is True
        assert decision.requires_mfa is True

    def test_check_permission_audit_required(self):
        """测试敏感操作需要审计"""
        engine = RBACEngine()
        context = PermissionContext(
            user_id="user_001",
            tenant_id="tenant_a",
            role=Role.SUPER_ADMIN,
        )

        decision = engine.check_permission(context, Permission.HIL_APPROVE)

        assert decision.allowed is True
        assert decision.audit_required is True

    def test_validate_permission_matrix(self):
        """测试权限矩阵验证"""
        engine = RBACEngine()
        result = engine.validate_permission_matrix()

        assert result["valid"] is True
        assert result["total_permissions"] > 0
        assert result["total_roles"] == 6
        assert len(result["uncovered_permissions"]) == 0

    def test_get_permission_matrix_report(self):
        """测试权限矩阵报告"""
        engine = RBACEngine()
        report = engine.get_permission_matrix_report()

        assert "roles" in report
        assert "permission_stats" in report
        assert "high_risk_permissions" in report

        assert "super_admin" in report["roles"]
        assert report["roles"]["super_admin"]["is_admin"] is True
        assert report["roles"]["viewer"]["is_admin"] is False

    def test_test_permission_boundary(self):
        """测试权限边界检查"""
        engine = RBACEngine()

        result = engine.test_permission_boundary(Role.VIEWER, Permission.TASK_READ)

        assert result["role"] == "viewer"
        assert result["permission"] == "task:read"
        assert result["has_permission"] is True
        assert result["is_critical"] is False
        assert result["passes_boundary"] is True

    def test_violations_logged(self):
        """测试违规被记录"""
        engine = RBACEngine()
        engine.clear_logs()

        context = PermissionContext(
            user_id="user_001",
            tenant_id="tenant_a",
            role=Role.VIEWER,
        )

        engine.check_permission(context, Permission.INSTANCE_DELETE)

        assert len(engine.violations) == 1
        assert engine.violations[0].violation_type == "PERMISSION_DENIED"

    def test_get_violations_report(self):
        """测试获取违规报告"""
        engine = RBACEngine()
        engine.clear_logs()

        context = PermissionContext(
            user_id="user_001",
            tenant_id="tenant_a",
            role=Role.VIEWER,
        )
        engine.check_permission(context, Permission.INSTANCE_DELETE)

        report = engine.get_violations_report()

        assert len(report) == 1
        assert report[0]["violation_type"] == "PERMISSION_DENIED"
        assert report[0]["user_id"] == "user_001"


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_check_permission_function(self):
        """测试便捷权限检查函数"""
        context = PermissionContext(
            user_id="user_001",
            tenant_id="tenant_a",
            role=Role.OPERATOR,
        )

        decision = check_permission(context, Permission.TASK_EXECUTE)
        assert decision.allowed is True

        decision = check_permission(context, Permission.INSTANCE_DELETE)
        assert decision.allowed is False

    def test_has_permission_function(self):
        """测试便捷权限判断函数"""
        assert has_permission(Role.VIEWER, Permission.TASK_READ) is True
        assert has_permission(Role.VIEWER, Permission.INSTANCE_DELETE) is False

    def test_validate_permission_matrix_function(self):
        """测试便捷矩阵验证函数"""
        result = validate_permission_matrix()
        assert result["valid"] is True


class TestRolePermissionAssignment:
    """测试角色权限分配"""

    def test_tenant_admin_cannot_access_other_tenant_admin(self):
        """测试租户管理员不能访问其他租户管理员功能"""
        engine = RBACEngine()

        tenant_admin_perms = engine.get_role_permissions(Role.TENANT_ADMIN)
        assert Permission.ADMIN_TENANT not in tenant_admin_perms

    def test_auditor_can_export_reports(self):
        """测试审计员可以导出报告"""
        engine = RBACEngine()

        auditor_perms = engine.get_role_permissions(Role.AUDITOR)
        assert Permission.REPORT_EXPORT in auditor_perms

    def test_auditor_cannot_modify(self):
        """测试审计员不能修改"""
        engine = RBACEngine()

        auditor_perms = engine.get_role_permissions(Role.AUDITOR)
        assert Permission.INSTANCE_UPDATE not in auditor_perms
        assert Permission.TASK_UPDATE not in auditor_perms


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

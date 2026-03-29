"""
租户隔离模块测试
================

测试租户隔离验证功能
"""

import pytest
from nova_executor.security.tenant_isolation import (
    IsolationLevel,
    ResourceType,
    Tenant,
    TenantContext,
    Resource,
    IsolationViolation,
    IsolationTestResult,
    TenantIsolationPolicy,
    TenantIsolationEngine,
    get_isolation_engine,
    check_cross_tenant_access,
    validate_query_filter,
    enforce_query_filter,
)


class TestIsolationEnums:
    """测试隔离枚举"""

    def test_isolation_level_values(self):
        """测试隔离级别枚举值"""
        assert IsolationLevel.STRICT.value == "strict"
        assert IsolationLevel.SOFT.value == "soft"
        assert IsolationLevel.NONE.value == "none"

    def test_resource_type_values(self):
        """测试资源类型枚举值"""
        assert ResourceType.TASK.value == "task"
        assert ResourceType.INSTANCE.value == "instance"
        assert ResourceType.REPORT.value == "report"
        assert ResourceType.STORAGE.value == "storage"
        assert ResourceType.HIL_TICKET.value == "hil_ticket"


class TestTenantAndResource:
    """测试租户和资源"""

    def test_tenant_creation(self):
        """测试租户创建"""
        tenant = Tenant(
            id="tenant_001",
            name="Test Tenant",
            tier="premium",
        )

        assert tenant.id == "tenant_001"
        assert tenant.name == "Test Tenant"
        assert tenant.tier == "premium"

    def test_tenant_context_creation(self):
        """测试租户上下文创建"""
        context = TenantContext(
            tenant_id="tenant_001",
            user_id="user_001",
            session_id="session_001",
        )

        assert context.tenant_id == "tenant_001"
        assert context.user_id == "user_001"
        assert context.session_id == "session_001"

    def test_resource_creation(self):
        """测试资源创建"""
        resource = Resource(
            id="resource_001",
            type=ResourceType.INSTANCE,
            tenant_id="tenant_001",
            owner_id="owner_001",
        )

        assert resource.id == "resource_001"
        assert resource.type == ResourceType.INSTANCE
        assert resource.tenant_id == "tenant_001"


class TestTenantIsolationPolicy:
    """测试租户隔离策略"""

    def test_get_isolated_resource_types(self):
        """测试需要隔离的资源类型"""
        isolated = TenantIsolationPolicy.get_isolated_resource_types()

        assert ResourceType.TASK in isolated
        assert ResourceType.INSTANCE in isolated
        assert ResourceType.REPORT in isolated
        assert ResourceType.STORAGE in isolated
        assert ResourceType.HIL_TICKET in isolated

    def test_get_cross_tenant_allowed_actions(self):
        """测试允许的跨租户操作"""
        allowed = TenantIsolationPolicy.get_cross_tenant_allowed_actions()

        assert "read" in allowed.get(ResourceType.TASK, set())
        assert "read" in allowed.get(ResourceType.INSTANCE, set())

    def test_requires_tenant_filter(self):
        """测试是否需要租户过滤"""
        assert TenantIsolationPolicy.requires_tenant_filter(ResourceType.TASK) is True
        assert TenantIsolationPolicy.requires_tenant_filter(ResourceType.INSTANCE) is True


class TestTenantIsolationEngine:
    """测试租户隔离引擎"""

    def test_engine_initialization(self):
        """测试引擎初始化"""
        engine = TenantIsolationEngine()
        assert engine is not None
        assert engine.isolation_level == IsolationLevel.STRICT

    def test_engine_with_different_isolation_level(self):
        """测试不同隔离级别的引擎"""
        engine = TenantIsolationEngine(IsolationLevel.SOFT)
        assert engine.isolation_level == IsolationLevel.SOFT

    def test_register_tenant(self):
        """测试注册租户"""
        engine = TenantIsolationEngine()
        tenant = Tenant(id="tenant_001", name="Test Tenant")

        engine.register_tenant(tenant)

        assert "tenant_001" in engine._tenant_cache

    def test_register_resource(self):
        """测试注册资源"""
        engine = TenantIsolationEngine()
        resource = Resource(
            id="resource_001",
            type=ResourceType.INSTANCE,
            tenant_id="tenant_001",
        )

        engine.register_resource(resource)

        assert "resource_001" in engine._resource_cache


class TestCrossTenantAccess:
    """测试跨租户访问"""

    def test_same_tenant_access_allowed(self):
        """测试同租户访问允许"""
        engine = TenantIsolationEngine()
        context = TenantContext(
            tenant_id="tenant_a",
            user_id="user_001",
        )
        resource = Resource(
            id="resource_001",
            type=ResourceType.INSTANCE,
            tenant_id="tenant_a",
        )

        allowed = engine.check_cross_tenant_access(context, resource, "read")

        assert allowed is True

    def test_cross_tenant_access_blocked_strict(self):
        """测试严格模式下跨租户访问被阻止"""
        engine = TenantIsolationEngine(IsolationLevel.STRICT)
        context = TenantContext(
            tenant_id="tenant_a",
            user_id="user_001",
        )
        resource = Resource(
            id="resource_001",
            type=ResourceType.INSTANCE,
            tenant_id="tenant_b",
        )

        allowed = engine.check_cross_tenant_access(context, resource, "delete")

        assert allowed is False
        assert len(engine.violations) == 1
        assert engine.violations[0].violation_type == "CROSS_TENANT_ACCESS"

    def test_cross_tenant_read_allowed_in_soft_mode(self):
        """测试软模式下允许跨租户读取"""
        engine = TenantIsolationEngine(IsolationLevel.SOFT)
        context = TenantContext(
            tenant_id="tenant_a",
            user_id="user_001",
        )
        resource = Resource(
            id="resource_001",
            type=ResourceType.INSTANCE,
            tenant_id="tenant_b",
        )

        allowed = engine.check_cross_tenant_access(context, resource, "read")

        assert allowed is True


class TestQueryFilter:
    """测试查询过滤"""

    def test_validate_query_filter_with_tenant_id(self):
        """测试包含租户 ID 的查询验证"""
        engine = TenantIsolationEngine()
        context = TenantContext(
            tenant_id="tenant_001",
            user_id="user_001",
        )
        query = {
            "status": "active",
            "tenant_id": "tenant_001",
            "limit": 100,
        }

        result = engine.validate_query_filter(context, ResourceType.INSTANCE, query)

        assert result["valid"] is True

    def test_validate_query_filter_missing_tenant_id(self):
        """测试缺少租户 ID 的查询验证"""
        engine = TenantIsolationEngine()
        context = TenantContext(
            tenant_id="tenant_001",
            user_id="user_001",
        )
        query = {
            "status": "active",
            "limit": 100,
        }

        result = engine.validate_query_filter(context, ResourceType.INSTANCE, query)

        assert result["valid"] is False
        assert "tenant filter" in result["reason"].lower()

    def test_validate_query_filter_wrong_tenant_id(self):
        """测试错误租户 ID 的查询验证"""
        engine = TenantIsolationEngine()
        context = TenantContext(
            tenant_id="tenant_001",
            user_id="user_001",
        )
        query = {
            "status": "active",
            "tenant_id": "tenant_002",
            "limit": 100,
        }

        result = engine.validate_query_filter(context, ResourceType.INSTANCE, query)

        assert result["valid"] is False

    def test_enforce_query_filter(self):
        """测试强制添加租户过滤"""
        engine = TenantIsolationEngine()
        context = TenantContext(
            tenant_id="tenant_001",
            user_id="user_001",
        )
        query = {"status": "active", "limit": 100}

        filtered = engine.enforce_query_filter(context, ResourceType.INSTANCE, query)

        assert filtered["tenant_id"] == "tenant_001"
        assert filtered["status"] == "active"

    def test_enforce_query_filter_preserves_existing(self):
        """测试强制添加保留已有租户 ID"""
        engine = TenantIsolationEngine()
        context = TenantContext(
            tenant_id="tenant_001",
            user_id="user_001",
        )
        query = {"status": "active", "tenant_id": "tenant_001"}

        filtered = engine.enforce_query_filter(context, ResourceType.INSTANCE, query)

        assert filtered["tenant_id"] == "tenant_001"


class TestIsolationTests:
    """测试隔离测试"""

    def test_same_tenant_access_test(self):
        """测试同租户访问测试"""
        engine = TenantIsolationEngine()

        result = engine.test_same_tenant_access(
            "tenant_a",
            "tenant_a",
            ResourceType.INSTANCE,
        )

        assert result.passed is True
        assert result.source_tenant_id == "tenant_a"
        assert result.target_tenant_id == "tenant_a"

    def test_cross_tenant_access_blocked_test(self):
        """测试跨租户访问被阻止测试"""
        engine = TenantIsolationEngine()

        result = engine.test_cross_tenant_access_blocked(
            "tenant_a",
            "tenant_b",
            ResourceType.INSTANCE,
            "delete",
        )

        assert result.passed is True
        assert result.violation_type == "CROSS_TENANT_ACCESS"

    def test_query_filter_missing_test(self):
        """测试查询缺少租户过滤测试"""
        engine = TenantIsolationEngine()
        context = TenantContext(
            tenant_id="tenant_001",
            user_id="user_001",
        )

        result = engine.test_query_filter_missing(context)

        assert result.passed is True
        assert result.violation_type == "MISSING_TENANT_FILTER"

    def test_query_filter_present_test(self):
        """测试查询包含租户过滤测试"""
        engine = TenantIsolationEngine()
        context = TenantContext(
            tenant_id="tenant_001",
            user_id="user_001",
        )

        result = engine.test_query_filter_present(context)

        assert result.passed is True
        assert result.violation_type is None

    def test_query_filter_wrong_tenant_test(self):
        """测试查询错误租户过滤测试"""
        engine = TenantIsolationEngine()
        context = TenantContext(
            tenant_id="tenant_001",
            user_id="user_001",
        )

        result = engine.test_query_filter_wrong_tenant(context)

        assert result.passed is True
        assert result.violation_type == "INVALID_TENANT_FILTER"

    def test_run_all_tests(self):
        """测试运行所有测试"""
        engine = TenantIsolationEngine()
        engine.clear_logs()

        result = engine.run_all_tests()

        assert "total_tests" in result
        assert "passed" in result
        assert "failed" in result
        assert result["total_tests"] > 0


class TestViolationsReport:
    """测试违规报告"""

    def test_get_violations_report(self):
        """测试获取违规报告"""
        engine = TenantIsolationEngine()
        engine.clear_logs()

        context = TenantContext(
            tenant_id="tenant_a",
            user_id="user_001",
        )
        resource = Resource(
            id="resource_001",
            type=ResourceType.INSTANCE,
            tenant_id="tenant_b",
        )
        engine.check_cross_tenant_access(context, resource, "delete")

        report = engine.get_violations_report()

        assert len(report) == 1
        assert report[0]["violation_type"] == "CROSS_TENANT_ACCESS"
        assert report[0]["source_tenant_id"] == "tenant_a"
        assert report[0]["target_tenant_id"] == "tenant_b"

    def test_get_violations_report_filtered_by_tenant(self):
        """测试按租户过滤违规报告"""
        engine = TenantIsolationEngine()
        engine.clear_logs()

        context1 = TenantContext(
            tenant_id="tenant_a",
            user_id="user_001",
        )
        resource1 = Resource(
            id="resource_001",
            type=ResourceType.INSTANCE,
            tenant_id="tenant_b",
        )
        engine.check_cross_tenant_access(context1, resource1, "delete")

        context2 = TenantContext(
            tenant_id="tenant_c",
            user_id="user_002",
        )
        resource2 = Resource(
            id="resource_002",
            type=ResourceType.INSTANCE,
            tenant_id="tenant_d",
        )
        engine.check_cross_tenant_access(context2, resource2, "delete")

        report = engine.get_violations_report(source_tenant_id="tenant_a")

        assert len(report) == 1
        assert report[0]["source_tenant_id"] == "tenant_a"


class TestIsolationStatus:
    """测试隔离状态"""

    def test_get_isolation_status(self):
        """测试获取隔离状态"""
        engine = TenantIsolationEngine()

        status = engine.get_isolation_status()

        assert "isolation_level" in status
        assert "total_violations" in status
        assert "total_tests_run" in status
        assert status["isolation_level"] == "strict"

    def test_clear_logs(self):
        """测试清除日志"""
        engine = TenantIsolationEngine()

        context = TenantContext(
            tenant_id="tenant_a",
            user_id="user_001",
        )
        resource = Resource(
            id="resource_001",
            type=ResourceType.INSTANCE,
            tenant_id="tenant_b",
        )
        engine.check_cross_tenant_access(context, resource, "delete")

        assert len(engine.violations) == 1

        engine.clear_logs()

        assert len(engine.violations) == 0
        assert len(engine.test_results) == 0


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_check_cross_tenant_access_function(self):
        """测试便捷跨租户访问检查函数"""
        context = TenantContext(
            tenant_id="tenant_a",
            user_id="user_001",
        )
        resource = Resource(
            id="resource_001",
            type=ResourceType.INSTANCE,
            tenant_id="tenant_a",
        )

        allowed = check_cross_tenant_access(context, resource, "read")
        assert allowed is True

        resource_cross = Resource(
            id="resource_002",
            type=ResourceType.INSTANCE,
            tenant_id="tenant_b",
        )

        allowed = check_cross_tenant_access(context, resource_cross, "delete")
        assert allowed is False

    def test_validate_query_filter_function(self):
        """测试便捷查询验证函数"""
        context = TenantContext(
            tenant_id="tenant_001",
            user_id="user_001",
        )
        query = {
            "status": "active",
            "tenant_id": "tenant_001",
        }

        result = validate_query_filter(context, ResourceType.INSTANCE, query)
        assert result["valid"] is True

    def test_enforce_query_filter_function(self):
        """测试便捷查询过滤函数"""
        context = TenantContext(
            tenant_id="tenant_001",
            user_id="user_001",
        )
        query = {"status": "active"}

        filtered = enforce_query_filter(context, ResourceType.INSTANCE, query)
        assert filtered["tenant_id"] == "tenant_001"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

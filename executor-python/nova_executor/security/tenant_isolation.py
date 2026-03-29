"""
租户隔离验证模块
================

提供多租户环境下的数据隔离验证功能：
1. 实现跨租户访问拦截
2. 添加租户数据隔离测试
3. 验证查询过滤逻辑
4. 编写租户隔离负向测试
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Callable
from datetime import datetime


class IsolationLevel(str, Enum):
    """隔离级别"""
    STRICT = "strict"
    SOFT = "soft"
    NONE = "none"


class ResourceType(str, Enum):
    """资源类型"""
    TASK = "task"
    INSTANCE = "instance"
    REPORT = "report"
    STORAGE = "storage"
    HIL_TICKET = "hil_ticket"
    USER = "user"
    CONFIG = "config"


@dataclass
class Tenant:
    """租户"""
    id: str
    name: str
    tier: str = "standard"
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TenantContext:
    """租户上下文"""
    tenant_id: str
    user_id: str
    session_id: Optional[str] = None
    ip_address: Optional[str] = None


@dataclass
class Resource:
    """资源"""
    id: str
    type: ResourceType
    tenant_id: str
    owner_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IsolationViolation:
    """隔离违规"""
    violation_id: str
    violation_type: str
    source_tenant_id: str
    target_tenant_id: str
    resource_type: ResourceType
    resource_id: Optional[str]
    attempted_action: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IsolationTestResult:
    """隔离测试结果"""
    test_name: str
    passed: bool
    source_tenant_id: str
    target_tenant_id: Optional[str]
    resource_type: ResourceType
    violation_type: Optional[str]
    message: str
    timestamp: datetime = field(default_factory=datetime.now)


class TenantIsolationPolicy:
    """租户隔离策略"""

    @staticmethod
    def get_isolated_resource_types() -> Set[ResourceType]:
        """获取需要隔离的资源类型"""
        return {
            ResourceType.TASK,
            ResourceType.INSTANCE,
            ResourceType.REPORT,
            ResourceType.STORAGE,
            ResourceType.HIL_TICKET,
            ResourceType.CONFIG,
        }

    @staticmethod
    def get_cross_tenant_allowed_actions() -> Dict[ResourceType, Set[str]]:
        """获取允许的跨租户操作"""
        return {
            ResourceType.USER: {"read_profile", "list"},
            ResourceType.TASK: {"read"},
            ResourceType.INSTANCE: {"read"},
        }

    @staticmethod
    def requires_tenant_filter(resource_type: ResourceType) -> bool:
        """检查资源类型是否需要租户过滤"""
        return resource_type in TenantIsolationPolicy.get_isolated_resource_types()


class TenantIsolationEngine:
    """租户隔离验证引擎"""

    def __init__(self, isolation_level: IsolationLevel = IsolationLevel.STRICT):
        self.isolation_level = isolation_level
        self.violations: List[IsolationViolation] = []
        self.test_results: List[IsolationTestResult] = []
        self._tenant_cache: Dict[str, Tenant] = {}
        self._resource_cache: Dict[str, Resource] = {}

    def register_tenant(self, tenant: Tenant):
        """注册租户"""
        self._tenant_cache[tenant.id] = tenant

    def register_resource(self, resource: Resource):
        """注册资源"""
        self._resource_cache[resource.id] = resource

    def check_cross_tenant_access(
        self,
        context: TenantContext,
        resource: Resource,
        action: str,
    ) -> bool:
        """
        检查跨租户访问

        Args:
            context: 租户上下文
            resource: 目标资源
            action: 操作类型

        Returns:
            是否允许访问
        """
        if resource.tenant_id == context.tenant_id:
            return True

        allowed_actions = TenantIsolationPolicy.get_cross_tenant_allowed_actions()
        resource_allowed = allowed_actions.get(resource.type, set())

        if action in resource_allowed:
            return True

        if self.isolation_level == IsolationLevel.STRICT:
            violation = IsolationViolation(
                violation_id=f"vio_{len(self.violations) + 1}",
                violation_type="CROSS_TENANT_ACCESS",
                source_tenant_id=context.tenant_id,
                target_tenant_id=resource.tenant_id,
                resource_type=resource.type,
                resource_id=resource.id,
                attempted_action=action,
                details={
                    "user_id": context.user_id,
                    "resource_owner": resource.owner_id,
                },
            )
            self.violations.append(violation)
            return False

        return self.isolation_level != IsolationLevel.NONE

    def validate_query_filter(
        self,
        context: TenantContext,
        resource_type: ResourceType,
        query: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        验证查询是否包含租户过滤

        Args:
            context: 租户上下文
            resource_type: 资源类型
            query: 查询条件

        Returns:
            验证结果
        """
        if not TenantIsolationPolicy.requires_tenant_filter(resource_type):
            return {
                "valid": True,
                "reason": f"Resource type {resource_type.value} does not require tenant filter",
            }

        tenant_filter_keys = ["tenant_id", "tenant", "owner_tenant", "organization_id"]

        has_tenant_filter = False
        for key in tenant_filter_keys:
            if key in query:
                has_tenant_filter = True
                if query[key] != context.tenant_id:
                    return {
                        "valid": False,
                        "reason": f"Query contains invalid tenant filter: {key}={query[key]}",
                        "expected": context.tenant_id,
                        "actual": query[key],
                    }

        if not has_tenant_filter:
            violation = IsolationViolation(
                violation_id=f"vio_{len(self.violations) + 1}",
                violation_type="MISSING_TENANT_FILTER",
                source_tenant_id=context.tenant_id,
                target_tenant_id="any",
                resource_type=resource_type,
                resource_id=None,
                attempted_action="query",
                details={"query": query},
            )
            self.violations.append(violation)

            return {
                "valid": False,
                "reason": "Query missing required tenant filter",
                "required_filter": "tenant_id",
                "context_tenant": context.tenant_id,
            }

        return {
            "valid": True,
            "reason": "Query contains valid tenant filter",
        }

    def enforce_query_filter(
        self,
        context: TenantContext,
        resource_type: ResourceType,
        query: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        强制添加租户过滤到查询

        Args:
            context: 租户上下文
            resource_type: 资源类型
            query: 查询条件

        Returns:
            添加租户过滤后的查询
        """
        if not TenantIsolationPolicy.requires_tenant_filter(resource_type):
            return query

        filtered_query = query.copy()
        filtered_query["tenant_id"] = context.tenant_id

        return filtered_query

    def test_same_tenant_access(
        self,
        source_tenant_id: str,
        target_tenant_id: str,
        resource_type: ResourceType,
        action: str = "read",
    ) -> IsolationTestResult:
        """
        测试同租户访问（应该成功）

        Args:
            source_tenant_id: 源租户 ID
            target_tenant_id: 目标租户 ID
            resource_type: 资源类型
            action: 操作

        Returns:
            测试结果
        """
        context = TenantContext(
            tenant_id=source_tenant_id,
            user_id=f"user_{source_tenant_id}",
        )

        resource = Resource(
            id=f"{resource_type.value}_{target_tenant_id}_001",
            type=resource_type,
            tenant_id=target_tenant_id,
        )

        allowed = self.check_cross_tenant_access(context, resource, action)

        return IsolationTestResult(
            test_name="same_tenant_access",
            passed=allowed,
            source_tenant_id=source_tenant_id,
            target_tenant_id=target_tenant_id,
            resource_type=resource_type,
            violation_type=None if allowed else "unexpected_denial",
            message="Same tenant access should be allowed" if allowed else "Same tenant access was denied unexpectedly",
        )

    def test_cross_tenant_access_blocked(
        self,
        source_tenant_id: str,
        target_tenant_id: str,
        resource_type: ResourceType,
        action: str = "delete",
    ) -> IsolationTestResult:
        """
        测试跨租户访问被阻止（应该失败）

        Args:
            source_tenant_id: 源租户 ID
            target_tenant_id: 目标租户 ID
            resource_type: 资源类型
            action: 操作

        Returns:
            测试结果
        """
        context = TenantContext(
            tenant_id=source_tenant_id,
            user_id=f"user_{source_tenant_id}",
        )

        resource = Resource(
            id=f"{resource_type.value}_{target_tenant_id}_001",
            type=resource_type,
            tenant_id=target_tenant_id,
        )

        allowed = self.check_cross_tenant_access(context, resource, action)

        return IsolationTestResult(
            test_name="cross_tenant_access_blocked",
            passed=not allowed,
            source_tenant_id=source_tenant_id,
            target_tenant_id=target_tenant_id,
            resource_type=resource_type,
            violation_type="CROSS_TENANT_ACCESS" if not allowed else None,
            message="Cross-tenant access was correctly blocked" if not allowed else "Cross-tenant access should be blocked but was allowed",
        )

    def test_query_filter_missing(self, context: TenantContext) -> IsolationTestResult:
        """
        测试缺少租户过滤的查询

        Args:
            context: 租户上下文

        Returns:
            测试结果
        """
        query = {"status": "active", "limit": 100}
        result = self.validate_query_filter(context, ResourceType.INSTANCE, query)

        return IsolationTestResult(
            test_name="query_filter_missing",
            passed=not result["valid"],
            source_tenant_id=context.tenant_id,
            target_tenant_id=None,
            resource_type=ResourceType.INSTANCE,
            violation_type="MISSING_TENANT_FILTER" if not result["valid"] else None,
            message=result["reason"],
        )

    def test_query_filter_present(self, context: TenantContext) -> IsolationTestResult:
        """
        测试包含租户过滤的查询

        Args:
            context: 租户上下文

        Returns:
            测试结果
        """
        query = {"status": "active", "tenant_id": context.tenant_id, "limit": 100}
        result = self.validate_query_filter(context, ResourceType.INSTANCE, query)

        return IsolationTestResult(
            test_name="query_filter_present",
            passed=result["valid"],
            source_tenant_id=context.tenant_id,
            target_tenant_id=None,
            resource_type=ResourceType.INSTANCE,
            violation_type=None if result["valid"] else "unexpected_filter_error",
            message=result["reason"],
        )

    def test_query_filter_wrong_tenant(self, context: TenantContext) -> IsolationTestResult:
        """
        测试错误租户过滤的查询

        Args:
            context: 租户上下文

        Returns:
            测试结果
        """
        other_tenant = f"other_{context.tenant_id}"
        query = {"status": "active", "tenant_id": other_tenant, "limit": 100}
        result = self.validate_query_filter(context, ResourceType.INSTANCE, query)

        return IsolationTestResult(
            test_name="query_filter_wrong_tenant",
            passed=not result["valid"],
            source_tenant_id=context.tenant_id,
            target_tenant_id=other_tenant,
            resource_type=ResourceType.INSTANCE,
            violation_type="INVALID_TENANT_FILTER" if not result["valid"] else None,
            message=result["reason"],
        )

    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有隔离测试"""
        test_results = []
        tenants = ["tenant_a", "tenant_b"]

        for source in tenants:
            for target in tenants:
                for resource_type in [
                    ResourceType.TASK,
                    ResourceType.INSTANCE,
                    ResourceType.REPORT,
                    ResourceType.STORAGE,
                ]:
                    context = TenantContext(
                        tenant_id=source,
                        user_id=f"user_{source}",
                    )

                    if source == target:
                        test_results.append(self.test_same_tenant_access(source, target, resource_type))
                    else:
                        for action in ["read", "update", "delete"]:
                            test_results.append(
                                self.test_cross_tenant_access_blocked(source, target, resource_type, action)
                            )

                    test_results.append(self.test_query_filter_missing(context))
                    test_results.append(self.test_query_filter_present(context))
                    test_results.append(self.test_query_filter_wrong_tenant(context))

        self.test_results.extend(test_results)

        passed = sum(1 for r in test_results if r.passed)
        failed = sum(1 for r in test_results if not r.passed)

        return {
            "total_tests": len(test_results),
            "passed": passed,
            "failed": failed,
            "success_rate": passed / len(test_results) if test_results else 0,
            "test_results": [
                {
                    "test_name": r.test_name,
                    "passed": r.passed,
                    "message": r.message,
                    "violation_type": r.violation_type,
                }
                for r in test_results
            ],
        }

    def get_violations_report(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        source_tenant_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """获取违规报告"""
        violations = self.violations

        if start_time:
            violations = [v for v in violations if v.timestamp >= start_time]
        if end_time:
            violations = [v for v in violations if v.timestamp <= end_time]
        if source_tenant_id:
            violations = [v for v in violations if v.source_tenant_id == source_tenant_id]

        return [
            {
                "violation_id": v.violation_id,
                "violation_type": v.violation_type,
                "source_tenant_id": v.source_tenant_id,
                "target_tenant_id": v.target_tenant_id,
                "resource_type": v.resource_type.value,
                "resource_id": v.resource_id,
                "attempted_action": v.attempted_action,
                "timestamp": v.timestamp.isoformat(),
                "details": v.details,
            }
            for v in violations
        ]

    def get_isolation_status(self) -> Dict[str, Any]:
        """获取隔离状态"""
        return {
            "isolation_level": self.isolation_level.value,
            "total_violations": len(self.violations),
            "total_tests_run": len(self.test_results),
            "tests_passed": sum(1 for r in self.test_results if r.passed),
            "tests_failed": sum(1 for r in self.test_results if not r.passed),
            "registered_tenants": len(self._tenant_cache),
            "registered_resources": len(self._resource_cache),
        }

    def clear_logs(self):
        """清除日志"""
        self.violations.clear()
        self.test_results.clear()


_default_engine: Optional[TenantIsolationEngine] = None


def get_isolation_engine(isolation_level: IsolationLevel = IsolationLevel.STRICT) -> TenantIsolationEngine:
    """获取全局隔离引擎实例"""
    global _default_engine
    if _default_engine is None:
        _default_engine = TenantIsolationEngine(isolation_level)
    return _default_engine


def check_cross_tenant_access(
    context: TenantContext,
    resource: Resource,
    action: str,
) -> bool:
    """
    便捷函数：检查跨租户访问

    Args:
        context: 租户上下文
        resource: 目标资源
        action: 操作类型

    Returns:
        是否允许访问
    """
    engine = get_isolation_engine()
    return engine.check_cross_tenant_access(context, resource, action)


def validate_query_filter(
    context: TenantContext,
    resource_type: ResourceType,
    query: Dict[str, Any],
) -> Dict[str, Any]:
    """
    便捷函数：验证查询租户过滤

    Args:
        context: 租户上下文
        resource_type: 资源类型
        query: 查询条件

    Returns:
        验证结果
    """
    engine = get_isolation_engine()
    return engine.validate_query_filter(context, resource_type, query)


def enforce_query_filter(
    context: TenantContext,
    resource_type: ResourceType,
    query: Dict[str, Any],
) -> Dict[str, Any]:
    """
    便捷函数：强制添加租户过滤

    Args:
        context: 租户上下文
        resource_type: 资源类型
        query: 查询条件

    Returns:
        添加租户过滤后的查询
    """
    engine = get_isolation_engine()
    return engine.enforce_query_filter(context, resource_type, query)

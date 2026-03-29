"""
健康检查测试
============

验证健康检查端点
"""

import pytest
from nova_executor.health.checker import HealthChecker, ComponentHealth, HealthStatus


class TestHealthChecker:
    """健康检查器测试"""

    @pytest.mark.asyncio
    async def test_check_liveness(self):
        """验证存活检查"""
        checker = HealthChecker()
        result = await checker.check_liveness()
        assert result["status"] == "alive"
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_check_readiness(self):
        """验证就绪检查"""
        checker = HealthChecker()
        result = await checker.check_readiness()
        assert "status" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_check_redis_healthy(self):
        """验证 Redis 检查（健康）"""
        checker = HealthChecker()
        result = await checker.check_redis()
        assert result.name == "redis"
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.UNHEALTHY]
        assert result.latency_ms is not None

    @pytest.mark.asyncio
    async def test_check_database_healthy(self):
        """验证数据库检查（健康）"""
        checker = HealthChecker()
        result = await checker.check_database()
        assert result.name == "database"
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.UNHEALTHY]
        assert result.latency_ms is not None

    @pytest.mark.asyncio
    async def test_check_all_returns_components(self):
        """验证检查所有返回所有组件"""
        checker = HealthChecker()
        result = await checker.check_all()
        assert "status" in result
        assert "timestamp" in result
        assert "components" in result
        component_names = [c["name"] for c in result["components"]]
        assert "redis" in component_names
        assert "database" in component_names

    @pytest.mark.asyncio
    async def test_check_all_overall_status(self):
        """验证检查所有返回总体状态"""
        checker = HealthChecker()
        result = await checker.check_all()
        assert result["status"] in ["healthy", "unhealthy", "degraded"]

    @pytest.mark.asyncio
    async def test_component_health_dataclass(self):
        """验证 ComponentHealth 数据类"""
        health = ComponentHealth(
            name="test_component",
            status=HealthStatus.HEALTHY,
            message="Test passed",
            latency_ms=10.5
        )
        assert health.name == "test_component"
        assert health.status == HealthStatus.HEALTHY
        assert health.message == "Test passed"
        assert health.latency_ms == 10.5

    @pytest.mark.asyncio
    async def test_health_status_enum(self):
        """验证健康状态枚举"""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.DEGRADED.value == "degraded"

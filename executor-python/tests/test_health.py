"""
健康检查测试
============

验证健康检查端点
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from nova_executor.health.checker import HealthChecker


class TestHealthChecker:
    """健康检查器测试"""

    @pytest.mark.asyncio
    async def test_check_liveness(self):
        """验证存活检查"""
        checker = HealthChecker()
        result = await checker.check_liveness()
        assert result["status"] == "alive"
    @pytest.mark.asyncio
    async def test_check_readiness_healthy(self):
        """验证就绪检查（健康）"""
        checker = HealthChecker()
        with patch.object(checker.redis_client, AsyncMock()):
            with patch.object(checker.db_client, AsyncMock()):
                result = await checker.check_readiness()
                assert result["status"] == "ready"
    @pytest.mark.asyncio
    async def test_check_readiness_unhealthy(self):
        """验证就绪检查（不健康）"""
        checker = HealthChecker()
        with patch.object(checker.redis_client, AsyncMock()) as mock_redis:
            mock_redis.ping = AsyncMock(side_effect=Exception("Connection failed"))
            result = await checker.check_readiness()
            assert result["status"] == "not_ready"
    @pytest.mark.asyncio
    async def test_check_all(self):
        """验证检查所有"""
        checker = HealthChecker()
        result = await checker.check_all()
        assert "status" in result
        assert "checks" in result
    @pytest.mark.asyncio
    async def test_check_all_with_details(self):
        """验证检查所有（包含详细信息）"""
        checker = HealthChecker()
        result = await checker.check_all()
        assert "redis" in result["checks"]
        assert "database" in result["checks"]
        assert "playwright" in result["checks"]

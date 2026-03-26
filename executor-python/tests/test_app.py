"""
FastAPI 应用测试
================

验证 FastAPI 端点
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from nova_executor.app import app
from nova_executor.types import InstanceStatus, NodeName


class TestHealthEndpoints:
    """健康检查端点测试"""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """验证健康检查端点"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
    @pytest.mark.asyncio
    async def test_liveness(self):
        """验证存活检查端点"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health/live")
            assert response.status_code == 200
    @pytest.mark.asyncio
    async def test_readiness(self):
        """验证就绪检查端点"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health/ready")
            assert response.status_code == 200


class TestMetricsEndpoint:
    """指标端点测试"""

    @pytest.mark.asyncio
    async def test_get_metrics(self):
        """验证获取指标端点"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/metrics")
            assert response.status_code == 200


class TestTaskEndpoints:
    """任务端点测试"""

    @pytest.mark.asyncio
    async def test_start_task(self):
        """验证启动任务端点"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/tasks/start",
                json={
                    "instance_id": "test-instance",
                    "tenant_id": "test-tenant",
                    "task_id": "test-task",
                    "target_url": "https://example.com",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["instance_id"] == "test-instance"
            assert data["status"] == "RUNNING"
    @pytest.mark.asyncio
    async def test_get_task_status_not_found(self):
        """验证获取不存在任务状态"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/tasks/nonexistent/status")
            assert response.status_code == 404
    @pytest.mark.asyncio
    async def test_terminate_task(self):
        """验证终止任务端点"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/v1/tasks/test-instance/terminate")
            assert response.status_code == 200
            data = response.json()
            assert "terminated" in data["message"].lower()


class TestHilEndpoints:
    """HIL 端点测试"""

    @pytest.mark.asyncio
    async def test_list_hil_tickets(self):
        """验证列出 HIL 工单"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/hil/tickets")
            assert response.status_code == 200
            data = response.json()
            assert "tickets" in data
    @pytest.mark.asyncio
    async def test_get_hil_ticket_not_found(self):
        """验证获取不存在工单"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/hil/tickets/nonexistent")
            assert response.status_code == 404
    @pytest.mark.asyncio
    async def test_hil_decision_invalid(self):
        """验证无效 HIL 决策"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/hil/decide",
                json={
                    "ticket_id": "nonexistent",
                    "decision": "INVALID",
                },
            )
            assert response.status_code == 422


class TestValidation:
    """输入验证测试"""

    def test_start_task_validation(self):
        """验证启动任务输入验证"""
        from nova_executor.app import StartTaskRequest
        with pytest.raises(ValueError):
            StartTaskRequest(
                instance_id="",
                tenant_id="test",
                task_id="test",
                target_url="https://example.com",
            )
    def test_max_steps_validation(self):
        """验证最大步数验证"""
        from nova_executor.app import StartTaskRequest
        request = StartTaskRequest(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
            max_steps=5,
        )
        assert request.max_steps == 5
        with pytest.raises(ValueError):
            StartTaskRequest(
                instance_id="test",
                tenant_id="test",
                task_id="test",
                target_url="https://example.com",
                max_steps=0,
            )
    def test_hil_decision_validation(self):
        """验证 HIL 决策输入验证"""
        from nova_executor.app import HilDecisionRequest
        request = HilDecisionRequest(
            ticket_id="ticket-123",
            decision="APPROVED",
        )
        assert request.decision == "APPROVED"
        with pytest.raises(ValueError):
            HilDecisionRequest(
                ticket_id="ticket-123",
                decision="INVALID",
            )

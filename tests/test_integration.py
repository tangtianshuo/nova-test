import pytest
import httpx
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
import json


BASE_URL = "http://localhost:8002"
TIMEOUT = 30.0


class TestAPIContract:
    """API 契约测试 - 验证 API 端点的契约规范"""

    @pytest.fixture(autouse=True)
    async def setup(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT)
        yield
        await self.client.aclose()

    async def test_task_create_contract(self):
        """测试任务创建 API 契约"""
        payload = {
            "name": "integration-test-task",
            "type": "automated",
            "config": {
                "browser": "chromium",
                "headless": True
            }
        }

        response = await self.client.post("/api/tasks", json=payload)

        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}"

        data = response.json()
        assert "id" in data, "Response must contain 'id' field"
        assert "created_at" in data, "Response must contain 'created_at' field"
        assert data["name"] == payload["name"], "Task name must match"

        return data["id"]

    async def test_task_get_contract(self, task_id: str):
        """测试获取任务 API 契约"""
        response = await self.client.get(f"/api/tasks/{task_id}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        required_fields = ["id", "name", "status", "created_at"]
        for field in required_fields:
            assert field in data, f"Response must contain '{field}' field"

    async def test_task_list_contract(self):
        """测试任务列表 API 契约"""
        response = await self.client.get("/api/tasks", params={"page": 1, "limit": 10})

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "items" in data or isinstance(data, list), "Response must contain 'items' or be a list"
        assert "total" in data, "Response must contain 'total' field"

    async def test_instance_create_contract(self, task_id: str):
        """测试实例创建 API 契约"""
        payload = {
            "task_id": task_id,
            "action": "explore",
            "parameters": {
                "url": "https://example.com"
            }
        }

        response = await self.client.post("/api/instances", json=payload)

        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}"

        data = response.json()
        required_fields = ["id", "task_id", "status"]
        for field in required_fields:
            assert field in data, f"Response must contain '{field}' field"

    async def test_health_endpoint_contract(self):
        """测试健康检查端点契约"""
        response = await self.client.get("/health")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "status" in data, "Response must contain 'status' field"


class TestStateMachine:
    """状态机测试 - 验证任务状态转换"""

    @pytest.fixture(autouse=True)
    async def setup(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT)
        yield
        await self.client.aclose()

    async def test_state_transitions(self):
        """测试任务状态转换"""
        task_payload = {
            "name": "state-machine-test",
            "type": "automated",
            "config": {"browser": "chromium"}
        }

        create_response = await self.client.post("/api/tasks", json=task_payload)
        assert create_response.status_code in [200, 201]

        task_data = create_response.json()
        task_id = task_data["id"]

        initial_status = task_data.get("status", "pending")
        assert initial_status in ["pending", "initialized"], f"Invalid initial status: {initial_status}"

        instance_payload = {
            "task_id": task_id,
            "action": "execute",
            "parameters": {}
        }
        instance_response = await self.client.post("/api/instances", json=instance_payload)
        assert instance_response.status_code in [200, 201]

        instance_data = instance_response.json()
        instance_id = instance_data["id"]

        await asyncio.sleep(2)

        status_response = await self.client.get(f"/api/instances/{instance_id}")
        assert status_response.status_code == 200

        updated_data = status_response.json()
        valid_statuses = ["pending", "running", "completed", "failed", "cancelled"]
        assert updated_data["status"] in valid_statuses, f"Invalid status: {updated_data['status']}"

        return task_id, instance_id

    async def test_state_machine_routing(self):
        """测试状态机路由逻辑"""
        valid_actions = ["init", "explore", "execute", "verify", "check_hil"]

        for action in valid_actions:
            task_payload = {
                "name": f"routing-test-{action}",
                "type": "automated",
                "config": {"browser": "chromium"}
            }

            create_response = await self.client.post("/api/tasks", json=task_payload)
            assert create_response.status_code in [200, 201]

            task_data = create_response.json()
            task_id = task_data["id"]

            instance_payload = {
                "task_id": task_id,
                "action": action,
                "parameters": {"url": "https://example.com"}
            }

            instance_response = await self.client.post("/api/instances", json=instance_payload)
            assert instance_response.status_code in [200, 201], f"Action '{action}' should be routable"

    async def test_concurrent_state_transitions(self):
        """测试并发状态转换"""
        task_payload = {
            "name": "concurrent-test",
            "type": "automated",
            "config": {"browser": "chromium"}
        }

        create_response = await self.client.post("/api/tasks", json=task_payload)
        assert create_response.status_code in [200, 201]

        task_data = create_response.json()
        task_id = task_data["id"]

        async def create_instance(action: str):
            payload = {
                "task_id": task_id,
                "action": action,
                "parameters": {}
            }
            return await self.client.post("/api/instances", json=payload)

        results = await asyncio.gather(
            create_instance("explore"),
            create_instance("execute"),
            return_exceptions=True
        )

        success_count = sum(1 for r in results if not isinstance(r, Exception) and r.status_code in [200, 201])
        assert success_count >= 1, "At least one concurrent request should succeed"


class TestEndToEnd:
    """端到端测试 - 验证完整的工作流程"""

    @pytest.fixture(autouse=True)
    async def setup(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT)
        yield
        await self.client.aclose()

    async def test_complete_workflow(self):
        """测试完整的任务执行工作流"""
        task_payload = {
            "name": "e2e-workflow-test",
            "type": "automated",
            "config": {
                "browser": "chromium",
                "headless": True,
                "viewport": {"width": 1920, "height": 1080}
            }
        }

        create_response = await self.client.post("/api/tasks", json=task_payload)
        assert create_response.status_code in [200, 201]
        task_data = create_response.json()
        task_id = task_data["id"]

        get_response = await self.client.get(f"/api/tasks/{task_id}")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == task_id

        instance_payload = {
            "task_id": task_id,
            "action": "explore",
            "parameters": {
                "url": "https://example.com",
                "timeout": 30000
            }
        }

        instance_response = await self.client.post("/api/instances", json=instance_payload)
        assert instance_response.status_code in [200, 201]
        instance_data = instance_response.json()
        instance_id = instance_data["id"]

        max_retries = 30
        for _ in range(max_retries):
            await asyncio.sleep(2)
            status_response = await self.client.get(f"/api/instances/{instance_id}")
            assert status_response.status_code == 200

            status_data = status_response.json()
            status = status_data["status"]

            if status in ["completed", "failed", "cancelled"]:
                break
        else:
            pytest.fail("Instance did not reach terminal state within timeout")

        assert status in ["completed", "failed"], f"Unexpected terminal status: {status}"

        return task_id, instance_id

    async def test_error_recovery_workflow(self):
        """测试错误恢复工作流"""
        task_payload = {
            "name": "error-recovery-test",
            "type": "automated",
            "config": {"browser": "chromium"}
        }

        create_response = await self.client.post("/api/tasks", json=task_payload)
        assert create_response.status_code in [200, 201]
        task_data = create_response.json()
        task_id = task_data["id"]

        invalid_instance_payload = {
            "task_id": task_id,
            "action": "execute",
            "parameters": {
                "script": "invalid_script_that_does_not_exist"
            }
        }

        instance_response = await self.client.post("/api/instances", json=invalid_instance_payload)
        instance_data = instance_response.json()
        instance_id = instance_data["id"]

        max_retries = 10
        for _ in range(max_retries):
            await asyncio.sleep(2)
            status_response = await self.client.get(f"/api/instances/{instance_id}")
            status_data = status_response.json()

            if status_data["status"] in ["completed", "failed"]:
                assert status_data["status"] == "failed", "Invalid script should result in failed status"
                assert "error" in status_data or "message" in status_data, "Failed instance should have error info"
                break
        else:
            pytest.fail("Instance did not reach terminal state")

        retry_payload = {
            "task_id": task_id,
            "action": "execute",
            "parameters": {
                "script": "valid_script"
            }
        }

        retry_response = await self.client.post("/api/instances", json=retry_payload)
        assert retry_response.status_code in [200, 201]

        return task_id

    async def test_multi_tenant_isolation(self):
        """测试多租户隔离"""
        tenant1_task = {
            "name": "tenant1-task",
            "type": "automated",
            "config": {"browser": "chromium"},
            "tenant_id": "tenant-1"
        }

        tenant2_task = {
            "name": "tenant2-task",
            "type": "automated",
            "config": {"browser": "chromium"},
            "tenant_id": "tenant-2"
        }

        response1 = await self.client.post("/api/tasks", json=tenant1_task)
        response2 = await self.client.post("/api/tasks", json=tenant2_task)

        assert response1.status_code in [200, 201]
        assert response2.status_code in [200, 201]

        task1_data = response1.json()
        task2_data = response2.json()

        assert task1_data["tenant_id"] == "tenant-1"
        assert task2_data["tenant_id"] == "tenant-2"
        assert task1_data["id"] != task2_data["id"]

        tenant1_header = {"X-Tenant-ID": "tenant-1"}
        list1_response = await self.client.get("/api/tasks", headers=tenant1_header)
        assert list1_response.status_code == 200

        list1_data = list1_response.json()
        if "items" in list1_data:
            for task in list1_data["items"]:
                assert task["tenant_id"] == "tenant-1", "Tenant 1 should only see their tasks"

    async def test_metrics_collection(self):
        """测试指标收集"""
        task_payload = {
            "name": "metrics-test",
            "type": "automated",
            "config": {"browser": "chromium"}
        }

        create_response = await self.client.post("/api/tasks", json=task_payload)
        assert create_response.status_code in [200, 201]
        task_data = create_response.json()
        task_id = task_data["id"]

        instance_payload = {
            "task_id": task_id,
            "action": "execute",
            "parameters": {}
        }

        instance_response = await self.client.post("/api/instances", json=instance_payload)
        instance_data = instance_response.json()
        instance_id = instance_data["id"]

        await asyncio.sleep(5)

        metrics_response = await self.client.get(f"/api/instances/{instance_id}/metrics")
        assert metrics_response.status_code == 200

        metrics_data = metrics_response.json()
        assert "cpu" in metrics_data or "memory" in metrics_data or "duration" in metrics_data

    async def test_audit_logging(self):
        """测试审计日志"""
        task_payload = {
            "name": "audit-test",
            "type": "automated",
            "config": {"browser": "chromium"}
        }

        create_response = await self.client.post("/api/tasks", json=task_payload)
        assert create_response.status_code in [200, 201]
        task_data = create_response.json()
        task_id = task_data["id"]

        audit_response = await self.client.get(f"/api/tasks/{task_id}/audit")
        assert audit_response.status_code == 200

        audit_data = audit_response.json()
        assert isinstance(audit_data, list), "Audit log should be a list"
        if len(audit_data) > 0:
            for entry in audit_data:
                assert "timestamp" in entry or "event" in entry, "Audit entry should have timestamp or event"


class TestSecurityIntegration:
    """安全集成测试"""

    @pytest.fixture(autouse=True)
    async def setup(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT)
        yield
        await self.client.aclose()

    async def test_tenant_isolation_security(self):
        """测试租户隔离安全性"""
        sensitive_task = {
            "name": "sensitive-data-task",
            "type": "automated",
            "config": {"browser": "chromium"},
            "tenant_id": "tenant-sensitive"
        }

        response = await self.client.post("/api/tasks", json=sensitive_task)
        assert response.status_code in [200, 201]
        task_data = response.json()
        task_id = task_data["id"]

        wrong_tenant_header = {"X-Tenant-ID": "tenant-attacker"}
        access_response = await self.client.get(f"/api/tasks/{task_id}", headers=wrong_tenant_header)

        assert access_response.status_code == 403 or access_response.status_code == 404, \
            "Cross-tenant access should be denied"

    async def test_input_sanitization(self):
        """测试输入清理"""
        malicious_payload = {
            "name": "<script>alert('xss')</script>",
            "type": "automated",
            "config": {"browser": "chromium"}
        }

        response = await self.client.post("/api/tasks", json=malicious_payload)
        response_data = response.json()

        if response.status_code in [200, 201]:
            assert "<script>" not in response_data.get("name", ""), \
                "XSS payload should be sanitized"


class TestPerformanceIntegration:
    """性能集成测试"""

    @pytest.fixture(autouse=True)
    async def setup(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT)
        yield
        await self.client.aclose()

    async def test_concurrent_requests(self):
        """测试并发请求性能"""

        async def create_task(index: int):
            payload = {
                "name": f"perf-test-{index}",
                "type": "automated",
                "config": {"browser": "chromium"}
            }
            return await self.client.post("/api/tasks", json=payload)

        results = await asyncio.gather(*[create_task(i) for i in range(10)], return_exceptions=True)

        success_count = sum(
            1 for r in results
            if not isinstance(r, Exception) and r.status_code in [200, 201]
        )

        assert success_count >= 8, f"Expected at least 8 successful requests, got {success_count}"

    async def test_response_time(self):
        """测试响应时间"""
        import time

        payload = {
            "name": "response-time-test",
            "type": "automated",
            "config": {"browser": "chromium"}
        }

        start_time = time.time()
        response = await self.client.post("/api/tasks", json=payload)
        elapsed = time.time() - start_time

        assert response.status_code in [200, 201]
        assert elapsed < 5.0, f"Response time should be under 5 seconds, got {elapsed:.2f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

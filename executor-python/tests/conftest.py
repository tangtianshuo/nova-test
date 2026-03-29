"""
测试配置
=====
提供测试 fixtures 和共享配置
"""

import os
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from nova_executor.types import (
    ExecutionState,
    InstanceStatus,
    NodeName,
    ActionType,
    PlannedAction,
    HilTriggerReason,
)
from nova_executor.config import Settings, get_settings
from nova_executor.hil.ticket_service import (
    HilTicketService,
    HilTicketStatus,
    HilTicketDecision,
    HilTicket,
)
from nova_executor.hil.checkpoint_service import (
    WorkerCheckpointService,
    WorkerCheckpoint,
    CheckpointStatus,
)


@pytest.fixture
def event_loop():
    """创建事件循环"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """Mock 配置"""
    with patch.dict(os.environ, {
        "REDIS_URL": "redis://localhost:6379",
        "DATABASE_URL": "postgresql://localhost:5432/nova_test",
        "FARA_API_URL": "http://localhost:8001/v1/chat/completions",
        "HIL_CONFIDENCE_THRESHOLD": "0.7",
        "MAX_STEPS": "10",
        "BROWSER_HEADLESS": "true",
    }):
        settings = Settings()
        yield settings


@pytest.fixture
def sample_execution_state() -> ExecutionState:
    """创建示例执行状态"""
    return ExecutionState(
        instance_id="test-instance-001",
        tenant_id="test-tenant-001",
        task_id="test-task-001",
        target_url="https://example.com",
        current_node=NodeName.INIT,
        step_count=0,
        max_steps=10,
    )


@pytest.fixture
def sample_planned_action() -> PlannedAction:
    """创建示例计划动作"""
    return PlannedAction(
        action_type=ActionType.CLICK,
        selector="#submit-button",
        confidence=0.9,
        thought="Click the submit button to proceed",
    )


@pytest.fixture
def sample_hil_ticket() -> HilTicket:
    """创建示例 HIL 工单"""
    return HilTicket(
        id="ticket-001",
        instance_id="test-instance-001",
        tenant_id="test-tenant-001",
        step_no=1,
        reason="Low confidence: 0.5",
        risk_level="MEDIUM",
        status=HilTicketStatus.WAITING,
        planned_action={
            "action_type": "click",
            "selector": "#unknown-btn",
            "confidence": 0.5,
        },
        created_at=datetime.now(),
    )


@pytest.fixture
def hil_ticket_service():
    """创建 HIL 工单服务实例"""
    return HilTicketService()


@pytest.fixture
def worker_checkpoint_service() -> WorkerCheckpointService:
    """创建 Worker 检查点服务实例"""
    return WorkerCheckpointService()


@pytest.fixture
def sample_worker_checkpoint() -> WorkerCheckpoint:
    """创建示例 Worker 检查点"""
    return WorkerCheckpoint(
        id="checkpoint-001",
        instance_id="test-instance-001",
        current_node="check_hil",
        step_count=3,
        execution_state={
            "instance_id": "test-instance-001",
            "tenant_id": "test-tenant-001",
            "task_id": "test-task-001",
            "current_node": "check_hil",
            "step_count": 3,
        },
        planned_action={
            "action_type": "click",
            "selector": "#submit",
            "confidence": 0.5,
        },
        worker_id="worker-001",
        ticket_id="ticket-001",
        hil_triggered=True,
        interrupted_reason="HIL_TIMEOUT",
        status=CheckpointStatus.INTERRUPTED,
    )


@pytest.fixture
def mock_sandbox_manager():
    """Mock 沙箱管理器"""
    manager = MagicMock()
    manager.create = AsyncMock(return_value=MagicMock())
    manager.get_sandbox = MagicMock(return_value=MagicMock())
    manager.destroy = AsyncMock(return_value=True)
    manager.destroy_all = AsyncMock()
    manager.close = AsyncMock()
    return manager


@pytest.fixture
def mock_playwright_page():
    """Mock Playwright 页面"""
    page = AsyncMock()
    page.goto = AsyncMock()
    page.click = AsyncMock()
    page.fill = AsyncMock()
    page.screenshot = AsyncMock(return_value=b"fake_screenshot_data")
    page.evaluate = AsyncMock()
    page.wait_for_timeout = AsyncMock()
    page.close = AsyncMock()
    return page


@pytest.fixture
def mock_playwright_context():
    """Mock Playwright 上下文"""
    context = AsyncMock()
    context.new_page = AsyncMock()
    context.close = AsyncMock()
    return context


@pytest.fixture
def mock_playwright_browser():
    """Mock Playwright 浏览器"""
    browser = AsyncMock()
    browser.new_context = AsyncMock()
    browser.close = AsyncMock()
    return browser


@pytest.fixture
def mock_redis_client():
    """Mock Redis 客户端"""
    client = AsyncMock()
    client.publish = AsyncMock()
    client.subscribe = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
def temp_dir(tmp_path):
    """临时目录"""
    return tmp_path / "test_output"


@pytest.fixture
def sample_step_record():
    """创建示例步骤记录"""
    from nova_executor.report.types import StepRecord
    return StepRecord(
        step_number=1,
        node_name="init",
        action_type="screenshot",
        timestamp="2024-01-01T10:00:00Z",
    )


@pytest.fixture
def sample_hil_record():
    """创建示例 HIL 记录"""
    from nova_executor.report.types import HilRecord
    return HilRecord(
        ticket_id="ticket-001",
        step_number=1,
        reason="Low confidence",
        risk_level="MEDIUM",
        decision="APPROVED",
        human_feedback="Looks good",
        resolved_at="2024-01-01T10:05:00Z",
    )

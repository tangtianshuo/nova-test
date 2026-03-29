"""
流式推送测试
================

验证 WebSocket 和事件发布
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from nova_executor.streaming.events import (
    EventType,
    ScreenshotUpdateEvent,
    AgentThoughtEvent,
    HilRequestEvent,
    ActionExecutedEvent,
    InstanceStartedEvent,
    InstanceCompletedEvent,
    InstanceFailedEvent,
    parse_event,
    validate_event,
    event_to_dict,
)
from nova_executor.streaming.ws_manager import ConnectionManager
from nova_executor.streaming.publisher import StreamPublisher


class TestEventTypes:
    """事件类型测试"""

    def test_all_event_types_defined(self):
        """验证所有事件类型已定义"""
        assert EventType.SCREENSHOT_UPDATE.value == "SCREENSHOT_UPDATE"
        assert EventType.AGENT_THOUGHT.value == "AGENT_THOUGHT"
        assert EventType.HIL_REQUEST.value == "HIL_REQUEST"
        assert EventType.ACTION_EXECUTED.value == "ACTION_EXECUTED"
        assert EventType.INSTANCE_STARTED.value == "INSTANCE_STARTED"
        assert EventType.INSTANCE_COMPLETED.value == "INSTANCE_COMPLETED"
        assert EventType.INSTANCE_FAILED.value == "INSTANCE_FAILED"


class TestScreenshotUpdateEvent:
    """截图更新事件测试"""

    def test_create_screenshot_event(self):
        """验证创建截图事件"""
        event = ScreenshotUpdateEvent(
            instance_id="test-instance",
            screenshot="base64_image",
            step_number=1,
        )
        assert event.instance_id == "test-instance"
        assert event.screenshot == "base64_image"
        assert event.step_number == 1
        assert event.event_type == EventType.SCREENSHOT_UPDATE

    def test_screenshot_event_to_dict(self):
        """验证截图事件转字典"""
        event = ScreenshotUpdateEvent(
            instance_id="test-instance",
            screenshot="base64_image",
            step_number=1,
        )
        data = event.model_dump()
        assert data["instance_id"] == "test-instance"
        assert data["screenshot"] == "base64_image"
        assert data["event_type"] == "SCREENSHOT_UPDATE"


class TestAgentThoughtEvent:
    """Agent 思维事件测试"""

    def test_create_thought_event(self):
        """验证创建思维事件"""
        event = AgentThoughtEvent(
            instance_id="test-instance",
            thought="I should click the submit button",
            planned_action={"action_type": "click", "selector": "#submit"},
            confidence=0.9,
        )
        assert event.thought == "I should click the submit button"
        assert event.planned_action == {"action_type": "click", "selector": "#submit"}
        assert event.confidence == 0.9

    def test_create_thought_event_with_high_confidence(self):
        """验证高置信度思维事件"""
        event = AgentThoughtEvent(
            instance_id="test-instance",
            thought="I should click the submit button",
            planned_action={"action_type": "click", "selector": "#submit", "confidence": 0.9},
            confidence=0.9,
        )
        assert event.event_type == EventType.AGENT_THOUGHT

    def test_create_thought_event_with_no_planned_action(self):
        """验证无计划动作的思维事件"""
        event = AgentThoughtEvent(
            instance_id="test-instance",
            thought="Page loaded successfully",
            planned_action=None,
        )
        assert event.planned_action is None
        assert event.confidence is None

    def test_create_thought_event_with_error(self):
        """验证带错误的思维事件"""
        event = AgentThoughtEvent(
            instance_id="test-instance",
            thought="Failed to analyze page",
            confidence=0.1,
        )
        assert event.thought == "Failed to analyze page"
        assert event.confidence == 0.1


class TestActionExecutedEvent:
    """动作执行事件测试"""

    def test_create_action_event_success(self):
        """验证创建成功动作事件"""
        event = ActionExecutedEvent(
            instance_id="test-instance",
            step_number=1,
            action={"action_type": "click", "selector": "#submit"},
            success=True,
        )
        assert event.action["action_type"] == "click"
        assert event.action["selector"] == "#submit"
        assert event.success is True

    def test_create_action_event_failure(self):
        """验证创建失败动作事件"""
        event = ActionExecutedEvent(
            instance_id="test-instance",
            step_number=1,
            action={"action_type": "click", "selector": "#nonexistent"},
            success=False,
            error="Element not found",
        )
        assert event.success is False
        assert event.error == "Element not found"


class TestWSConnectionManager:
    """WebSocket 连接管理器测试"""

    def test_add_connection(self):
        """验证添加连接"""
        manager = ConnectionManager()
        mock_ws = AsyncMock()
        # 模拟 WebSocket.accept()
        mock_ws.accept = AsyncMock()

        # 使用内部方法
        import asyncio
        asyncio.get_event_loop().run_until_complete(
            manager.connect(mock_ws, "tenant-1", "user-1")
        )
        assert manager.get_connection_count() == 1

    def test_remove_connection(self):
        """验证移除连接"""
        manager = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()

        import asyncio
        asyncio.get_event_loop().run_until_complete(
            manager.connect(mock_ws, "tenant-1", "user-1")
        )
        assert manager.get_connection_count() == 1

        asyncio.get_event_loop().run_until_complete(
            manager.disconnect("tenant-1:user-1:123")
        )
        assert manager.get_connection_count() == 0

    def test_broadcast_to_instance(self):
        """验证广播到实例"""
        manager = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_text = AsyncMock()

        import asyncio
        asyncio.get_event_loop().run_until_complete(
            manager.connect(mock_ws, "tenant-1", "user-1")
        )
        asyncio.get_event_loop().run_until_complete(
            manager.subscribe("tenant-1:user-1:123", "instance-1")
        )

        # 广播消息
        asyncio.get_event_loop().run_until_complete(
            manager.broadcast("instance-1", '{"type": "test"}')
        )
        mock_ws.send_text.assert_called_once()

    def test_broadcast_to_empty_instance(self):
        """验证广播到空实例"""
        manager = ConnectionManager()
        # 广播到不存在的实例应该静默失败
        import asyncio
        asyncio.get_event_loop().run_until_complete(
            manager.broadcast("nonexistent", '{"type": "test"}')
        )
        # 没有连接应该不会抛出异常


class TestStreamPublisher:
    """流发布器测试"""

    @pytest.mark.asyncio
    async def test_publish_screenshot(self):
        """验证发布截图"""
        publisher = StreamPublisher()

        # 模拟 Redis 客户端
        mock_redis = AsyncMock()
        mock_redis.publish = AsyncMock(return_value=1)

        with patch.object(publisher, "redis_client", mock_redis):
            await publisher.publish_screenshot(
                instance_id="test-instance",
                screenshot="base64_data",
                step_number=1,
            )
            mock_redis.publish.assert_called()

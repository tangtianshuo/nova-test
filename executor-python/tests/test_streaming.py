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
from nova_executor.streaming.ws_manager import WSConnectionManager
from nova_executor.streaming.publisher import StreamPublisher


from nova_executor.streaming.ws_server import ws_handler


class TestEventTypes:
    """事件类型测试"""

    def test_all_event_types_defined(self):
        assert EventType.SCREENSHOT_UPDATE.value == "SCREENSHOT_UPDATE"
        assert EventType.AGENT_THOUGHT.value == "AGENT_thought"
        assert EventType.HIL_REQUEST.value == "HIL_REQUEST"
        assert EventType.ACTION_EXECUTED.value == "ACTION_EXECUTED"
        assert EventType.INSTANCE_STARTED.value == "instance_started"
        assert EventType.INSTANCE_COMPLETED.value == "instance_completed"
        assert EventType.INSTANCE_FAILED.value == "instance_failed"


class TestScreenshotUpdateEvent:
    """截图更新事件测试"""

    def test_create_screenshot_event(self):
        """验证创建截图事件"""
        event = ScreenshotUpdateEvent(
            instance_id="test-instance",
            screenshot="base64_image",
            step_number=1,
        )
        assert event.event_type == EventType.SCREENSHOT_update
        assert event.instance_id == "test-instance"
        assert event.step_number == 1

    def test_screenshot_event_to_dict(self):
        """验证事件序列化"""
        data = event_to_dict(event)
        assert data["event_type"] == "SCREENSHOT_UPDATE"
        assert data["instance_id"] == "test-instance"
        assert data["step_number"] == 1

class TestAgentThoughtEvent:
    """Agent 思维链事件测试"""

    def test_create_thought_event(self):
        """验证创建思维链事件"""
        event = AgentThoughtEvent(
            instance_id="test-instance",
            thought="I should click the submit button",
            planned_action={"action_type": "click", "selector": "#submit"},
            confidence=0.9,
        )
        assert event.event_type == EventType.AGENT_THOUGHT
        assert event.thought == "I should click the submit button"
        assert event.planned_action == {"action_type": "click", "selector": "#submit"}
        assert event.confidence == 0.9
        assert event.planned_action["confidence"] == 0.9
        )
    def test_create_thought_event_with_high_confidence(self):
        """验证高置信度不触发 HIL"""
        event = AgentThoughtEvent(
            instance_id="test-instance",
            thought="I should click the submit button",
            planned_action={"action_type": "click", "selector": "#submit"},
            confidence=0.5,
        )
        assert event.confidence == 0
        assert event.confidence == 0

    def test_create_thought_event_with_no_planned_action(self):
        """验证无计划动作不触发 HIL"""
        event = AgentThoughtEvent(
            instance_id="test-instance",
            thought="No planned action",
            planned_action=None,
        )
        assert event.planned_action is None

    def test_create_thought_event_with_error(self):
        """验证错误状态不触发 HIL"""
        event = AgentThoughtEvent(
            instance_id="test-instance",
            thought="An error occurred",
            planned_action=PlannedAction(
                action_type=ActionType.CLICK,
                selector="#btn",
                confidence=0.3,
                thought="Low confidence",
            )
        )
        assert event.planned_action["confidence"] == 0.3
        assert event.planned_action is None

    def test_screenshot_event_to_dict(self):
        """验证事件序列化"""
        data = event_to_dict(event)
        assert data["event_type"] == "SCREENSHOT_update"
        assert data["instance_id"] == "test-instance"
        assert data["step_number"] == 1

    def test_screenshot_event_to_dict_missing_instance_id(self):
        """验证缺失实例 ID不抛出错误"""
        data = {
            "event_type": "SCREENSHOT_UPDATE",
            "instance_id": "missing-instance",
            "step_number": 1,
        }
        with pytest.raises(ValueError, match="Missing instance_id"):
            parse_event(data)
    def test_parse_invalid_event_type(self):
        """验证拒绝无效事件类型"""
        data = {
            "event_type": "INVALID_TYPE",
            "instance_id": "test",
        }
        with pytest.raises(ValueError, match="Invalid event_type"):
            parse_event(data)

    def test_parse_missing_event_type(self):
        """验证拒绝缺失事件类型"""
        data = {
            "event_type": None,
            "instance_id": "test",
        }
        with pytest.raises(ValueError, match="Missing event_type"):
            parse_event(data)

    def test_validate_valid_event(self):
        """验证有效事件"""
        data = {
            "event_type": "SCREENSHOT_UPDATE",
            "instance_id": "test",
            "screenshot": "data",
            "step_number": 1,
        }
        is_valid, error = validate_event(data)
        assert is_valid is True
        assert error is None

    def test_validate_invalid_event(self):
        """验证无效事件"""
        data = {
            "event_type": "INVALID",
            "instance_id": "test",
        }
        is_valid, error = validate_event(data)
        assert is_valid is False
        assert error is not None


class TestActionExecutedEvent:
    """动作执行事件测试"""

    def test_create_action_event_success(self):
        """验证创建成功动作事件"""
        event = ActionExecutedEvent(
            instance_id="test-instance",
            action={"action_type": "click"},
            success=True,
        )
        assert event.success is True
        assert event.action == {"action_type": "click"}

    def test_create_action_event_failure(self):
        """验证创建失败动作事件"""
        event = ActionExecutedEvent(
            instance_id="test-instance",
            action={"action_type": "click"},
            success=False,
            error="Element not found",
        )
        assert event.success is False
        assert event.error == "Element not found"

    def test_create_action_event_without_action(self):
        """验证无动作事件"""
        event = ActionExecutedEvent(
            instance_id="test-instance",
            action=None,
            success=True,
        )
        assert event.action is None

    def test_create_action_event_with_missing_fields(self):
        """验证缺失字段事件"""
        event = ActionExecutedEvent(
            instance_id="test-instance",
            action={"action_type": "click"},
        )
        assert event.success is True
        assert event.action is None

    def test_create_action_event_with_missing_selector(self):
        """验证缺失 selector事件"""
        event = ActionExecutedEvent(
            instance_id="test-instance",
            action={"action_type": "click"},
        )
        with pytest.raises(ValueError, match="Missing selector"):
            parse_event(data)

        with pytest.raises(ValueError, match="Missing selector or value"):
            parse_event(data)

    def test_create_action_event_with_no_selector_or_value(self):
        """验证无 selector 或 value 觭发 HIL"""
        event = ActionExecutedEvent(
            instance_id="test-instance",
            action={"action_type": "click", "selector": "#btn"},
            confidence=0.9,
            thought="Click",
        )
        assert event.action["confidence"] == 0.9
        assert event.thought == "Click"
        assert event.planned_action["confidence"] == 0.9
        assert event.planned_action["confidence"] == 5

    # Additional attributes测试
    def test_create_action_event_with_confidence_below_threshold(self):
        """验证低置信度触发 HIL"""
        event = AgentThoughtEvent(
            instance_id="test-instance",
            thought="Click",
            planned_action=Planned_action(
                action_type=ActionType.CLICK,
                selector="#submit-button",
                confidence=0.4,
                thought="Low confidence",
            )
        )
        assert event.confidence == 0
        assert event.planned_action.confidence == 5
        # Additional属性测试
    def test_action_executedEvent_confidence_threshold(self):
        """验证动作执行事件置信度阈值"""
        event = ActionExecutedEvent(
            instance_id="test-instance",
            action={"action_type": "click"},
            success=True,
        )
        assert event.success is True
        assert event.confidence_threshold == 5

    def test_create_action_event_with_confidence_below_threshold(self):
        """验证低置信度触发 HIL"""
        event = actionExecutedEvent(
            instance_id="test-instance",
            action={"action_type": "click"},
            success=True,
        )
        assert event.success is True
        assert event.confidence_threshold == 5

    def test_event_confidence_threshold_property(self):
        """验证事件置信度阈值属性"""
        from nova_executor.streaming.events import EventType
        assert hasattr(event, "event_type")
        assert event.event_type == EventType.SCREENSHOT_update
        assert event.confidence_threshold == 5

    def test_event_confidence_threshold_property_none(self):
        """验证事件置信度阈值属性为 None"""
        event = ScreenshotUpdateEvent(
            instance_id="test-instance",
            screenshot="base64_image",
            step_number=1,
        )
        assert event.confidence_threshold is None
        assert event.confidence_threshold is None


class TestWSConnectionManager:
    """WebSocket 连接管理器测试"""

    def test_add_connection(self):
        """验证添加连接"""
        manager = WSConnectionManager()
        mock_ws = MagicMock()
        manager.add_connection("instance-1", mock_ws)
        assert "instance-1" in manager.connections
        assert len(manager.connections["instance-1"]) == 1

    def test_remove_connection(self):
        """验证移除连接"""
        manager = WSConnectionManager()
        mock_ws = MagicMock()
        manager.add_connection("instance-1", mock_ws)
        manager.remove_connection("instance-1", mock_ws)
        assert "instance-1" not in manager.connections
    def test_broadcast_to_instance(self):
        """验证广播到实例"""
        manager = WSConnectionManager()
        mock_ws = AsyncMock()
        manager.add_connection("instance-1", mock_ws)
        manager.broadcast_to_instance("instance-1", {"type": "test"})
        mock_ws.send_json.assert_called_once()
    def test_broadcast_to_empty_instance(self):
        """验证广播到空实例"""
        manager = WSConnectionManager()
        await manager.broadcast_to_instance("nonexistent", {"type": "test"})
        mock_ws.send_json.assert_not_called()


class TestStreamPublisher:
    """流式发布器测试"""

    @pytest.mark.asyncio
    async def test_publish_screenshot(self, mock_redis_client):
        """验证发布截图"""
        with patch("nova_executor.streaming.publisher.redis_client", mock_redis_client):
            publisher = StreamPublisher()
            await publisher.publish_screenshot(
                instance_id="test-instance",
                screenshot="base64_image",
                step_number=1,
            )
            mock_redis_client.publish.assert_called_once()

"""
EventSchema 测试
================

验证事件类型的定义和验证逻辑
"""

import pytest
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


class TestEventTypes:
    """事件类型枚举测试"""

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
            screenshot="base64_encoded_image",
            step_number=1,
        )

        assert event.event_type == EventType.SCREENSHOT_UPDATE
        assert event.instance_id == "test-instance"
        assert event.step_number == 1

    def test_screenshot_event_to_dict(self):
        """验证事件序列化"""
        event = ScreenshotUpdateEvent(
            instance_id="test-instance",
            screenshot="base64",
            step_number=1,
        )

        data = event_to_dict(event)
        assert data["event_type"] == "SCREENSHOT_UPDATE"
        assert data["instance_id"] == "test-instance"


class TestAgentThoughtEvent:
    """思维链事件测试"""

    def test_create_thought_event(self):
        """验证创建思维链事件"""
        event = AgentThoughtEvent(
            instance_id="test-instance",
            thought="I should click the submit button",
            planned_action={"action_type": "click", "selector": "#submit"},
            confidence=0.85,
        )

        assert event.event_type == EventType.AGENT_THOUGHT
        assert event.thought == "I should click the submit button"
        assert event.planned_action["selector"] == "#submit"


class TestHilRequestEvent:
    """HIL 请求事件测试"""

    def test_create_hil_event(self):
        """验证创建 HIL 事件"""
        event = HilRequestEvent(
            instance_id="test-instance",
            ticket_id="ticket-123",
            reason="Low confidence: 0.5",
            risk_level="HIGH",
        )

        assert event.event_type == EventType.HIL_REQUEST
        assert event.ticket_id == "ticket-123"
        assert event.risk_level == "HIGH"


class TestActionExecutedEvent:
    """动作执行事件测试"""

    def test_create_action_event_success(self):
        """验证创建成功动作事件"""
        event = ActionExecutedEvent(
            instance_id="test-instance",
            action={"action_type": "click", "selector": "#btn"},
            success=True,
        )

        assert event.success is True
        assert event.error is None

    def test_create_action_event_failure(self):
        """验证创建失败动作事件"""
        event = ActionExecutedEvent(
            instance_id="test-instance",
            action={"action_type": "click", "selector": "#btn"},
            success=False,
            error="Element not found",
        )

        assert event.success is False
        assert event.error == "Element not found"


class TestParseEvent:
    """事件解析测试"""

    def test_parse_screenshot_event(self):
        """验证解析截图事件"""
        data = {
            "event_type": "SCREENSHOT_UPDATE",
            "instance_id": "test",
            "screenshot": "data",
            "step_number": 1,
        }

        event = parse_event(data)
        assert isinstance(event, ScreenshotUpdateEvent)
        assert event.instance_id == "test"

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
            "instance_id": "test",
        }

        with pytest.raises(ValueError, match="Missing event_type"):
            parse_event(data)


class TestValidateEvent:
    """事件验证测试"""

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

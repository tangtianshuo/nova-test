"""
事件类型定义
============

定义推流事件的类型和数据结构
"""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Literal
import json


class EventType(str, Enum):
    """事件类型枚举"""
    SCREENSHOT_UPDATE = "SCREENSHOT_UPDATE"
    AGENT_THOUGHT = "AGENT_THOUGHT"
    HIL_REQUEST = "HIL_REQUEST"
    ACTION_EXECUTED = "ACTION_EXECUTED"
    INSTANCE_STARTED = "INSTANCE_STARTED"
    INSTANCE_COMPLETED = "INSTANCE_COMPLETED"
    INSTANCE_FAILED = "INSTANCE_FAILED"


class BaseEvent(BaseModel):
    """基础事件"""
    event_type: EventType
    instance_id: str
    timestamp: float = Field(default_factory=lambda: __import__("time").time())
    step_count: Optional[int] = None


class ScreenshotUpdateEvent(BaseEvent):
    """截图更新事件"""
    event_type: Literal[EventType.SCREENSHOT_UPDATE] = EventType.SCREENSHOT_UPDATE
    screenshot: str  # base64 encoded
    step_number: int


class AgentThoughtEvent(BaseEvent):
    """Agent 思维链事件"""
    event_type: Literal[EventType.AGENT_THOUGHT] = EventType.AGENT_THOUGHT
    thought: str
    planned_action: Optional[dict] = None
    confidence: Optional[float] = None


class HilRequestEvent(BaseEvent):
    """HIL 请求事件"""
    event_type: Literal[EventType.HIL_REQUEST] = EventType.HIL_REQUEST
    ticket_id: str
    reason: str
    risk_level: str
    screenshot: Optional[str] = None


class ActionExecutedEvent(BaseEvent):
    """动作执行完成事件"""
    event_type: Literal[EventType.ACTION_EXECUTED] = EventType.ACTION_EXECUTED
    action: dict
    success: bool
    error: Optional[str] = None
    screenshot: Optional[str] = None


class InstanceStartedEvent(BaseEvent):
    """实例启动事件"""
    event_type: Literal[EventType.INSTANCE_STARTED] = EventType.INSTANCE_STARTED
    task_id: str
    target_url: str


class InstanceCompletedEvent(BaseEvent):
    """实例完成事件"""
    event_type: Literal[EventType.INSTANCE_COMPLETED] = EventType.INSTANCE_COMPLETED
    reason: str
    step_count: int
    summary: Optional[str] = None


class InstanceFailedEvent(BaseEvent):
    """实例失败事件"""
    event_type: Literal[EventType.INSTANCE_FAILED] = EventType.INSTANCE_FAILED
    error: str
    step_count: int


def parse_event(data: dict) -> BaseEvent:
    """
    解析事件 JSON

    Args:
        data: 事件数据字典

    Returns:
        对应的事件对象

    Raises:
        ValueError: 事件类型无效或数据不完整
    """
    event_type = data.get("event_type")
    if not event_type:
        raise ValueError("Missing event_type")

    try:
        event_enum = EventType(event_type)
    except ValueError:
        raise ValueError(f"Invalid event_type: {event_type}")

    event_classes = {
        EventType.SCREENSHOT_UPDATE: ScreenshotUpdateEvent,
        EventType.AGENT_THOUGHT: AgentThoughtEvent,
        EventType.HIL_REQUEST: HilRequestEvent,
        EventType.ACTION_EXECUTED: ActionExecutedEvent,
        EventType.INSTANCE_STARTED: InstanceStartedEvent,
        EventType.INSTANCE_COMPLETED: InstanceCompletedEvent,
        EventType.INSTANCE_FAILED: InstanceFailedEvent,
    }

    event_class = event_classes.get(event_enum)
    if not event_class:
        raise ValueError(f"Unhandled event_type: {event_type}")

    return event_class(**data)


def validate_event(data: dict) -> tuple[bool, Optional[str]]:
    """
    验证事件数据

    Args:
        data: 事件数据

    Returns:
        (is_valid, error_message)
    """
    try:
        parse_event(data)
        return True, None
    except (ValueError, TypeError) as e:
        return False, str(e)


def event_to_json(event: BaseEvent) -> str:
    """将事件转换为 JSON 字符串"""
    return event.model_dump_json()


def event_to_dict(event: BaseEvent) -> dict:
    """将事件转换为字典"""
    return event.model_dump()

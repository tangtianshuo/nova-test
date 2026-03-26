"""
事件发布服务
============

通过 Redis PubSub 发布事件到 WebSocket

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求
"""

import logging
import json
import asyncio
from typing import Optional, Callable, Awaitable
from dataclasses import dataclass

import redis.asyncio as redis

from nova_executor.streaming.events import (
    EventType,
    BaseEvent,
    ScreenshotUpdateEvent,
    AgentThoughtEvent,
    HilRequestEvent,
    ActionExecutedEvent,
    InstanceStartedEvent,
    InstanceCompletedEvent,
    InstanceFailedEvent,
    event_to_json,
)
from nova_executor.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class EventHandler:
    """事件处理器"""
    callback: Callable[[BaseEvent], Awaitable[None]]
    event_types: set[EventType]


class StreamPublisher:
    """
    事件发布器

    功能：
    1. 通过 Redis PubSub 发布事件
    2. 维护本地事件处理器
    3. 支持事件过滤
    """

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._handlers: list[EventHandler] = []
        self._lock = asyncio.Lock()

    async def connect(self):
        """连接到 Redis"""
        if self.redis_client is None:
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info("[Publisher] 已连接到 Redis")

    async def close(self):
        """关闭连接"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
            logger.info("[Publisher] Redis 连接已关闭")

    async def publish(self, event: BaseEvent):
        """
        发布事件

        Args:
            event: 事件对象
        """
        # 确保已连接
        await self.connect()

        # 序列化事件
        message = event_to_json(event)
        channel = f"{settings.redis_stream_prefix}{event.instance_id}"

        # 发布到 Redis
        await self.redis_client.publish(channel, message)

        logger.debug(f"[Publisher] 发布事件: {event.event_type} -> {channel}")

        # 调用本地处理器
        await self._dispatch(event)

    async def _dispatch(self, event: BaseEvent):
        """分发事件到本地处理器"""
        async with self._lock:
            handlers = self._handlers.copy()

        for handler in handlers:
            if event.event_type in handler.event_types or not handler.event_types:
                try:
                    await handler.callback(event)
                except Exception as e:
                    logger.error(f"[Publisher] 处理器异常: {e}")

    def subscribe(
        self,
        callback: Callable[[BaseEvent], Awaitable[None]],
        event_types: Optional[set[EventType]] = None,
    ):
        """
        订阅事件

        Args:
            callback: 回调函数
            event_types: 要处理的事件类型，None 表示处理所有类型
        """
        handler = EventHandler(
            callback=callback,
            event_types=event_types or set(EventType),
        )
        self._handlers.append(handler)
        logger.info(f"[Publisher] 添加处理器: {event_types}")

    def unsubscribe(self, callback: Callable):
        """取消订阅"""
        self._handlers = [h for h in self._handlers if h.callback != callback]
        logger.info("[Publisher] 移除处理器")

    # ============ 便捷发布方法 ============

    async def publish_screenshot(
        self,
        instance_id: str,
        screenshot: str,
        step_number: int,
    ):
        """发布截图更新"""
        event = ScreenshotUpdateEvent(
            instance_id=instance_id,
            screenshot=screenshot,
            step_number=step_number,
        )
        await self.publish(event)

    async def publish_thought(
        self,
        instance_id: str,
        thought: str,
        planned_action: Optional[dict] = None,
        confidence: Optional[float] = None,
    ):
        """发布思维链"""
        event = AgentThoughtEvent(
            instance_id=instance_id,
            thought=thought,
            planned_action=planned_action,
            confidence=confidence,
        )
        await self.publish(event)

    async def publish_hil_request(
        self,
        instance_id: str,
        ticket_id: str,
        reason: str,
        risk_level: str = "MEDIUM",
        screenshot: Optional[str] = None,
    ):
        """发布 HIL 请求"""
        event = HilRequestEvent(
            instance_id=instance_id,
            ticket_id=ticket_id,
            reason=reason,
            risk_level=risk_level,
            screenshot=screenshot,
        )
        await self.publish(event)

    async def publish_action_executed(
        self,
        instance_id: str,
        action: dict,
        success: bool,
        error: Optional[str] = None,
        screenshot: Optional[str] = None,
    ):
        """发布动作执行完成"""
        event = ActionExecutedEvent(
            instance_id=instance_id,
            action=action,
            success=success,
            error=error,
            screenshot=screenshot,
        )
        await self.publish(event)

    async def publish_instance_started(
        self,
        instance_id: str,
        task_id: str,
        target_url: str,
    ):
        """发布实例启动"""
        event = InstanceStartedEvent(
            instance_id=instance_id,
            task_id=task_id,
            target_url=target_url,
        )
        await self.publish(event)

    async def publish_instance_completed(
        self,
        instance_id: str,
        reason: str,
        step_count: int,
        summary: Optional[str] = None,
    ):
        """发布实例完成"""
        event = InstanceCompletedEvent(
            instance_id=instance_id,
            reason=reason,
            step_count=step_count,
            summary=summary,
        )
        await self.publish(event)

    async def publish_instance_failed(
        self,
        instance_id: str,
        error: str,
        step_count: int,
    ):
        """发布实例失败"""
        event = InstanceFailedEvent(
            instance_id=instance_id,
            error=error,
            step_count=step_count,
        )
        await self.publish(event)


# 全局发布器实例
stream_publisher = StreamPublisher()

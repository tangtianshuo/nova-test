"""
Redis 队列消费者
================

从 Redis 队列消费任务，触发 LangGraph 执行

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求：
- 使用 Redis 队列管理任务分发
"""

import asyncio
import json
import logging
from typing import Optional

import redis.asyncio as redis

from nova_executor.config import get_settings
from nova_executor.types import ExecutionState, NodeName
from nova_executor.graph import ExecutionGraph
from nova_executor.audit import get_audit_logger, AuditEventType, AuditOutcome

logger = logging.getLogger(__name__)
settings = get_settings()
audit_logger = get_audit_logger()


class QueueConsumer:
    """
    Redis 队列消费者

    监听 queue:agent_tasks 队列，消费任务并触发执行
    """

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.graph: Optional[ExecutionGraph] = None
        self.is_running = False

    async def start(self, graph: ExecutionGraph):
        """
        启动消费者

        Args:
            graph: LangGraph 执行图
        """
        logger.info("[Queue] 启动队列消费者...")

        self.graph = graph
        self.redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

        self.is_running = True
        asyncio.create_task(self._consume_loop())

        logger.info("[Queue] 队列消费者已启动")

    async def stop(self):
        """停止消费者"""
        logger.info("[Queue] 停止队列消费者...")

        self.is_running = False

        if self.pubsub:
            await self.pubsub.close()

        if self.redis_client:
            await self.redis_client.close()

        logger.info("[Queue] 队列消费者已停止")

    async def _consume_loop(self):
        """消费循环"""
        while self.is_running:
            try:
                # 从队列获取任务 (阻塞)
                result = await self.redis_client.brpop(
                    settings.redis_queue_key,
                    timeout=5,
                )

                if result:
                    _, message = result
                    await self._process_task(message)

            except Exception as e:
                logger.error(f"[Queue] 消费异常: {e}")
                await asyncio.sleep(1)

    async def _process_task(self, message: str):
        """
        处理任务消息

        Args:
            message: 任务消息 JSON
        """
        try:
            data = json.loads(message)
            logger.info(f"[Queue] 收到任务: {data.get('instance_id')}")

            audit_logger.log_task_event(
                event_type=AuditEventType.TASK_CREATED,
                instance_id=data["instance_id"],
                task_id=data["task_id"],
                tenant_id=data["tenant_id"],
                outcome=AuditOutcome.SUCCESS,
                metadata={
                    "target_url": data.get("target_url"),
                    "max_steps": data.get("max_steps", 10),
                },
            )

            state = ExecutionState(
                instance_id=data["instance_id"],
                tenant_id=data["tenant_id"],
                task_id=data["task_id"],
                target_url=data.get("target_url", "about:blank"),
                current_node=NodeName.INIT,
                step_count=0,
                max_steps=data.get("max_steps", 10),
            )

            config = {
                "configurable": {
                    "thread_id": state.instance_id,
                    "checkpoint_ns": "queue_task",
                }
            }

            await self.graph.execute(state, config)

            audit_logger.log_task_event(
                event_type=AuditEventType.TASK_COMPLETED,
                instance_id=data["instance_id"],
                task_id=data["task_id"],
                tenant_id=data["tenant_id"],
                outcome=AuditOutcome.SUCCESS,
            )

            logger.info(f"[Queue] 任务执行完成: {data['instance_id']}")

        except Exception as e:
            logger.exception(f"[Queue] 处理任务失败: {e}")
            audit_logger.log_task_event(
                event_type=AuditEventType.TASK_FAILED,
                instance_id=data.get("instance_id", "unknown"),
                task_id=data.get("task_id", "unknown"),
                tenant_id=data.get("tenant_id", "unknown"),
                outcome=AuditOutcome.FAILURE,
                error_message=str(e),
            )

    async def publish_stream(
        self,
        instance_id: str,
        event_type: str,
        data: dict,
    ):
        """
        发布执行流事件

        Args:
            instance_id: 实例 ID
            event_type: 事件类型
            data: 事件数据
        """
        if not self.redis_client:
            return

        channel = f"{settings.redis_stream_prefix}{instance_id}"
        message = json.dumps({
            "type": event_type,
            "instance_id": instance_id,
            "data": data,
        })

        await self.redis_client.publish(channel, message)

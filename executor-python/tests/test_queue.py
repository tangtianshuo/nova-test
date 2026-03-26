"""
队列测试
============

验证 Redis 队列消费者
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from nova_executor.queue import QueueConsumer
from nova_executor.types import ExecutionState, NodeName
from nova_executor.graph import ExecutionGraph


class TestQueueConsumer:
    """队列消费者测试"""

    def test_create_consumer(self):
        """验证创建消费者"""
        consumer = QueueConsumer()
        assert consumer is not None
    @pytest.mark.asyncio
    async def test_start_consumer(self, mock_redis_client):
        """验证启动消费者"""
        with patch("nova_executor.queue.redis_client", return_value=mock_redis_client):
            consumer = QueueConsumer()
            mock_graph = MagicMock(spec=ExecutionGraph)
            await consumer.start(mock_graph)
            assert consumer.running is True
    @pytest.mark.asyncio
    async def test_stop_consumer(self):
        """验证停止消费者"""
        consumer = QueueConsumer()
        consumer.running = True
        await consumer.stop()
        assert consumer.running is False
    @pytest.mark.asyncio
    async def test_process_task(self, mock_redis_client):
        """验证处理任务"""
        mock_graph = MagicMock(spec=ExecutionGraph)
        mock_graph.execute = AsyncMock()
        with patch("nova_executor.queue.redis_client", return_value=mock_redis_client):
            consumer = QueueConsumer()
            task_data = {
                "instance_id": "test-instance",
                "tenant_id": "test-tenant",
                "task_id": "test-task",
                "target_url": "https://example.com",
            }
            await consumer._process_task(mock_graph, task_data)
            mock_graph.execute.assert_called_once()


class TestQueueConsumerProcessTask:
    """队列任务处理测试"""

    @pytest.mark.asyncio
    async def test_process_task_creates_state(self, mock_redis_client):
        """验证处理任务创建状态"""
        mock_graph = MagicMock(spec=ExecutionGraph)
        mock_graph.execute = AsyncMock()
        with patch("nova_executor.queue.redis_client", return_value=mock_redis_client):
            consumer = QueueConsumer()
            task_data = {
                "instance_id": "test-instance",
                "tenant_id": "test-tenant",
                "task_id": "test-task",
                "target_url": "https://example.com",
            }
            await consumer._process_task(mock_graph, task_data)
            call_args = mock_graph.execute.call_args
            assert isinstance(call_args[0][0], ExecutionState)
            state = call_args[0][0]
            assert state.instance_id == "test-instance"
            assert state.tenant_id == "test-tenant"
            assert state.task_id == "test-task"
            assert state.target_url == "https://example.com"

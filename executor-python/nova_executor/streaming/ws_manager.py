"""
WebSocket 连接管理器
===================

管理 WebSocket 客户端连接和订阅
"""

import logging
import asyncio
from typing import Dict, Set, Optional
from dataclasses import dataclass, field
from fastapi import WebSocket

logger = logging.getLogger(__name__)


@dataclass
class Connection:
    """WebSocket 连接"""
    websocket: WebSocket
    tenant_id: str
    user_id: str
    subscriptions: Set[str] = field(default_factory=set)  # 订阅的 instance_id 集合
    is_active: bool = True


class ConnectionManager:
    """
    WebSocket 连接管理器

    功能：
    1. 管理所有 WebSocket 连接
    2. 处理客户端订阅/取消订阅
    3. 向订阅者广播事件
    4. 连接心跳检测
    """

    def __init__(self):
        # instance_id -> Set[Connection]
        self._subscriptions: Dict[str, Set[Connection]] = {}
        # connection_id -> Connection
        self._connections: Dict[str, Connection] = {}
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        tenant_id: str,
        user_id: str,
    ) -> str:
        """
        建立连接

        Args:
            websocket: WebSocket 连接
            tenant_id: 租户 ID
            user_id: 用户 ID

        Returns:
            connection_id
        """
        await websocket.accept()

        connection_id = f"{tenant_id}:{user_id}:{id(websocket)}"
        connection = Connection(
            websocket=websocket,
            tenant_id=tenant_id,
            user_id=user_id,
        )

        async with self._lock:
            self._connections[connection_id] = connection

        logger.info(f"[WS] 连接已建立: {connection_id}")
        return connection_id

    async def disconnect(self, connection_id: str):
        """
        断开连接

        Args:
            connection_id: 连接 ID
        """
        async with self._lock:
            connection = self._connections.pop(connection_id, None)
            if connection:
                # 从所有订阅中移除
                for instance_id in connection.subscriptions:
                    if instance_id in self._subscriptions:
                        self._subscriptions[instance_id].discard(connection)
                connection.is_active = False

        logger.info(f"[WS] 连接已断开: {connection_id}")

    async def subscribe(self, connection_id: str, instance_id: str) -> bool:
        """
        订阅实例

        Args:
            connection_id: 连接 ID
            instance_id: 实例 ID

        Returns:
            是否成功
        """
        async with self._lock:
            connection = self._connections.get(connection_id)
            if not connection or not connection.is_active:
                logger.warning(f"[WS] 连接不存在或已断开: {connection_id}")
                return False

            # 添加订阅
            connection.subscriptions.add(instance_id)

            # 更新全局订阅表
            if instance_id not in self._subscriptions:
                self._subscriptions[instance_id] = set()
            self._subscriptions[instance_id].add(connection)

        logger.info(f"[WS] 订阅: {connection_id} -> {instance_id}")
        return True

    async def unsubscribe(self, connection_id: str, instance_id: str) -> bool:
        """
        取消订阅

        Args:
            connection_id: 连接 ID
            instance_id: 实例 ID

        Returns:
            是否成功
        """
        async with self._lock:
            connection = self._connections.get(connection_id)
            if not connection:
                return False

            connection.subscriptions.discard(instance_id)
            if instance_id in self._subscriptions:
                self._subscriptions[instance_id].discard(connection)

        logger.info(f"[WS] 取消订阅: {connection_id} -> {instance_id}")
        return True

    async def broadcast(self, instance_id: str, message: str):
        """
        向订阅者广播消息

        Args:
            instance_id: 实例 ID
            message: 消息内容 (JSON 字符串)
        """
        subscribers = self._subscriptions.get(instance_id, set())
        if not subscribers:
            return

        disconnected = []

        for connection in subscribers:
            if not connection.is_active:
                disconnected.append(connection)
                continue

            try:
                await connection.websocket.send_text(message)
            except Exception as e:
                logger.error(f"[WS] 发送消息失败: {connection}, {e}")
                disconnected.append(connection)

        # 清理断开的连接
        for connection in disconnected:
            await self.disconnect(f"{connection.tenant_id}:{connection.user_id}:{id(connection.websocket)}")

    async def broadcast_to_all(self, message: str):
        """
        向所有连接广播消息

        Args:
            message: 消息内容
        """
        async with self._lock:
            connections = list(self._connections.values())

        for connection in connections:
            if not connection.is_active:
                continue

            try:
                await connection.websocket.send_text(message)
            except Exception as e:
                logger.error(f"[WS] 广播失败: {connection}, {e}")

    def get_subscription_count(self, instance_id: str) -> int:
        """获取订阅者数量"""
        return len(self._subscriptions.get(instance_id, set()))

    def get_connection_count(self) -> int:
        """获取连接数量"""
        return len(self._connections)

    def is_subscribed(self, connection_id: str, instance_id: str) -> bool:
        """检查是否已订阅"""
        connection = self._connections.get(connection_id)
        if not connection:
            return False
        return instance_id in connection.subscriptions


# 全局连接管理器实例
connection_manager = ConnectionManager()

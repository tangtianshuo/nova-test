"""
WebSocket 服务器
===============

提供 WebSocket 端点用于实时推流

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求
"""

import logging
import json
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from pydantic import BaseModel

from nova_executor.streaming.ws_manager import connection_manager
from nova_executor.streaming.events import EventType

logger = logging.getLogger(__name__)

router = APIRouter(tags=["streaming"])


class SubscribeRequest(BaseModel):
    """订阅请求"""
    instance_id: str


class WSMessage(BaseModel):
    """WebSocket 消息"""
    type: str  # subscribe, unsubscribe, ping
    instance_id: Optional[str] = None
    data: Optional[dict] = None


class WSResponse(BaseModel):
    """WebSocket 响应"""
    success: bool
    message: str
    data: Optional[dict] = None


async def verify_token(token: str) -> dict:
    """
    验证 JWT token

    Args:
        token: JWT token

    Returns:
        用户信息 {"tenant_id": str, "user_id": str}

    Raises:
        HTTPException: token 无效
    """
    # TODO: 实现 JWT 验证
    # 目前使用简化实现
    try:
        # 解析简化 token: tenant_id:user_id
        parts = token.split(":")
        if len(parts) >= 2:
            return {"tenant_id": parts[0], "user_id": parts[1]}
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"[WS] Token 验证失败: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


@router.websocket("/ws/stream")
async def websocket_stream(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    WebSocket 流式推送端点

    连接后，客户端需要发送订阅消息：
    {
        "type": "subscribe",
        "instance_id": "xxx"
    }
    """
    # 验证 token
    try:
        user_info = await verify_token(token)
    except HTTPException:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    tenant_id = user_info["tenant_id"]
    user_id = user_info["user_id"]

    # 建立连接
    connection_id = await connection_manager.connect(websocket, tenant_id, user_id)

    try:
        # 发送连接成功消息
        await websocket.send_json({
            "type": "connected",
            "connection_id": connection_id,
            "message": "Connected to Nova Stream"
        })

        # 消息循环
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            msg_type = message.get("type")
            instance_id = message.get("instance_id")

            if msg_type == "subscribe":
                # 订阅实例
                if instance_id:
                    success = await connection_manager.subscribe(connection_id, instance_id)
                    await websocket.send_json({
                        "type": "subscribed",
                        "instance_id": instance_id,
                        "success": success
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Missing instance_id"
                    })

            elif msg_type == "unsubscribe":
                # 取消订阅
                if instance_id:
                    success = await connection_manager.unsubscribe(connection_id, instance_id)
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "instance_id": instance_id,
                        "success": success
                    })

            elif msg_type == "ping":
                # 心跳
                await websocket.send_json({"type": "pong"})

            elif msg_type == "list":
                # 列出订阅
                connection = connection_manager._connections.get(connection_id)
                if connection:
                    await websocket.send_json({
                        "type": "subscription_list",
                        "subscriptions": list(connection.subscriptions)
                    })

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}"
                })

    except WebSocketDisconnect:
        logger.info(f"[WS] 客户端断开: {connection_id}")
    except Exception as e:
        logger.error(f"[WS] 连接异常: {connection_id}, {e}")
    finally:
        await connection_manager.disconnect(connection_id)


@router.get("/api/v1/streaming/health")
async def streaming_health():
    """流媒体服务健康检查"""
    return {
        "status": "healthy",
        "connections": connection_manager.get_connection_count(),
    }


@router.get("/api/v1/streaming/subscribers/{instance_id}")
async def get_subscribers(instance_id: str):
    """获取实例订阅者数量"""
    count = connection_manager.get_subscription_count(instance_id)
    return {
        "instance_id": instance_id,
        "subscriber_count": count,
    }

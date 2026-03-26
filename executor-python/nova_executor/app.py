"""
Nova Test AaaS 执行引擎 FastAPI 应用
======================================

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求：
- FastAPI 提供高性能的 Agent 触发接口
- LangGraph 负责维护状态机流转

Author: Nova Team
Version: 1.0.0
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from nova_executor.config import get_settings
from nova_executor.types import ExecutionState, InstanceStatus, NodeName
from nova_executor.graph import ExecutionGraph
from nova_executor.queue import QueueConsumer
from nova_executor.sandbox import SandboxManager
from nova_executor.streaming import ws_server, stream_publisher
from nova_executor.streaming.events import EventType
from nova_executor.hil import hil_ticket_service, hil_processor, HilTicketDecision
from nova_executor.health import health_checker
from nova_executor.metrics import metrics

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()

# 全局实例
graph: Optional[ExecutionGraph] = None
queue_consumer: Optional[QueueConsumer] = None
sandbox_manager: Optional[SandboxManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global graph, queue_consumer, sandbox_manager

    logger.info("[App] 启动执行引擎...")

    # 初始化组件
    sandbox_manager = SandboxManager()
    graph = ExecutionGraph()
    queue_consumer = QueueConsumer()

    # 启动队列消费者
    await queue_consumer.start(graph)

    logger.info("[App] 执行引擎已启动")

    yield

    # 清理
    logger.info("[App] 关闭执行引擎...")
    await queue_consumer.stop()
    await sandbox_manager.close()
    logger.info("[App] 执行引擎已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="Nova Test AaaS Executor",
    description="AaaS Execution Engine - FastAPI + LangGraph",
    version="1.0.0",
    lifespan=lifespan,
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ 请求/响应模型 ============

class StartTaskRequest(BaseModel):
    """启动任务请求"""
    instance_id: str
    tenant_id: str
    task_id: str
    target_url: str
    max_steps: int = Field(default=10, ge=1, le=100)


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    instance_id: str
    status: InstanceStatus
    current_node: NodeName
    step_count: int
    hil_triggered: bool
    error: Optional[str] = None


class HilDecisionRequest(BaseModel):
    """HIL 决策请求"""
    ticket_id: str
    decision: str = Field(pattern="^(APPROVED|REJECTED|MODIFIED)$")
    feedback: Optional[str] = None
    modified_action: Optional[dict] = None


# ============ 健康检查 ============

@app.get("/health")
async def health_check():
    """健康检查"""
    return await health_checker.check_all()


@app.get("/health/live")
async def liveness():
    """Liveness 检查"""
    return await health_checker.check_liveness()


@app.get("/health/ready")
async def readiness():
    """Readiness 检查"""
    return await health_checker.check_readiness()


# ============ 指标端点 ============

@app.get("/metrics")
async def get_metrics():
    """Prometheus 指标端点"""
    return metrics.get_metrics()


# ============ 任务管理 ============

@app.post("/api/v1/tasks/start", response_model=TaskStatusResponse)
async def start_task(request: StartTaskRequest, background_tasks: BackgroundTasks):
    """
    启动任务执行

    接收任务配置，启动 LangGraph 状态机执行
    """
    logger.info(f"[API] 启动任务: {request.instance_id}")

    # 创建初始状态
    initial_state = ExecutionState(
        instance_id=request.instance_id,
        tenant_id=request.tenant_id,
        task_id=request.task_id,
        target_url=request.target_url,
        current_node=NodeName.INIT,
        step_count=0,
        max_steps=request.max_steps,
    )

    # 在后台执行
    background_tasks.add_task(graph.execute, initial_state)

    return TaskStatusResponse(
        instance_id=request.instance_id,
        status=InstanceStatus.RUNNING,
        current_node=NodeName.INIT,
        step_count=0,
        hil_triggered=False,
    )


@app.get("/api/v1/tasks/{instance_id}/status", response_model=TaskStatusResponse)
async def get_task_status(instance_id: str):
    """
    获取任务状态

    从 LangGraph checkpointer 获取当前状态
    """
    config = {"configurable": {"thread_id": instance_id}}
    state = graph.get_state(config)

    if not state:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskStatusResponse(
        instance_id=instance_id,
        status=InstanceStatus.RUNNING if not state.error else InstanceStatus.FAILED,
        current_node=state.current_node,
        step_count=state.step_count,
        hil_triggered=state.hil_triggered,
        error=state.error,
    )


@app.post("/api/v1/tasks/{instance_id}/resume")
async def resume_task(instance_id: str, background_tasks: BackgroundTasks):
    """
    恢复任务执行

    从 HIL 暂停状态恢复执行
    """
    logger.info(f"[API] 恢复任务: {instance_id}")

    config = {"configurable": {"thread_id": instance_id}}
    state = graph.get_state(config)

    if not state:
        raise HTTPException(status_code=404, detail="Task not found")

    if not state.hil_triggered:
        raise HTTPException(status_code=400, detail="Task is not in HIL state")

    # 清除 HIL 状态，继续执行
    graph.update_state(config, {"hil_triggered": False})
    state = graph.get_state(config)

    background_tasks.add_task(graph.execute, state)

    return {"message": "Task resumed", "instance_id": instance_id}


@app.post("/api/v1/tasks/{instance_id}/terminate")
async def terminate_task(instance_id: str):
    """
    终止任务执行

    强制终止任务并清理资源
    """
    logger.info(f"[API] 终止任务: {instance_id}")

    # 更新状态
    config = {"configurable": {"thread_id": instance_id}}
    graph.update_state(config, {
        "error": "Terminated by user",
        "hil_triggered": True,
    })

    # 清理沙箱
    await sandbox_manager.destroy(instance_id)

    return {"message": "Task terminated", "instance_id": instance_id}


# ============ HIL 管理 ============

@app.post("/api/v1/hil/decide")
async def hil_decision(request: HilDecisionRequest, background_tasks: BackgroundTasks):
    """
    HIL 决策

    处理人工决策，更新任务状态并恢复执行
    """
    logger.info(f"[API] HIL 决策: {request.ticket_id}, {request.decision}")

    # 获取工单
    ticket = await hil_ticket_service.get_ticket(request.ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # 处理决策
    decision_enum = HilTicketDecision(request.decision)
    result = await hil_processor.process_decision(
        ticket=ticket,
        decision=decision_enum,
        user_id="api-user",  # TODO: 从认证获取
        human_feedback=request.feedback,
        modified_action=request.modified_action,
    )

    # 根据决策结果处理
    if result.terminate_instance:
        # 终止实例
        config = {"configurable": {"thread_id": ticket.instance_id}}
        graph.update_state(config, {
            "error": f"HIL rejected: {request.feedback}",
            "hil_triggered": True,
        })
        await sandbox_manager.destroy(ticket.instance_id)

        return {
            "message": "Instance terminated",
            "ticket_id": request.ticket_id,
            "decision": request.decision,
            "terminate": True,
        }

    else:
        # 恢复执行
        config = {"configurable": {"thread_id": ticket.instance_id}}

        # 更新状态
        updates = {
            "hil_triggered": False,
            "planned_action": (
                result.action_to_execute.model_dump()
                if result.action_to_execute
                else None
            ),
        }
        graph.update_state(config, updates)

        # 发布恢复事件
        await stream_publisher.publish_thought(
            instance_id=ticket.instance_id,
            thought=f"HIL resolved: {decision_enum.value}",
            planned_action=(
                result.action_to_execute.model_dump()
                if result.action_to_execute
                else None
            ),
        )

        return {
            "message": "Execution resumed",
            "ticket_id": request.ticket_id,
            "decision": request.decision,
            "terminate": False,
            "resume_from": result.resume_from_node,
        }


@app.get("/api/v1/hil/tickets")
async def list_hil_tickets(tenant_id: str = None, limit: int = 50):
    """列出 HIL 工单"""
    tickets = await hil_ticket_service.list_waiting_tickets(
        tenant_id=tenant_id,
        limit=limit,
    )
    return {
        "tickets": [
            {
                "id": t.id,
                "instance_id": t.instance_id,
                "step_no": t.step_no,
                "reason": t.reason,
                "risk_level": t.risk_level,
                "status": t.status.value,
                "created_at": t.created_at.isoformat(),
            }
            for t in tickets
        ]
    }


@app.get("/api/v1/hil/tickets/{ticket_id}")
async def get_hil_ticket(ticket_id: str):
    """获取 HIL 工单详情"""
    ticket = await hil_ticket_service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return {
        "id": ticket.id,
        "instance_id": ticket.instance_id,
        "tenant_id": ticket.tenant_id,
        "step_no": ticket.step_no,
        "reason": ticket.reason,
        "risk_level": ticket.risk_level,
        "status": ticket.status.value,
        "planned_action": ticket.planned_action,
        "screenshot_url": ticket.screenshot_url,
        "locked_by": ticket.locked_by,
        "created_at": ticket.created_at.isoformat(),
        "expires_at": ticket.expires_at.isoformat() if ticket.expires_at else None,
    }


# ============ WebSocket 端点 (可选) ============

@app.websocket("/ws/stream/{instance_id}")
async def stream_endpoint(websocket, instance_id: str):
    """
    WebSocket 流式推送

    推送执行过程中的截图和日志
    """
    await websocket.accept()

    try:
        # TODO: 实现 WebSocket 流式推送
        # 订阅 Redis pub/sub 频道
        # pubsub:agent_stream:{instance_id}

        while True:
            data = await websocket.receive_text()
            # 处理客户端消息
            pass

    except Exception as e:
        logger.error(f"[WebSocket] 连接异常: {e}")
    finally:
        await websocket.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "nova_executor.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )

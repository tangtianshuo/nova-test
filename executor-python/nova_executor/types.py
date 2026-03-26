"""
状态机类型定义
定义 LangGraph 状态机的数据结构
"""

from typing import Optional, Literal, Any
from pydantic import BaseModel, Field
from enum import Enum


class InstanceStatus(str, Enum):
    """实例执行状态枚举"""
    PENDING = "PENDING"
    INITIALIZED = "INITIALIZED"
    RUNNING = "RUNNING"
    WAITING_HIL = "WAITING_HIL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TERMINATED = "TERMINATED"


class NodeName(str, Enum):
    """状态机节点名称"""
    INIT = "init"
    EXPLORE = "explore"
    CHECK_HIL = "check_hil"
    EXECUTE = "execute"
    VERIFY = "verify"
    END = "end"


class ActionType(str, Enum):
    """动作类型"""
    CLICK = "click"
    TYPE = "type"
    NAVIGATE = "navigate"
    SCROLL = "scroll"
    SCREENSHOT = "screenshot"
    WAIT = "wait"


class HilTriggerReason(str, Enum):
    """HIL 触发原因"""
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    PARSE_FAILURE = "PARSE_FAILURE"
    UNKNOWN_ELEMENT = "UNKNOWN_ELEMENT"
    EXECUTION_FAILURE = "EXECUTION_FAILURE"


class HilDecision(str, Enum):
    """HIL 决策"""
    APPROVE = "APPROVED"
    REJECT = "REJECTED"
    MODIFIED = "MODIFIED"


class PlannedAction(BaseModel):
    """计划动作"""
    action_type: ActionType
    selector: Optional[str] = None
    value: Optional[str] = None
    url: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    thought: str = ""


class ExecutionState(BaseModel):
    """执行状态 - LangGraph 的 state"""

    # 基本信息
    instance_id: str
    tenant_id: str
    task_id: str
    target_url: str

    # 状态机状态
    current_node: NodeName = NodeName.INIT
    step_count: int = 0
    max_steps: int = 10

    # 动作计划
    planned_action: Optional[PlannedAction] = None

    # 执行结果
    last_screenshot: Optional[str] = None  # base64
    hil_triggered: bool = False
    hil_reason: Optional[HilTriggerReason] = None

    # 错误处理
    error: Optional[str] = None
    retry_count: int = 0

    # 元数据
    class Config:
        use_enum_values = True


class NodeResult(BaseModel):
    """节点执行结果"""
    node_name: str
    success: bool
    next_node: NodeName
    state: ExecutionState
    error: Optional[str] = None


class ExecutionResult(BaseModel):
    """执行结果"""
    success: bool
    instance_id: str
    status: InstanceStatus
    final_state: ExecutionState
    message: Optional[str] = None

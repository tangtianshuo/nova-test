"""
Nova Test AaaS LangGraph 状态机
===============================
基于 LangGraph 实现的智能体状态机

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求：
- 使用 LangGraph 管理状态流转
- 节点包括: init, explore, check_hil, execute, verify

状态转换图：
    start -> init -> explore -> check_hil -> execute -> verify -> end
                       ^                                      |
                       +--------------------------------------+
"""

import logging
from typing import Literal, Annotated, TYPE_CHECKING
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from nova_executor.types import (
    ExecutionState,
    NodeName,
    InstanceStatus,
    NodeResult,
)
from nova_executor.nodes import (
    init_node,
    explore_node,
    check_hil_node,
    execute_node,
    verify_node,
)
from nova_executor.config import get_settings

if TYPE_CHECKING:
    from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)
settings = get_settings()


def should_continue(state: ExecutionState) -> Literal[
    str,
    "terminate"
]:
    """
    决定下一个节点

    这是状态机的核心路由函数，控制状态流转逻辑。

    Args:
        state: 当前执行状态

    Returns:
        下一个节点名称或 "terminate" 终止执行
    """
    if state.step_count >= state.max_steps:
        logger.info(f"[Graph] 达到最大步数 {state.max_steps}，终止")
        return "terminate"

    if state.error:
        logger.info(f"[Graph] 发生错误，终止: {state.error}")
        return "terminate"

    if state.hil_triggered:
        logger.info(f"[Graph] HIL 触发，暂停等待人工介入")
        return "terminate"

    current = state.current_node.value if hasattr(state.current_node, 'value') else state.current_node

    if current == NodeName.INIT.value:
        return NodeName.EXPLORE.value

    elif current == NodeName.EXPLORE.value:
        return NodeName.CHECK_HIL.value

    elif current == NodeName.CHECK_HIL.value:
        if state.hil_triggered:
            return "terminate"
        return NodeName.EXECUTE.value

    elif current == NodeName.EXECUTE.value:
        return NodeName.VERIFY.value

    elif current == NodeName.VERIFY.value:
        return NodeName.EXPLORE.value

    else:
        logger.warning(f"[Graph] 未知节点: {current}，终止")
        return "terminate"


def create_execution_graph(checkpointer=None):
    """
    创建 LangGraph 执行图

    Args:
        checkpointer: LangGraph checkpointer，用于状态持久化

    Returns:
        Compiled LangGraph
    """
    workflow = StateGraph(ExecutionState)

    workflow.add_node(NodeName.INIT.value, init_node)
    workflow.add_node(NodeName.EXPLORE.value, explore_node)
    workflow.add_node(NodeName.CHECK_HIL.value, check_hil_node)
    workflow.add_node(NodeName.EXECUTE.value, execute_node)
    workflow.add_node(NodeName.VERIFY.value, verify_node)

    workflow.set_entry_point(NodeName.INIT.value)

    workflow.add_conditional_edges(
        NodeName.INIT.value,
        should_continue,
        {
            NodeName.EXPLORE.value: NodeName.EXPLORE.value,
            "terminate": END
        }
    )

    workflow.add_conditional_edges(
        NodeName.EXPLORE.value,
        should_continue,
        {
            NodeName.CHECK_HIL.value: NodeName.CHECK_HIL.value,
            "terminate": END
        }
    )

    workflow.add_conditional_edges(
        NodeName.CHECK_HIL.value,
        should_continue,
        {
            NodeName.EXECUTE.value: NodeName.EXECUTE.value,
            "terminate": END
        }
    )

    workflow.add_conditional_edges(
        NodeName.EXECUTE.value,
        should_continue,
        {
            NodeName.VERIFY.value: NodeName.VERIFY.value,
            "terminate": END
        }
    )

    workflow.add_conditional_edges(
        NodeName.VERIFY.value,
        should_continue,
        {
            NodeName.EXPLORE.value: NodeName.EXPLORE.value,
            "terminate": END
        }
    )

    graph = workflow.compile(checkpointer=checkpointer)

    return graph


class ExecutionGraph:
    """
    LangGraph 执行管理器

    封装 LangGraph 的执行逻辑，提供高层 API
    """

    def __init__(self, checkpointer=None):
        self.graph = create_execution_graph(checkpointer)

    async def execute(self, initial_state: ExecutionState, config: dict = None) -> ExecutionState:
        """
        执行状态机

        Args:
            initial_state: 初始状态
            config: LangGraph 配置（包含 thread_id 等）

        Returns:
            最终状态
        """
        logger.info(f"[Graph] 开始执行: instance_id={initial_state.instance_id}")

        try:
            final_state = None
            async for state_update in self.graph.astream(
                initial_state.model_dump(),
                config=config or {"configurable": {"thread_id": initial_state.instance_id}}
            ):
                logger.debug(f"[Graph] State update: {state_update}")
                final_state = state_update

            if final_state is None:
                logger.error(f"[Graph] 执行失败: 无最终状态")
                initial_state.error = "Execution failed: no final state"
                return initial_state

            result = ExecutionState(**final_state)
            logger.info(
                f"[Graph] 执行完成: instance_id={initial_state.instance_id}, "
                f"steps={result.step_count}, status={result.current_node}"
            )
            return result

        except Exception as e:
            logger.exception(f"[Graph] 执行异常: {e}")
            initial_state.error = str(e)
            initial_state.hil_triggered = True
            return initial_state

    def get_state(self, config: dict) -> ExecutionState:
        """获取当前状态"""
        state = self.graph.get_state(config)
        return ExecutionState(**state.values) if state else None

    def update_state(self, config: dict, updates: dict) -> ExecutionState:
        """更新状态"""
        self.graph.update_state(config, updates)
        return self.get_state(config)


def create_checkpointer(database_url: str = None):
    """
    创建 checkpointer

    用于 LangGraph 状态持久化，支持断点续测和容错恢复

    Args:
        database_url: PostgreSQL 连接字符串，如果为 None 则使用内存存储
    """
    if database_url:
        try:
            from langgraph.checkpoint.postgres import PostgresSaver
            return PostgresSaver.from_conn_string(database_url)
        except ImportError:
            logger.warning("[Graph] langgraph-checkpoint-postgres 未安装，使用内存存储")
            from langgraph.checkpoint.memory import MemorySaver
            return MemorySaver()
    else:
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()

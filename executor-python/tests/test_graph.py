"""
LangGraph 状态机测试
===================

验证状态机的创建和路由逻辑
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from nova_executor.types import (
    ExecutionState,
    NodeName,
    ActionType,
    PlannedAction,
    InstanceStatus,
)
from nova_executor.graph import (
    create_execution_graph,
    ExecutionGraph,
    should_continue,
)


class TestCreateExecutionGraph:
    """创建执行图测试"""

    def test_create_graph_without_checkpointer(self):
        """验证无 checkpointer 创建图"""
        graph = create_execution_graph()
        assert graph is not None

    def test_create_graph_with_checkpointer(self):
        """验证带 checkpointer 创建图"""
        mock_checkpointer = MagicMock()
        graph = create_execution_graph(checkpointer=mock_checkpointer)
        assert graph is not None

    def test_graph_has_all_nodes(self):
        """验证图包含所有节点"""
        graph = create_execution_graph()
        node_names = ["init", "explore", "check_hil", "execute", "verify"]
        for name in node_names:
            assert name in graph.nodes


class TestShouldContinue:
    """路由逻辑测试"""

    def test_init_routes_to_explore(self):
        """验证 init 节点路由到 explore"""
        state = ExecutionState(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
            current_node=NodeName.INIT,
        )
        result = should_continue(state)
        assert result == NodeName.EXPLORE.value

    def test_explore_routes_to_check_hil(self):
        """验证 explore 节点路由到 check_hil"""
        state = ExecutionState(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
            current_node=NodeName.EXPLORE,
        )
        result = should_continue(state)
        assert result == NodeName.CHECK_HIL.value

    def test_check_hil_routes_to_execute(self):
        """验证 check_hil 节点路由到 execute"""
        state = ExecutionState(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
            current_node=NodeName.CHECK_HIL,
            hil_triggered=False,
        )
        result = should_continue(state)
        assert result == NodeName.EXECUTE.value

    def test_check_hil_hil_triggered_terminates(self):
        """验证 check_hil 节点 HIL 触发时终止"""
        state = ExecutionState(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
            current_node=NodeName.CHECK_HIL,
            hil_triggered=True,
        )
        result = should_continue(state)
        assert result == "terminate"

    def test_execute_routes_to_verify(self):
        """验证 execute 节点路由到 verify"""
        state = ExecutionState(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
            current_node=NodeName.EXECUTE,
        )
        result = should_continue(state)
        assert result == NodeName.VERIFY.value

    def test_verify_routes_to_explore(self):
        """验证 verify 节点路由回 explore"""
        state = ExecutionState(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
            current_node=NodeName.VERIFY,
            step_count=1,
            max_steps=10,
        )
        result = should_continue(state)
        assert result == NodeName.EXPLORE.value


class TestTerminationConditions:
    """终止条件测试"""

    def test_max_steps_terminates(self):
        """验证达到最大步数终止"""
        state = ExecutionState(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
            current_node=NodeName.EXPLORE,
            step_count=10,
            max_steps=10,
        )
        result = should_continue(state)
        assert result == "terminate"

    def test_error_terminates(self):
        """验证错误状态终止"""
        state = ExecutionState(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
            current_node=NodeName.EXPLORE,
            error="Something went wrong",
        )
        result = should_continue(state)
        assert result == "terminate"

    def test_hil_triggered_terminates(self):
        """验证 HIL 触发终止"""
        state = ExecutionState(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
            current_node=NodeName.CHECK_HIL,
            hil_triggered=True,
        )
        result = should_continue(state)
        assert result == "terminate"


class TestExecutionGraph:
    """执行图管理器测试"""

    def test_init_without_checkpointer(self):
        """验证无 checkpointer 初始化"""
        graph_manager = ExecutionGraph()
        assert graph_manager.graph is not None

    def test_init_with_checkpointer(self):
        """验证带 checkpointer 初始化"""
        mock_checkpointer = MagicMock()
        graph_manager = ExecutionGraph(checkpointer=mock_checkpointer)
        assert graph_manager.graph is not None

    @pytest.mark.asyncio
    async def test_execute_returns_state(self):
        """验证执行返回状态"""
        graph_manager = ExecutionGraph()

        initial_state = ExecutionState(
            instance_id="test-instance",
            tenant_id="test-tenant",
            task_id="test-task",
            target_url="https://example.com",
            max_steps=1,
        )

        with patch("nova_executor.graph.init_node") as mock_init:
            mock_init.return_value = {"current_node": NodeName.INIT}

            result = await graph_manager.execute(initial_state)

            assert result is not None


class TestStateTransitions:
    """状态转换测试"""

    def test_state_transition_init_to_explore(self):
        """验证 init 到 explore 状态转换"""
        state = ExecutionState(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
            current_node=NodeName.INIT,
        )

        next_node = should_continue(state)
        assert next_node == NodeName.EXPLORE.value

    def test_state_transition_explore_to_check_hil(self):
        """验证 explore 到 check_hil 状态转换"""
        state = ExecutionState(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
            current_node=NodeName.EXPLORE,
        )

        next_node = should_continue(state)
        assert next_node == NodeName.CHECK_HIL.value

    def test_state_transition_check_hil_to_execute(self):
        """验证 check_hil 到 execute 状态转换"""
        state = ExecutionState(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
            current_node=NodeName.CHECK_HIL,
            hil_triggered=False,
        )

        next_node = should_continue(state)
        assert next_node == NodeName.EXECUTE.value

    def test_state_transition_execute_to_verify(self):
        """验证 execute 到 verify 状态转换"""
        state = ExecutionState(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
            current_node=NodeName.EXECUTE,
        )

        next_node = should_continue(state)
        assert next_node == NodeName.VERIFY.value

    def test_state_transition_verify_back_to_explore(self):
        """验证 verify 回到 explore 状态转换"""
        state = ExecutionState(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
            current_node=NodeName.VERIFY,
            step_count=1,
            max_steps=10,
        )

        next_node = should_continue(state)
        assert next_node == NodeName.EXPLORE.value

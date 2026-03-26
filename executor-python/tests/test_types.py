"""
类型定义测试
============

验证状态机类型定义
"""

import pytest
from nova_executor.types import (
    ExecutionState,
    InstanceStatus,
    NodeName,
    ActionType,
    PlannedAction,
    HilTriggerReason,
    HilDecision,
)


class TestInstanceStatus:
    """实例状态枚举测试"""

    def test_all_statuses_defined(self):
        """验证所有状态已定义"""
        assert InstanceStatus.PENDING.value == "PENDING"
        assert InstanceStatus.INITIALIZED.value == "INITIALIZED"
        assert InstanceStatus.RUNNING.value == "RUNNING"
        assert InstanceStatus.WAITING_HIL.value == "WAITING_HIL"
        assert InstanceStatus.COMPLETED.value == "COMPLETED"
        assert InstanceStatus.FAILED.value == "FAILED"
        assert InstanceStatus.TERMINATED.value == "TERMINATED"


class TestNodeName:
    """节点名称枚举测试"""

    def test_all_nodes_defined(self):
        """验证所有节点已定义"""
        assert NodeName.INIT.value == "init"
        assert NodeName.EXPLORE.value == "explore"
        assert NodeName.CHECK_HIL.value == "check_hil"
        assert NodeName.EXECUTE.value == "execute"
        assert NodeName.VERIFY.value == "verify"
        assert NodeName.END.value == "end"


class TestActionType:
    """动作类型枚举测试"""

    def test_all_action_types_defined(self):
        """验证所有动作类型已定义"""
        assert ActionType.CLICK.value == "click"
        assert ActionType.TYPE.value == "type"
        assert ActionType.NAVIGATE.value == "navigate"
        assert ActionType.SCROLL.value == "scroll"
        assert ActionType.SCREENSHOT.value == "screenshot"
        assert ActionType.WAIT.value == "wait"


class TestExecutionState:
    """执行状态测试"""

    def test_create_state_with_defaults(self):
        """验证默认状态"""
        state = ExecutionState(
            instance_id="test-instance",
            tenant_id="test-tenant",
            task_id="test-task",
            target_url="https://example.com",
        )

        assert state.instance_id == "test-instance"
        assert state.current_node == NodeName.INIT
        assert state.step_count == 0
        assert state.max_steps == 10
        assert state.hil_triggered is False
        assert state.planned_action is None

    def test_create_state_with_action(self):
        """验证带动作的状态"""
        action = PlannedAction(
            action_type=ActionType.CLICK,
            selector="#submit",
            confidence=0.9,
            thought="Click submit button",
        )

        state = ExecutionState(
            instance_id="test-instance",
            tenant_id="test-tenant",
            task_id="test-task",
            target_url="https://example.com",
            planned_action=action,
        )

        assert state.planned_action is not None
        assert state.planned_action.action_type == ActionType.CLICK
        assert state.planned_action.selector == "#submit"


class TestPlannedAction:
    """计划动作测试"""

    def test_create_click_action(self):
        """验证点击动作"""
        action = PlannedAction(
            action_type=ActionType.CLICK,
            selector="#btn",
            confidence=0.95,
            thought="Click the button",
        )

        assert action.action_type == ActionType.CLICK
        assert action.selector == "#btn"
        assert action.confidence == 0.95

    def test_create_type_action(self):
        """验证输入动作"""
        action = PlannedAction(
            action_type=ActionType.TYPE,
            selector="input[name='q']",
            value="test query",
            confidence=0.85,
            thought="Type search query",
        )

        assert action.action_type == ActionType.TYPE
        assert action.value == "test query"

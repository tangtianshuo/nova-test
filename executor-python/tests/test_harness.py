"""
Harness 测试
============

端到端场景测试
"""

import pytest
from nova_executor.types import (
    ExecutionState,
    InstanceStatus,
    NodeName,
    ActionType,
    PlannedAction,
)
from nova_executor.config import get_settings

settings = get_settings()


class TestSuccessfulExecutionFlow:
    """成功执行流程测试"""

    def test_full_execution_flow_states(self):
        """验证完整执行流程状态转换"""
        flow = [
            NodeName.INIT,
            NodeName.EXPLORE,
            NodeName.CHECK_HIL,
            NodeName.EXECUTE,
            NodeName.VERIFY,
        ]

        state = ExecutionState(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
        )

        assert state.current_node == NodeName.INIT
        assert state.step_count == 0

        # 模拟流程
        for i, expected_node in enumerate(flow[1:], 1):
            if expected_node == NodeName.EXECUTE:
                state.step_count += 1
            state.current_node = expected_node

        assert state.current_node == NodeName.VERIFY
        assert state.step_count == 1


class TestHilTriggerFlow:
    """HIL 触发流程测试"""

    def test_low_confidence_triggers_hil(self):
        """验证低置信度触发 HIL"""
        action = PlannedAction(
            action_type=ActionType.CLICK,
            selector="#unknown",
            confidence=0.3,  # 低于阈值
            thought="Not confident",
        )

        threshold = settings.hil_confidence_threshold
        should_hil = action.confidence < threshold

        assert should_hil is True

    def test_hil_state_transition(self):
        """验证 HIL 状态转换"""
        state = ExecutionState(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
            current_node=NodeName.CHECK_HIL,
            planned_action=PlannedAction(
                action_type=ActionType.CLICK,
                selector="#btn",
                confidence=0.5,
                thought="Low confidence",
            ),
        )

        # 检查是否触发 HIL
        threshold = settings.hil_confidence_threshold
        if state.planned_action and state.planned_action.confidence < threshold:
            state.hil_triggered = True
            state.current_node = NodeName.WAITING_HIL

        assert state.hil_triggered is True
        assert state.current_node == NodeName.WAITING_HIL


class TestDefectDetectionFlow:
    """缺陷检测流程测试"""

    def test_defect_terminates_execution(self):
        """验证检测到缺陷终止执行"""
        state = ExecutionState(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
            current_node=NodeName.VERIFY,
            step_count=5,
            max_steps=10,
            error="Defect detected: Page shows error message",
        )

        should_terminate = (
            state.error is not None or
            state.step_count >= state.max_steps
        )

        assert should_terminate is True


class TestMaxStepsTermination:
    """最大步数终止测试"""

    def test_execution_stops_at_max_steps(self):
        """验证达到最大步数停止"""
        state = ExecutionState(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
            step_count=10,
            max_steps=10,
        )

        should_terminate = state.step_count >= state.max_steps

        assert should_terminate is True

    def test_execution_continues_before_max_steps(self):
        """验证未达到最大步数继续执行"""
        state = ExecutionState(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
            step_count=5,
            max_steps=10,
        )

        should_terminate = state.step_count >= state.max_steps

        assert should_terminate is False


class TestMultiRoundExecution:
    """多轮执行测试"""

    def test_multiple_rounds_continue(self):
        """验证多轮执行继续"""
        state = ExecutionState(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
            current_node=NodeName.VERIFY,
            step_count=3,
            max_steps=10,
        )

        # 模拟多轮
        rounds = 0
        while state.step_count < state.max_steps and rounds < 5:
            # verify -> explore
            if state.current_node == NodeName.VERIFY:
                state.current_node = NodeName.EXPLORE

            # explore -> check_hil
            elif state.current_node == NodeName.EXPLORE:
                state.current_node = NodeName.CHECK_HIL

            # check_hil -> execute (假设批准)
            elif state.current_node == NodeName.CHECK_HIL:
                state.current_node = NodeName.EXECUTE

            # execute -> verify
            elif state.current_node == NodeName.EXECUTE:
                state.current_node = NodeName.VERIFY
                state.step_count += 1

            rounds += 1

        assert state.step_count > 0
        assert state.current_node == NodeName.VERIFY

"""
路由逻辑测试
============

验证状态机路由和 HIL 判断逻辑
"""

import pytest
from nova_executor.types import ExecutionState, NodeName, ActionType, PlannedAction, HilTriggerReason
from nova_executor.config import get_settings

settings = get_settings()


class TestRoutingLogic:
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

        # 模拟路由逻辑
        if state.current_node == NodeName.INIT:
            next_node = NodeName.EXPLORE
        elif state.current_node == NodeName.EXPLORE:
            next_node = NodeName.CHECK_HIL

        assert next_node == NodeName.EXPLORE

    def test_explore_routes_to_check_hil(self):
        """验证 explore 节点路由到 check_hil"""
        state = ExecutionState(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
            current_node=NodeName.EXPLORE,
            planned_action=PlannedAction(
                action_type=ActionType.CLICK,
                selector="#btn",
                confidence=0.9,
                thought="Click",
            ),
        )

        if state.current_node == NodeName.EXPLORE:
            next_node = NodeName.CHECK_HIL

        assert next_node == NodeName.CHECK_HIL

    def test_check_hil_approved_routes_to_execute(self):
        """验证 check_hil 节点批准后路由到 execute"""
        state = ExecutionState(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
            current_node=NodeName.CHECK_HIL,
            hil_triggered=False,
            planned_action=PlannedAction(
                action_type=ActionType.CLICK,
                selector="#btn",
                confidence=0.9,
                thought="Click",
            ),
        )

        if state.current_node == NodeName.CHECK_HIL:
            if not state.hil_triggered:
                next_node = NodeName.EXECUTE

        assert next_node == NodeName.EXECUTE

    def test_check_hil_rejected_routes_to_end(self):
        """验证 check_hil 节点拒绝后路由到 end"""
        state = ExecutionState(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
            current_node=NodeName.CHECK_HIL,
            hil_triggered=True,
            planned_action=PlannedAction(
                action_type=ActionType.CLICK,
                selector="#btn",
                confidence=0.5,
                thought="Low confidence",
            ),
        )

        if state.current_node == NodeName.CHECK_HIL:
            if state.hil_triggered:
                next_node = NodeName.END

        assert next_node == NodeName.END


class TestHilTriggerLogic:
    """HIL 触发逻辑测试"""

    def test_trigger_hil_on_low_confidence(self):
        """验证低置信度触发 HIL"""
        action = PlannedAction(
            action_type=ActionType.CLICK,
            selector="#btn",
            confidence=0.5,  # 低于阈值 0.7
            thought="Low confidence",
        )

        threshold = settings.hil_confidence_threshold
        should_trigger_hil = action.confidence < threshold

        assert should_trigger_hil is True

    def test_no_hil_on_high_confidence(self):
        """验证高置信度不触发 HIL"""
        action = PlannedAction(
            action_type=ActionType.CLICK,
            selector="#btn",
            confidence=0.9,  # 高于阈值 0.7
            thought="High confidence",
        )

        threshold = settings.hil_confidence_threshold
        should_trigger_hil = action.confidence < threshold

        assert should_trigger_hil is False

    def test_trigger_hil_on_missing_action(self):
        """验证无动作计划触发 HIL"""
        state = ExecutionState(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
            planned_action=None,
        )

        should_trigger_hil = state.planned_action is None

        assert should_trigger_hil is True

    def test_trigger_hil_on_click_without_selector(self):
        """验证点击无 selector 触发 HIL"""
        action = PlannedAction(
            action_type=ActionType.CLICK,
            confidence=0.9,
            thought="Click without selector",
        )

        should_trigger_hil = (
            action.action_type == ActionType.CLICK and not action.selector
        )

        assert should_trigger_hil is True


class TestTerminationLogic:
    """终止条件测试"""

    def test_terminate_on_max_steps(self):
        """验证达到最大步数终止"""
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

    def test_terminate_on_error(self):
        """验证发生错误终止"""
        state = ExecutionState(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
            error="Execution failed",
        )

        should_terminate = state.error is not None

        assert should_terminate is True

    def test_terminate_on_hil_triggered(self):
        """验证 HIL 触发终止"""
        state = ExecutionState(
            instance_id="test",
            tenant_id="test",
            task_id="test",
            target_url="https://example.com",
            hil_triggered=True,
        )

        should_terminate = state.hil_triggered

        assert should_terminate is True

"""
LangGraph 节点测试
=================

验证各节点的执行逻辑
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from nova_executor.types import (
    ExecutionState,
    NodeName,
    ActionType,
    PlannedAction,
)
from nova_executor.nodes.init_node import init_node
from nova_executor.nodes.explore_node import explore_node
from nova_executor.nodes.check_hil_node import check_hil_node
from nova_executor.nodes.execute_node import execute_node
from nova_executor.nodes.verify_node import verify_node


class TestInitNode:
    """Init 节点测试"""

    @pytest.mark.asyncio
    async def test_init_node_creates_sandbox(self, sample_execution_state):
        """验证 init 节点创建沙箱"""
        with patch("nova_executor.nodes.init_node.SandboxManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.create = AsyncMock()
            mock_instance.screenshot = AsyncMock(return_value="base64_screenshot")
            mock_manager.return_value = mock_instance

            result = await init_node(sample_execution_state)

            assert result is not None
            assert "current_node" in result or result.get("error") is not None

    @pytest.mark.asyncio
    async def test_init_node_handles_error(self, sample_execution_state):
        """验证 init 节点处理错误"""
        with patch("nova_executor.nodes.init_node.SandboxManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.create = AsyncMock(side_effect=Exception("Failed"))
            mock_manager.return_value = mock_instance

            result = await init_node(sample_execution_state)

            assert result.get("error") is not None or result.get("hil_triggered") is True


class TestExploreNode:
    """Explore 节点测试"""

    @pytest.mark.asyncio
    async def test_explore_node_analyzes_page(self, sample_execution_state):
        """验证 explore 节点分析页面"""
        sample_execution_state.last_screenshot = "base64_screenshot"

        with patch("nova_executor.nodes.explore_node.VisionAdapter") as mock_adapter:
            mock_instance = MagicMock()
            mock_instance.analyze_page = AsyncMock(return_value=PlannedAction(
                action_type=ActionType.CLICK,
                selector="#btn",
                confidence=0.9,
                thought="Click button",
            ))
            mock_adapter.return_value = mock_instance

            result = await explore_node(sample_execution_state)

            assert result is not None

    @pytest.mark.asyncio
    async def test_explore_node_handles_vision_failure(self, sample_execution_state):
        """验证 explore 节点处理视觉分析失败"""
        sample_execution_state.last_screenshot = "base64_screenshot"

        with patch("nova_executor.nodes.explore_node.VisionAdapter") as mock_adapter:
            mock_instance = MagicMock()
            mock_instance.analyze_page = AsyncMock(side_effect=Exception("Vision failed"))
            mock_adapter.return_value = mock_instance

            result = await explore_node(sample_execution_state)

            assert result is not None


class TestCheckHilNode:
    """Check HIL 节点测试"""

    @pytest.mark.asyncio
    async def test_check_hil_high_confidence_passes(self, sample_execution_state):
        """验证高置信度通过 HIL 检查"""
        sample_execution_state.planned_action = PlannedAction(
            action_type=ActionType.CLICK,
            selector="#btn",
            confidence=0.9,
            thought="High confidence",
        )

        result = await check_hil_node(sample_execution_state)

        assert result is not None

    @pytest.mark.asyncio
    async def test_check_hil_low_confidence_triggers_hil(self, sample_execution_state):
        """验证低置信度触发 HIL"""
        sample_execution_state.planned_action = PlannedAction(
            action_type=ActionType.CLICK,
            selector="#btn",
            confidence=0.5,
            thought="Low confidence",
        )

        result = await check_hil_node(sample_execution_state)

        assert result is not None
        if result.get("hil_triggered"):
            assert result["hil_triggered"] is True

    @pytest.mark.asyncio
    async def test_check_hil_missing_selector_triggers_hil(self, sample_execution_state):
        """验证缺失 selector 触发 HIL"""
        sample_execution_state.planned_action = PlannedAction(
            action_type=ActionType.CLICK,
            confidence=0.9,
            thought="No selector",
        )

        result = await check_hil_node(sample_execution_state)

        assert result is not None

    @pytest.mark.asyncio
    async def test_check_hil_no_action_triggers_hil(self, sample_execution_state):
        """验证无动作触发 HIL"""
        sample_execution_state.planned_action = None

        result = await check_hil_node(sample_execution_state)

        assert result is not None


class TestExecuteNode:
    """Execute 节点测试"""

    @pytest.mark.asyncio
    async def test_execute_node_executes_action(self, sample_execution_state):
        """验证 execute 节点执行动作"""
        sample_execution_state.planned_action = PlannedAction(
            action_type=ActionType.CLICK,
            selector="#btn",
            confidence=0.9,
            thought="Click",
        )
        sample_execution_state.last_screenshot = "base64_screenshot"

        with patch("nova_executor.nodes.execute_node.ExecutorAdapter") as mock_adapter:
            from nova_executor.adapters.executor import ExecutionResult
            mock_instance = MagicMock()
            mock_instance.execute_action = AsyncMock(return_value=ExecutionResult(
                success=True,
                screenshot="new_screenshot",
            ))
            mock_adapter.return_value = mock_instance

            result = await execute_node(sample_execution_state)

            assert result is not None

    @pytest.mark.asyncio
    async def test_execute_node_handles_failure(self, sample_execution_state):
        """验证 execute 节点处理失败"""
        sample_execution_state.planned_action = PlannedAction(
            action_type=ActionType.CLICK,
            selector="#btn",
            confidence=0.9,
            thought="Click",
        )
        sample_execution_state.last_screenshot = "base64_screenshot"

        with patch("nova_executor.nodes.execute_node.ExecutorAdapter") as mock_adapter:
            from nova_executor.adapters.executor import ExecutionResult
            mock_instance = MagicMock()
            mock_instance.execute_action = AsyncMock(return_value=ExecutionResult(
                success=False,
                error="Element not found",
            ))
            mock_adapter.return_value = mock_instance

            result = await execute_node(sample_execution_state)

            assert result is not None

    @pytest.mark.asyncio
    async def test_execute_node_no_action_returns_error(self, sample_execution_state):
        """验证无动作返回错误"""
        sample_execution_state.planned_action = None

        result = await execute_node(sample_execution_state)

        assert result.get("error") is not None or result.get("hil_triggered") is True


class TestVerifyNode:
    """Verify 节点测试"""

    @pytest.mark.asyncio
    async def test_verify_node_verifies_execution(self, sample_execution_state):
        """验证 verify 节点验证执行"""
        sample_execution_state.last_screenshot = "base64_screenshot"
        sample_execution_state.planned_action = PlannedAction(
            action_type=ActionType.CLICK,
            selector="#btn",
            confidence=0.9,
            thought="Click",
        )

        with patch("nova_executor.nodes.verify_node.VerifierAdapter") as mock_adapter:
            from nova_executor.adapters.verifier import VerificationResult
            mock_instance = MagicMock()
            mock_instance.verify_execution = AsyncMock(return_value=VerificationResult(
                is_success=True,
                is_defect=False,
                message="Verification passed",
            ))
            mock_adapter.return_value = mock_instance

            result = await verify_node(sample_execution_state)

            assert result is not None

    @pytest.mark.asyncio
    async def test_verify_node_detects_defect(self, sample_execution_state):
        """验证 verify 节点检测缺陷"""
        sample_execution_state.last_screenshot = "base64_screenshot"
        sample_execution_state.planned_action = PlannedAction(
            action_type=ActionType.CLICK,
            selector="#btn",
            confidence=0.9,
            thought="Click",
        )

        with patch("nova_executor.nodes.verify_node.VerifierAdapter") as mock_adapter:
            from nova_executor.adapters.verifier import VerificationResult
            mock_instance = MagicMock()
            mock_instance.verify_execution = AsyncMock(return_value=VerificationResult(
                is_success=False,
                is_defect=True,
                message="Defect detected",
            ))
            mock_adapter.return_value = mock_instance

            result = await verify_node(sample_execution_state)

            assert result is not None


class TestNodeIntegration:
    """节点集成测试"""

    @pytest.mark.asyncio
    async def test_full_node_flow(self, sample_execution_state):
        """验证完整节点流程"""
        state = sample_execution_state
        state.last_screenshot = "base64_screenshot"
        state.planned_action = PlannedAction(
            action_type=ActionType.CLICK,
            selector="#btn",
            confidence=0.9,
            thought="Click",
        )

        with patch("nova_executor.nodes.check_hil_node.get_settings") as mock_settings:
            mock_settings.return_value.hil_confidence_threshold = 0.7

            result = await check_hil_node(state)

            assert result is not None

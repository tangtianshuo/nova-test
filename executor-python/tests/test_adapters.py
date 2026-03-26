"""
适配器测试
==========

验证 Vision、Executor、Verifier 适配器
"""

import pytest
from nova_executor.adapters import (
    VisionAdapter,
    MockVisionAdapter,
    ExecutorAdapter,
    MockExecutorAdapter,
    VerifierAdapter,
    MockVerifierAdapter,
)
from nova_executor.types import PlannedAction, ActionType


class TestMockVisionAdapter:
    """Mock Vision 适配器测试"""

    @pytest.mark.asyncio
    async def test_analyze_page_returns_valid_action(self):
        """验证分析页面返回有效动作"""
        adapter = MockVisionAdapter()

        result = await adapter.analyze_page(
            screenshot="fake_screenshot",
            instance_id="test-instance",
            target_url="https://example.com",
        )

        assert result is not None
        assert isinstance(result, PlannedAction)
        assert result.action_type in list(ActionType)
        assert 0 <= result.confidence <= 1
        assert result.thought is not None

    @pytest.mark.asyncio
    async def test_analyze_page_with_valid_confidence(self):
        """验证置信度在有效范围内"""
        adapter = MockVisionAdapter()

        # 执行多次，确保置信度始终在有效范围
        for _ in range(10):
            result = await adapter.analyze_page(
                screenshot="fake_screenshot",
                instance_id="test-instance",
                target_url="https://example.com",
            )

            assert 0 <= result.confidence <= 1


class TestMockExecutorAdapter:
    """Mock Executor 适配器测试"""

    @pytest.mark.asyncio
    async def test_execute_click_action(self):
        """验证执行点击动作"""
        adapter = MockExecutorAdapter()

        action = PlannedAction(
            action_type=ActionType.CLICK,
            selector="#btn",
            confidence=0.9,
            thought="Click button",
        )

        result = await adapter.execute_action(
            instance_id="test-instance",
            action=action,
            previous_screenshot="fake_screenshot",
        )

        assert result.success is True
        assert result.screenshot is not None


class TestMockVerifierAdapter:
    """Mock Verifier 适配器测试"""

    @pytest.mark.asyncio
    async def test_verify_execution_returns_result(self):
        """验证验证执行返回结果"""
        adapter = MockVerifierAdapter()

        action = PlannedAction(
            action_type=ActionType.CLICK,
            selector="#btn",
            confidence=0.9,
            thought="Click button",
        )

        result = await adapter.verify_execution(
            screenshot="fake_screenshot",
            previous_screenshot="prev_screenshot",
            action=action,
            instance_id="test-instance",
        )

        assert result.is_success is not None
        assert result.is_defect is not None
        assert result.message is not None

    @pytest.mark.asyncio
    async def test_verify_returns_message(self):
        """验证返回消息"""
        adapter = MockVerifierAdapter()

        result = await adapter.verify_execution(
            screenshot="fake_screenshot",
            previous_screenshot="prev_screenshot",
            action=None,
            instance_id="test-instance",
        )

        assert isinstance(result.message, str)
        assert len(result.message) > 0

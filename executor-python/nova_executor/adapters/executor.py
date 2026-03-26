"""
Executor 适配器
===============

调用 Magentic-UI (Playwright) 执行浏览器动作

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求：
- Magentic-UI 提供沙盒内的无头浏览器控制
"""

import logging
import base64
from typing import Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass

from nova_executor.types import PlannedAction, ActionType
from nova_executor.sandbox import SandboxManager

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    screenshot: Optional[str] = None
    error: Optional[str] = None


class ExecutorAdapterBase(ABC):
    """Executor 适配器基类"""

    @abstractmethod
    async def execute_action(
        self,
        instance_id: str,
        action: PlannedAction,
        previous_screenshot: Optional[str],
    ) -> ExecutionResult:
        """执行动作"""
        pass


class ExecutorAdapter(ExecutorAdapterBase):
    """
    Executor 适配器 - 调用 Playwright

    使用 Playwright 执行浏览器动作
    """

    def __init__(self):
        self.sandbox_manager = SandboxManager()

    async def execute_action(
        self,
        instance_id: str,
        action: PlannedAction,
        previous_screenshot: Optional[str],
    ) -> ExecutionResult:
        """
        执行动作

        Args:
            instance_id: 实例 ID
            action: 计划动作
            previous_screenshot: 前一个截图

        Returns:
            执行结果
        """
        logger.info(f"[Executor] 执行动作: {action.action_type.value}")

        try:
            sandbox = self.sandbox_manager.get_sandbox(instance_id)
            if not sandbox:
                return ExecutionResult(
                    success=False,
                    error=f"Sandbox not found for instance: {instance_id}"
                )

            action_type = action.action_type.value

            # 根据动作类型执行
            if action_type == ActionType.CLICK.value:
                if not action.selector:
                    return ExecutionResult(success=False, error="Missing selector")
                await sandbox.click(action.selector, timeout=10000)

            elif action_type == ActionType.TYPE.value:
                if not action.selector or not action.value:
                    return ExecutionResult(success=False, error="Missing selector or value")
                await sandbox.fill(action.selector, action.value, timeout=10000)

            elif action_type == ActionType.NAVIGATE.value:
                if not action.url:
                    return ExecutionResult(success=False, error="Missing URL")
                await sandbox.goto(action.url, timeout=30000)

            elif action_type == ActionType.SCROLL.value:
                await sandbox.evaluate("window.scrollBy(0, 300)")

            elif action_type == ActionType.WAIT.value:
                await sandbox.wait_for_timeout(1000)

            elif action_type == ActionType.SCREENSHOT.value:
                pass  # 截图是最后统一做的

            else:
                return ExecutionResult(success=False, error=f"Unknown action type: {action_type}")

            # 执行成功后截图
            screenshot = await sandbox.screenshot()
            return ExecutionResult(success=True, screenshot=screenshot)

        except Exception as e:
            logger.exception(f"[Executor] 执行异常: {e}")
            try:
                screenshot = await sandbox.screenshot() if sandbox else None
            except:
                screenshot = None
            return ExecutionResult(success=False, error=str(e), screenshot=screenshot)


class MockExecutorAdapter(ExecutorAdapterBase):
    """
    Mock Executor 适配器

    用于开发和测试
    """

    async def execute_action(
        self,
        instance_id: str,
        action: PlannedAction,
        previous_screenshot: Optional[str],
    ) -> ExecutionResult:
        """模拟执行动作"""
        import random
        import time

        logger.info(f"[MockExecutor] 模拟执行: {action.action_type.value}")

        # 模拟执行延迟
        await time.sleep(0.5)

        # 90% 成功率
        if random.random() < 0.9:
            return ExecutionResult(
                success=True,
                screenshot=previous_screenshot or "",
            )
        else:
            return ExecutionResult(
                success=False,
                error="Mock execution failed",
                screenshot=previous_screenshot or "",
            )

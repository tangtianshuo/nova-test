"""
Verifier 适配器
===============

缺陷检测和执行结果验证

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求
"""

import logging
import random
from typing import Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass

from nova_executor.types import PlannedAction

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """验证结果"""
    is_success: bool
    is_defect: bool
    message: str
    screenshot: Optional[str] = None


class VerifierAdapterBase(ABC):
    """Verifier 适配器基类"""

    @abstractmethod
    async def verify_execution(
        self,
        screenshot: str,
        previous_screenshot: str,
        action: Optional[PlannedAction],
        instance_id: str,
    ) -> VerificationResult:
        """验证执行结果"""
        pass


class VerifierAdapter(VerifierAdapterBase):
    """
    Verifier 适配器

    调用缺陷检测模型验证执行结果
    """

    async def verify_execution(
        self,
        screenshot: str,
        previous_screenshot: str,
        action: Optional[PlannedAction],
        instance_id: str,
    ) -> VerificationResult:
        """
        验证执行结果

        Args:
            screenshot: 当前截图
            previous_screenshot: 前一个截图
            action: 执行的动作用于分析预期结果
            instance_id: 实例 ID

        Returns:
            验证结果
        """
        logger.info(f"[Verifier] 验证执行: {instance_id}")

        try:
            # TODO: 调用实际的缺陷检测模型
            # 目前使用 Mock 实现

            # 调用缺陷检测 API
            # response = await self.client.post("/verify", json={...})

            # Mock: 随机生成验证结果
            return await MockVerifierAdapter().verify_execution(
                screenshot, previous_screenshot, action, instance_id
            )

        except Exception as e:
            logger.exception(f"[Verifier] 验证异常: {e}")
            return VerificationResult(
                is_success=False,
                is_defect=False,
                message=f"Verification error: {str(e)}",
                screenshot=screenshot,
            )


class MockVerifierAdapter(VerifierAdapterBase):
    """
    Mock Verifier 适配器

    用于开发和测试
    """

    async def verify_execution(
        self,
        screenshot: str,
        previous_screenshot: str,
        action: Optional[PlannedAction],
        instance_id: str,
    ) -> VerificationResult:
        """模拟验证"""
        logger.info(f"[MockVerifier] 模拟验证: {instance_id}")

        # 10% 概率检测到缺陷
        if random.random() < 0.1:
            defect_messages = [
                "页面显示错误信息 'Error 500'",
                "检测到意外的弹窗",
                "页面加载超时",
                "元素不可点击",
            ]
            return VerificationResult(
                is_success=False,
                is_defect=True,
                message=random.choice(defect_messages),
                screenshot=screenshot,
            )

        # 90% 概率验证成功
        action_desc = f"成功执行 {action.action_type.value}" if action else "验证通过"
        return VerificationResult(
            is_success=True,
            is_defect=False,
            message=f"{action_desc}，页面状态正常",
            screenshot=screenshot,
        )

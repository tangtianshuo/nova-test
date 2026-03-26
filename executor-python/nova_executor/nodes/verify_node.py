"""
verify 节点 - 验证节点
======================

验证阶段，负责：
1. 验证执行结果是否符合预期
2. 使用 Verifier 模型检测缺陷
3. 判断是否需要继续执行或终止

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求
- 使用缺陷检测模型验证执行结果
"""

import logging
from typing import Dict, Any

from nova_executor.types import ExecutionState, NodeName
from nova_executor.adapters import VerifierAdapter

logger = logging.getLogger(__name__)


async def verify_node(state: ExecutionState) -> Dict[str, Any]:
    """
    verify 节点执行函数

    调用 Verifier 适配器验证执行结果

    Args:
        state: 当前执行状态

    Returns:
        状态更新字典
    """
    logger.info(f"[Verify] 验证结果: {state.instance_id}")

    try:
        # 调用 Verifier 适配器验证结果
        verifier = VerifierAdapter()
        result = await verifier.verify_execution(
            screenshot=state.last_screenshot or "",
            previous_screenshot="",
            action=state.planned_action,
            instance_id=state.instance_id,
        )

        logger.info(
            f"[Verify] 验证结果: success={result.is_success}, "
            f"defect={result.is_defect}"
        )

        # 处理缺陷检测
        if result.is_defect:
            logger.warning(f"[Verify] 检测到缺陷: {result.message}")
            return {
                "current_node": NodeName.VERIFY,
                "last_screenshot": result.screenshot,
                "error": f"Defect detected: {result.message}",
                "hil_triggered": True,
            }

        # 验证成功，继续探索
        if result.is_success:
            logger.info("[Verify] 验证通过")
            return {
                "current_node": NodeName.VERIFY,
                "last_screenshot": result.screenshot,
                "hil_triggered": False,
                "error": None,
            }

        # 验证失败但不是缺陷
        logger.warning(f"[Verify] 验证失败: {result.message}")
        return {
            "current_node": NodeName.VERIFY,
            "last_screenshot": result.screenshot,
            "error": result.message,
            "retry_count": state.retry_count + 1,
        }

    except Exception as e:
        logger.exception(f"[Verify] 验证异常: {e}")
        return {
            "current_node": NodeName.VERIFY,
            "hil_triggered": True,
            "error": f"Verify failed: {str(e)}",
        }

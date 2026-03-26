"""
check_hil 节点 - HIL 检查节点
==============================

HIL 检查阶段，负责：
1. 评估动作计划的置信度
2. 检查是否需要人工介入
3. 根据判断决定后续流程

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求

触发 HIL 的条件：
1. 置信度低于阈值 (HIL_CONFIG.CONFIDENCE_THRESHOLD)
2. 动作计划不完整或无效
3. 模型输出解析失败
"""

import logging
from typing import Dict, Any

from nova_executor.types import ExecutionState, NodeName, HilTriggerReason
from nova_executor.config import get_settings
from nova_executor.adapters import HilTicketAdapter

logger = logging.getLogger(__name__)
settings = get_settings()


async def check_hil_node(state: ExecutionState) -> Dict[str, Any]:
    """
    check_hil 节点执行函数

    评估置信度，决定是否触发 HIL

    Args:
        state: 当前执行状态

    Returns:
        状态更新字典
    """
    logger.info(f"[CheckHil] 检查 HIL: {state.instance_id}")

    # 检查是否有动作计划
    if not state.planned_action:
        logger.warning("[CheckHil] 无动作计划，触发 HIL")
        return await _trigger_hil(
            state,
            HilTriggerReason.PARSE_FAILURE,
            "No planned action"
        )

    # 检查置信度
    if state.planned_action.confidence < settings.hil_confidence_threshold:
        logger.warning(
            f"[CheckHil] 置信度 {state.planned_action.confidence} "
            f"低于阈值 {settings.hil_confidence_threshold}，触发 HIL"
        )
        return await _trigger_hil(
            state,
            HilTriggerReason.LOW_CONFIDENCE,
            f"Low confidence: {state.planned_action.confidence}"
        )

    # 检查动作有效性
    if not _is_valid_action(state.planned_action):
        logger.warning("[CheckHil] 动作无效，触发 HIL")
        return await _trigger_hil(
            state,
            HilTriggerReason.UNKNOWN_ELEMENT,
            "Invalid action"
        )

    # 置信度足够，直接执行
    logger.info("[CheckHil] 置信度足够，直接执行")

    return {
        "current_node": NodeName.CHECK_HIL,
        "hil_triggered": False,
        "error": None,
    }


def _is_valid_action(action) -> bool:
    """检查动作是否有效"""
    if not action:
        return False

    # 检查动作类型
    valid_types = ["click", "type", "navigate", "scroll", "wait"]
    if action.action_type.value not in valid_types:
        return False

    # click 类型必须有 selector
    if action.action_type.value == "click" and not action.selector:
        return False

    # type 类型必须有 selector 和 value
    if action.action_type.value == "type" and not (action.selector and action.value):
        return False

    # navigate 类型必须有 url
    if action.action_type.value == "navigate" and not action.url:
        return False

    return True


async def _trigger_hil(
    state: ExecutionState,
    reason: HilTriggerReason,
    message: str
) -> Dict[str, Any]:
    """触发 HIL"""
    try:
        # 创建 HIL 工单
        hil_adapter = HilTicketAdapter()
        await hil_adapter.create_ticket(
            instance_id=state.instance_id,
            tenant_id=state.tenant_id,
            step_no=state.step_count,
            reason=f"{reason.value}: {message}",
            planned_action=state.planned_action,
            screenshot=state.last_screenshot,
        )
        logger.info(f"[CheckHil] HIL 工单已创建: {reason.value}")
    except Exception as e:
        logger.error(f"[CheckHil] 创建 HIL 工单失败: {e}")

    return {
        "current_node": NodeName.WAITING_HIL,
        "hil_triggered": True,
        "hil_reason": reason,
        "error": message,
    }

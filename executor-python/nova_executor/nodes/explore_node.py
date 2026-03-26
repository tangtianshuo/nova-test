"""
explore 节点 - 探索节点
========================

探索阶段，负责：
1. 分析当前页面状态
2. 使用 Vision 模型生成动作计划
3. 产出 planned_action

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求
- 使用 Fara-7B 作为视觉推理大脑
"""

import logging
from typing import Dict, Any

from nova_executor.types import ExecutionState, NodeName, PlannedAction
from nova_executor.adapters import VisionAdapter

logger = logging.getLogger(__name__)


async def explore_node(state: ExecutionState) -> Dict[str, Any]:
    """
    explore 节点执行函数

    调用 Vision 模型分析当前页面，生成动作计划

    Args:
        state: 当前执行状态

    Returns:
        状态更新字典
    """
    logger.info(f"[Explore] 探索实例: {state.instance_id}, 步骤: {state.step_count}")

    try:
        # 调用 Vision 适配器分析页面
        vision = VisionAdapter()
        planned_action = await vision.analyze_page(
            screenshot=state.last_screenshot or "",
            instance_id=state.instance_id,
            target_url=state.target_url,
        )

        logger.info(
            f"[Explore] 动作计划: {planned_action.action_type.value}, "
            f"置信度: {planned_action.confidence}"
        )

        # 返回状态更新
        return {
            "current_node": NodeName.EXPLORE,
            "planned_action": planned_action,
            "hil_triggered": False,
            "error": None,
        }

    except Exception as e:
        logger.exception(f"[Explore] 探索失败: {e}")
        return {
            "current_node": NodeName.EXPLORE,
            "planned_action": None,
            "hil_triggered": True,
            "error": f"Explore failed: {str(e)}",
        }

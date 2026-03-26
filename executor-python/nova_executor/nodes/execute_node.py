"""
execute 节点 - 执行节点
======================

执行阶段，负责：
1. 根据 planned_action 执行具体动作
2. 使用 Playwright 执行动作
3. 捕获执行结果和截图
4. 处理执行失败情况

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求
- 使用 Magentic-UI (Playwright) 执行浏览器动作
"""

import logging
from typing import Dict, Any

from nova_executor.types import ExecutionState, NodeName
from nova_executor.adapters import ExecutorAdapter

logger = logging.getLogger(__name__)


async def execute_node(state: ExecutionState) -> Dict[str, Any]:
    """
    execute 节点执行函数

    调用 Executor 适配器执行动作

    Args:
        state: 当前执行状态

    Returns:
        状态更新字典
    """
    logger.info(f"[Execute] 执行动作: {state.instance_id}")

    if not state.planned_action:
        logger.error("[Execute] 无动作计划")
        return {
            "current_node": NodeName.EXECUTE,
            "hil_triggered": True,
            "error": "No planned action",
        }

    try:
        # 调用 Executor 适配器执行动作
        executor = ExecutorAdapter()
        result = await executor.execute_action(
            instance_id=state.instance_id,
            action=state.planned_action,
            previous_screenshot=state.last_screenshot,
        )

        if not result.success:
            logger.warning(f"[Execute] 执行失败: {result.error}")
            return {
                "current_node": NodeName.EXECUTE,
                "last_screenshot": result.screenshot,
                "step_count": state.step_count + 1,
                "error": result.error,
            }

        logger.info("[Execute] 执行成功")

        return {
            "current_node": NodeName.EXECUTE,
            "last_screenshot": result.screenshot,
            "step_count": state.step_count + 1,
            "hil_triggered": False,
            "error": None,
        }

    except Exception as e:
        logger.exception(f"[Execute] 执行异常: {e}")
        return {
            "current_node": NodeName.EXECUTE,
            "hil_triggered": True,
            "error": f"Execute failed: {str(e)}",
        }

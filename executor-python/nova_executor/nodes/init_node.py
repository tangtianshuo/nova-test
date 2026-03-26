"""
init 节点 - 初始化节点
======================

初始化阶段，负责：
1. 初始化浏览器环境
2. 导航到目标页面
3. 生成初始截图
4. 设置初始状态

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求
"""

import logging
from typing import Dict, Any

from nova_executor.types import ExecutionState, NodeName
from nova_executor.sandbox import SandboxManager

logger = logging.getLogger(__name__)


async def init_node(state: ExecutionState) -> Dict[str, Any]:
    """
    init 节点执行函数

    Args:
        state: 当前执行状态

    Returns:
        状态更新字典
    """
    logger.info(f"[Init] 初始化实例: {state.instance_id}")

    try:
        # 创建沙箱
        sandbox = SandboxManager()
        await sandbox.create(
            instance_id=state.instance_id,
            target_url=state.target_url,
            headless=True
        )

        # 截图
        screenshot = await sandbox.screenshot(state.instance_id)

        logger.info(f"[Init] 初始化完成，截图大小: {len(screenshot) if screenshot else 0} bytes")

        # 返回状态更新
        return {
            "current_node": NodeName.INITIALIZED,
            "last_screenshot": screenshot,
            "step_count": 0,
            "hil_triggered": False,
            "error": None,
        }

    except Exception as e:
        logger.exception(f"[Init] 初始化失败: {e}")
        return {
            "current_node": NodeName.INIT,
            "hil_triggered": True,
            "error": f"Init failed: {str(e)}",
        }

"""
HIL 工单适配器
==============

处理 Human-in-the-Loop 工单

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求
"""

import logging
from typing import Optional
import httpx

from nova_executor.types import PlannedAction
from nova_executor.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class HilTicketAdapter:
    """
    HIL 工单适配器

    与后端 API 通信，创建和管理 HIL 工单
    """

    def __init__(self):
        self.api_base = settings.database_url.split("@")[-1].split("/")[0] if "@" in settings.database_url else "localhost:3000"
        self.api_base = f"http://{self.api_base.split(':')[0]}:3000"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def create_ticket(
        self,
        instance_id: str,
        tenant_id: str,
        step_no: int,
        reason: str,
        planned_action: Optional[PlannedAction],
        screenshot: Optional[str],
    ) -> str:
        """
        创建 HIL 工单

        Args:
            instance_id: 实例 ID
            tenant_id: 租户 ID
            step_no: 步骤编号
            reason: 触发原因
            planned_action: 计划动作
            screenshot: 截图

        Returns:
            工单 ID
        """
        logger.info(f"[HilTicket] 创建工单: instance={instance_id}, step={step_no}")

        try:
            # 构建请求
            payload = {
                "instance_id": instance_id,
                "step_no": step_no,
                "reason": reason,
                "risk_level": "HIGH" if planned_action and planned_action.confidence < 0.5 else "MEDIUM",
                "planned_action": planned_action.model_dump() if planned_action else None,
                "screenshot_url": None,  # 上传到 S3 后获得
            }

            # 调用 API
            response = await self.client.post(
                f"{self.api_base}/api/hil-tickets",
                json=payload
            )

            if response.status_code == 201:
                data = response.json()
                ticket_id = data.get("id", "")
                logger.info(f"[HilTicket] 工单创建成功: {ticket_id}")
                return ticket_id
            else:
                logger.warning(f"[HilTicket] 工单创建失败: {response.status_code}")
                return ""

        except Exception as e:
            logger.exception(f"[HilTicket] 创建工单异常: {e}")
            return ""

    async def get_ticket(self, ticket_id: str) -> Optional[dict]:
        """获取工单详情"""
        try:
            response = await self.client.get(f"{self.api_base}/api/hil-tickets/{ticket_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"[HilTicket] 获取工单失败: {e}")
            return None

    async def resolve_ticket(
        self,
        ticket_id: str,
        decision: str,
        human_feedback: Optional[str] = None,
        modified_action: Optional[dict] = None,
    ) -> bool:
        """
        解决 HIL 工单

        Args:
            ticket_id: 工单 ID
            decision: 决策 (APPROVED, REJECTED, MODIFIED)
            human_feedback: 人工反馈
            modified_action: 修改后的动作

        Returns:
            是否成功
        """
        logger.info(f"[HilTicket] 解决工单: {ticket_id}, decision={decision}")

        try:
            payload = {
                "decision": decision,
                "human_feedback": human_feedback,
                "modified_action": modified_action,
            }

            response = await self.client.patch(
                f"{self.api_base}/api/hil-tickets/{ticket_id}/resolve",
                json=payload
            )

            return response.status_code == 200

        except Exception as e:
            logger.exception(f"[HilTicket] 解决工单异常: {e}")
            return False

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

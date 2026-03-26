"""
HIL 工单服务
============

管理 Human-in-the-Loop 工单的生命周期

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum
import uuid

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class HilTicketStatus(str, Enum):
    """工单状态"""
    WAITING = "WAITING"  # 等待处理
    LOCKED = "LOCKED"    # 已被锁定（有人正在处理）
    RESOLVED = "RESOLVED"  # 已解决
    EXPIRED = "EXPIRED"    # 已过期
    CANCELLED = "CANCELLED"  # 已取消


class HilTicketDecision(str, Enum):
    """工单决策"""
    APPROVED = "APPROVED"  # 批准
    REJECTED = "REJECTED"  # 拒绝
    MODIFIED = "MODIFIED"  # 修改后批准


@dataclass
class HilTicket:
    """
    HIL 工单数据模型

    属性:
        id: 工单 ID
        instance_id: 实例 ID
        tenant_id: 租户 ID
        step_no: 步骤编号
        reason: 触发原因
        risk_level: 风险等级 (LOW, MEDIUM, HIGH, CRITICAL)
        status: 工单状态
        planned_action: 计划动作 (JSON)
        screenshot_url: 截图 URL
        locked_by: 锁定者用户 ID
        locked_at: 锁定时间
        resolved_by: 解决者用户 ID
        resolved_at: 解决时间
        decision: 决策结果
        human_feedback: 人工反馈
        modified_action: 修改后的动作
        created_at: 创建时间
        updated_at: 更新时间
        expires_at: 过期时间
    """
    id: str
    instance_id: str
    tenant_id: str
    step_no: int
    reason: str
    risk_level: str
    status: HilTicketStatus
    planned_action: Optional[dict] = None
    screenshot_url: Optional[str] = None
    locked_by: Optional[str] = None
    locked_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    decision: Optional[HilTicketDecision] = None
    human_feedback: Optional[str] = None
    modified_action: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


class HilTicketService:
    """
    HIL 工单服务

    功能：
    1. 创建工单
    2. 锁定/解锁工单
    3. 解决工单
    4. 查询工单
    """

    def __init__(self):
        # 内存存储（生产环境应使用数据库）
        self._tickets: dict[str, HilTicket] = {}
        # 锁管理: ticket_id -> {user_id, locked_at}
        self._locks: dict[str, dict] = {}
        self._lock_timeout = timedelta(minutes=30)  # 锁超时时间

    async def create_ticket(
        self,
        instance_id: str,
        tenant_id: str,
        step_no: int,
        reason: str,
        risk_level: str = "MEDIUM",
        planned_action: Optional[dict] = None,
        screenshot_url: Optional[str] = None,
        timeout_minutes: int = 30,
    ) -> HilTicket:
        """
        创建 HIL 工单

        Args:
            instance_id: 实例 ID
            tenant_id: 租户 ID
            step_no: 步骤编号
            reason: 触发原因
            risk_level: 风险等级
            planned_action: 计划动作
            screenshot_url: 截图 URL
            timeout_minutes: 超时时间（分钟）

        Returns:
            创建的工单
        """
        ticket_id = str(uuid.uuid4())

        ticket = HilTicket(
            id=ticket_id,
            instance_id=instance_id,
            tenant_id=tenant_id,
            step_no=step_no,
            reason=reason,
            risk_level=risk_level,
            status=HilTicketStatus.WAITING,
            planned_action=planned_action,
            screenshot_url=screenshot_url,
            expires_at=datetime.now() + timedelta(minutes=timeout_minutes),
        )

        self._tickets[ticket_id] = ticket
        logger.info(f"[HilTicket] 创建工单: {ticket_id}, instance={instance_id}, reason={reason}")

        return ticket

    async def get_ticket(self, ticket_id: str) -> Optional[HilTicket]:
        """获取工单"""
        return self._tickets.get(ticket_id)

    async def get_ticket_by_instance(self, instance_id: str) -> Optional[HilTicket]:
        """根据实例 ID 获取最新工单"""
        tickets = [t for t in self._tickets.values() if t.instance_id == instance_id]
        if not tickets:
            return None
        # 返回最新创建的
        return max(tickets, key=lambda t: t.created_at)

    async def lock_ticket(self, ticket_id: str, user_id: str) -> bool:
        """
        锁定工单

        Args:
            ticket_id: 工单 ID
            user_id: 用户 ID

        Returns:
            是否成功
        """
        ticket = self._tickets.get(ticket_id)
        if not ticket:
            logger.warning(f"[HilTicket] 工单不存在: {ticket_id}")
            return False

        if ticket.status != HilTicketStatus.WAITING:
            logger.warning(f"[HilTicket] 工单状态不允许锁定: {ticket_id}, status={ticket.status}")
            return False

        # 检查是否已被其他人锁定
        if ticket_id in self._locks:
            lock_info = self._locks[ticket_id]
            if lock_info["user_id"] != user_id:
                # 检查锁是否超时
                if datetime.now() - lock_info["locked_at"] < self._lock_timeout:
                    logger.warning(f"[HilTicket] 工单已被其他人锁定: {ticket_id}")
                    return False

        # 锁定工单
        ticket.status = HilTicketStatus.LOCKED
        ticket.locked_by = user_id
        ticket.locked_at = datetime.now()
        ticket.updated_at = datetime.now()

        self._locks[ticket_id] = {
            "user_id": user_id,
            "locked_at": datetime.now(),
        }

        logger.info(f"[HilTicket] 锁定工单: {ticket_id}, user={user_id}")
        return True

    async def unlock_ticket(self, ticket_id: str, user_id: str) -> bool:
        """
        解锁工单

        Args:
            ticket_id: 工单 ID
            user_id: 用户 ID

        Returns:
            是否成功
        """
        ticket = self._tickets.get(ticket_id)
        if not ticket:
            return False

        if ticket.locked_by != user_id:
            logger.warning(f"[HilTicket] 无权解锁: {ticket_id}, user={user_id}")
            return False

        ticket.status = HilTicketStatus.WAITING
        ticket.locked_by = None
        ticket.locked_at = None
        ticket.updated_at = datetime.now()

        self._locks.pop(ticket_id, None)

        logger.info(f"[HilTicket] 解锁工单: {ticket_id}")
        return True

    async def resolve_ticket(
        self,
        ticket_id: str,
        user_id: str,
        decision: HilTicketDecision,
        human_feedback: Optional[str] = None,
        modified_action: Optional[dict] = None,
    ) -> Optional[HilTicket]:
        """
        解决工单

        Args:
            ticket_id: 工单 ID
            user_id: 用户 ID
            decision: 决策
            human_feedback: 人工反馈
            modified_action: 修改后的动作（用于 MODIFIED 决策）

        Returns:
            解决后的工单
        """
        ticket = self._tickets.get(ticket_id)
        if not ticket:
            return None

        # 验证权限
        if ticket.status == HilTicketStatus.LOCKED and ticket.locked_by != user_id:
            logger.warning(f"[HilTicket] 无权解决: {ticket_id}, user={user_id}")
            return None

        # 更新工单
        ticket.status = HilTicketStatus.RESOLVED
        ticket.resolved_by = user_id
        ticket.resolved_at = datetime.now()
        ticket.updated_at = datetime.now()
        ticket.decision = decision
        ticket.human_feedback = human_feedback
        ticket.modified_action = modified_action

        # 清除锁
        self._locks.pop(ticket_id, None)

        logger.info(f"[HilTicket] 解决工单: {ticket_id}, decision={decision.value}")

        return ticket

    async def cancel_ticket(self, ticket_id: str) -> bool:
        """
        取消工单

        Args:
            ticket_id: 工单 ID

        Returns:
            是否成功
        """
        ticket = self._tickets.get(ticket_id)
        if not ticket:
            return False

        ticket.status = HilTicketStatus.CANCELLED
        ticket.updated_at = datetime.now()

        self._locks.pop(ticket_id, None)

        logger.info(f"[HilTicket] 取消工单: {ticket_id}")
        return True

    async def list_waiting_tickets(
        self,
        tenant_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[HilTicket]:
        """
        列出等待中的工单

        Args:
            tenant_id: 租户 ID（可选）
            limit: 返回数量限制

        Returns:
            工单列表
        """
        tickets = [
            t for t in self._tickets.values()
            if t.status == HilTicketStatus.WAITING
            and (tenant_id is None or t.tenant_id == tenant_id)
            and (t.expires_at is None or t.expires_at > datetime.now())
        ]

        # 按创建时间排序
        tickets.sort(key=lambda t: t.created_at, reverse=True)

        return tickets[:limit]

    async def cleanup_expired_tickets(self) -> int:
        """
        清理过期工单

        Returns:
            清理的工单数量
        """
        count = 0
        now = datetime.now()

        for ticket_id, ticket in list(self._tickets.items()):
            if (
                ticket.status == HilTicketStatus.WAITING
                and ticket.expires_at
                and ticket.expires_at < now
            ):
                ticket.status = HilTicketStatus.EXPIRED
                ticket.updated_at = now
                self._locks.pop(ticket_id, None)
                count += 1
                logger.info(f"[HilTicket] 工单已过期: {ticket_id}")

        return count


# 全局服务实例
hil_ticket_service = HilTicketService()

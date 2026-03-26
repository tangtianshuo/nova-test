"""
HIL 工单服务测试
================

验证 HIL 工单的生命周期管理
"""

import pytest
from datetime import datetime, timedelta

from nova_executor.hil.ticket_service import (
    HilTicketService,
    HilTicketStatus,
    HilTicketDecision,
)


@pytest.fixture
def service():
    """创建服务实例"""
    return HilTicketService()


class TestHilTicketCreation:
    """工单创建测试"""

    @pytest.mark.asyncio
    async def test_create_ticket(self, service):
        """验证创建工单"""
        ticket = await service.create_ticket(
            instance_id="instance-1",
            tenant_id="tenant-1",
            step_no=1,
            reason="Low confidence",
            risk_level="MEDIUM",
        )

        assert ticket.id is not None
        assert ticket.instance_id == "instance-1"
        assert ticket.status == HilTicketStatus.WAITING
        assert ticket.reason == "Low confidence"

    @pytest.mark.asyncio
    async def test_create_ticket_with_expiry(self, service):
        """验证创建带过期时间的工单"""
        ticket = await service.create_ticket(
            instance_id="instance-1",
            tenant_id="tenant-1",
            step_no=1,
            reason="Test",
            timeout_minutes=10,
        )

        assert ticket.expires_at is not None
        assert ticket.expires_at > datetime.now()


class TestHilTicketLocking:
    """工单锁定测试"""

    @pytest.mark.asyncio
    async def test_lock_ticket(self, service):
        """验证锁定工单"""
        ticket = await service.create_ticket(
            instance_id="instance-1",
            tenant_id="tenant-1",
            step_no=1,
            reason="Test",
        )

        success = await service.lock_ticket(ticket.id, "user-1")
        assert success is True

        locked_ticket = await service.get_ticket(ticket.id)
        assert locked_ticket.status == HilTicketStatus.LOCKED
        assert locked_ticket.locked_by == "user-1"

    @pytest.mark.asyncio
    async def test_unlock_ticket(self, service):
        """验证解锁工单"""
        ticket = await service.create_ticket(
            instance_id="instance-1",
            tenant_id="tenant-1",
            step_no=1,
            reason="Test",
        )

        await service.lock_ticket(ticket.id, "user-1")
        success = await service.unlock_ticket(ticket.id, "user-1")

        assert success is True
        unlocked_ticket = await service.get_ticket(ticket.id)
        assert unlocked_ticket.status == HilTicketStatus.WAITING

    @pytest.mark.asyncio
    async def test_cannot_lock_by_different_user(self, service):
        """验证不能被其他用户锁定"""
        ticket = await service.create_ticket(
            instance_id="instance-1",
            tenant_id="tenant-1",
            step_no=1,
            reason="Test",
        )

        await service.lock_ticket(ticket.id, "user-1")
        success = await service.lock_ticket(ticket.id, "user-2")

        assert success is False


class TestHilTicketResolution:
    """工单解决测试"""

    @pytest.mark.asyncio
    async def test_resolve_approved(self, service):
        """验证批准决策"""
        ticket = await service.create_ticket(
            instance_id="instance-1",
            tenant_id="tenant-1",
            step_no=1,
            reason="Test",
        )

        resolved = await service.resolve_ticket(
            ticket_id=ticket.id,
            user_id="user-1",
            decision=HilTicketDecision.APPROVED,
            human_feedback="OK",
        )

        assert resolved.status == HilTicketStatus.RESOLVED
        assert resolved.decision == HilTicketDecision.APPROVED
        assert resolved.human_feedback == "OK"

    @pytest.mark.asyncio
    async def test_resolve_rejected(self, service):
        """验证拒绝决策"""
        ticket = await service.create_ticket(
            instance_id="instance-1",
            tenant_id="tenant-1",
            step_no=1,
            reason="Test",
        )

        resolved = await service.resolve_ticket(
            ticket_id=ticket.id,
            user_id="user-1",
            decision=HilTicketDecision.REJECTED,
        )

        assert resolved.status == HilTicketStatus.RESOLVED
        assert resolved.decision == HilTicketDecision.REJECTED

    @pytest.mark.asyncio
    async def test_resolve_modified(self, service):
        """验证修改决策"""
        ticket = await service.create_ticket(
            instance_id="instance-1",
            tenant_id="tenant-1",
            step_no=1,
            reason="Test",
            planned_action={"action_type": "click", "selector": "#old"},
        )

        modified = await service.resolve_ticket(
            ticket_id=ticket.id,
            user_id="user-1",
            decision=HilTicketDecision.MODIFIED,
            human_feedback="Use different selector",
            modified_action={"selector": "#new"},
        )

        assert modified.status == HilTicketStatus.RESOLVED
        assert modified.decision == HilTicketDecision.MODIFIED
        assert modified.modified_action == {"selector": "#new"}


class TestHilTicketQuery:
    """工单查询测试"""

    @pytest.mark.asyncio
    async def test_list_waiting_tickets(self, service):
        """验证列出等待中的工单"""
        # 创建多个工单
        await service.create_ticket(
            instance_id="instance-1",
            tenant_id="tenant-1",
            step_no=1,
            reason="Test 1",
        )
        await service.create_ticket(
            instance_id="instance-2",
            tenant_id="tenant-1",
            step_no=1,
            reason="Test 2",
        )

        tickets = await service.list_waiting_tickets(tenant_id="tenant-1")

        assert len(tickets) == 2

    @pytest.mark.asyncio
    async def test_get_ticket_by_instance(self, service):
        """验证根据实例获取工单"""
        ticket1 = await service.create_ticket(
            instance_id="instance-1",
            tenant_id="tenant-1",
            step_no=1,
            reason="Test 1",
        )
        await service.create_ticket(
            instance_id="instance-1",
            tenant_id="tenant-1",
            step_no=2,
            reason="Test 2",
        )

        latest = await service.get_ticket_by_instance("instance-1")
        assert latest.step_no == 2  # 最新的是 step_no=2

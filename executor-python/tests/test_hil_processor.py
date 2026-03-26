"""
HIL 处理器测试
==============

验证 HIL 决策处理逻辑
"""

import pytest
from datetime import datetime

from nova_executor.hil.processor import HilProcessor, ProcessedDecision
from nova_executor.hil.ticket_service import (
    HilTicketService,
    HilTicket,
    HilTicketStatus,
    HilTicketDecision,
)


@pytest.fixture
def service():
    """创建服务实例"""
    return HilTicketService()


@pytest.fixture
def processor(service):
    """创建处理器实例"""
    return HilProcessor(ticket_service=service)


class TestApproveDecision:
    """APPROVED 决策测试"""

    @pytest.mark.asyncio
    async def test_approve_uses_original_action(self, processor, service):
        """验证批准使用原计划动作"""
        # 创建工单
        ticket = await service.create_ticket(
            instance_id="instance-1",
            tenant_id="tenant-1",
            step_no=1,
            reason="Low confidence",
            planned_action={
                "action_type": "click",
                "selector": "#submit",
                "confidence": 0.6,
            },
        )

        # 处理批准决策
        result = await processor.process_decision(
            ticket=ticket,
            decision=HilTicketDecision.APPROVED,
            user_id="user-1",
            human_feedback="Looks good",
        )

        assert result.should_execute is True
        assert result.terminate_instance is False
        assert result.resume_from_node == "execute"
        assert result.action_to_execute is not None
        assert result.action_to_execute.confidence == 1.0  # 批准后置信度为 1.0


class TestRejectDecision:
    """REJECTED 决策测试"""

    @pytest.mark.asyncio
    async def test_reject_terminates_execution(self, processor, service):
        """验证拒绝终止执行"""
        ticket = await service.create_ticket(
            instance_id="instance-1",
            tenant_id="tenant-1",
            step_no=1,
            reason="High risk action",
        )

        result = await processor.process_decision(
            ticket=ticket,
            decision=HilTicketDecision.REJECTED,
            user_id="user-1",
            human_feedback="Too dangerous",
        )

        assert result.should_execute is False
        assert result.terminate_instance is True
        assert result.resume_from_node == "end"


class TestModifyDecision:
    """MODIFIED 决策测试"""

    @pytest.mark.asyncio
    async def test_modify_merges_selector(self, processor, service):
        """验证修改融合 selector"""
        ticket = await service.create_ticket(
            instance_id="instance-1",
            tenant_id="tenant-1",
            step_no=1,
            reason="Test",
            planned_action={
                "action_type": "click",
                "selector": "#old-selector",
                "value": "old-value",
            },
        )

        result = await processor.process_decision(
            ticket=ticket,
            decision=HilTicketDecision.MODIFIED,
            user_id="user-1",
            human_feedback="Use correct selector",
            modified_action={"selector": "#new-selector"},
        )

        assert result.should_execute is True
        assert result.action_to_execute is not None
        # selector 应该是用户修改的
        assert result.action_to_execute.selector == "#new-selector"
        # value 应该保持原计划的
        assert result.action_to_execute.value == "old-value"

    @pytest.mark.asyncio
    async def test_modify_merges_value(self, processor, service):
        """验证修改融合 value"""
        ticket = await service.create_ticket(
            instance_id="instance-1",
            tenant_id="tenant-1",
            step_no=1,
            reason="Test",
            planned_action={
                "action_type": "type",
                "selector": "input[name='q']",
                "value": "wrong input",
            },
        )

        result = await processor.process_decision(
            ticket=ticket,
            decision=HilTicketDecision.MODIFIED,
            user_id="user-1",
            human_feedback="Correct input",
            modified_action={"value": "correct input"},
        )

        assert result.should_execute is True
        assert result.action_to_execute.value == "correct input"
        # selector 保持不变
        assert result.action_to_execute.selector == "input[name='q']"

    @pytest.mark.asyncio
    async def test_modify_without_original_action(self, processor, service):
        """验证无原计划动作的修改"""
        ticket = await service.create_ticket(
            instance_id="instance-1",
            tenant_id="tenant-1",
            step_no=1,
            reason="No action plan",
            planned_action=None,
        )

        result = await processor.process_decision(
            ticket=ticket,
            decision=HilTicketDecision.MODIFIED,
            user_id="user-1",
            modified_action={
                "action_type": "click",
                "selector": "#new-btn",
            },
        )

        # 应该使用修改后的动作
        assert result.should_execute is True
        assert result.action_to_execute.selector == "#new-btn"


class TestResumeContext:
    """恢复上下文测试"""

    @pytest.mark.asyncio
    async def test_build_resume_context(self, processor, service):
        """验证构建恢复上下文"""
        ticket = await service.create_ticket(
            instance_id="instance-1",
            tenant_id="tenant-1",
            step_no=1,
            reason="Test",
        )

        # 先解决工单
        resolved = await service.resolve_ticket(
            ticket_id=ticket.id,
            user_id="user-1",
            decision=HilTicketDecision.APPROVED,
        )

        # 处理决策
        decision = ProcessedDecision(
            should_execute=True,
            action_to_execute=None,
            resume_from_node="execute",
            terminate_instance=False,
        )

        context = processor.build_resume_context(resolved, decision)

        assert context["ticket_id"] == ticket.id
        assert context["instance_id"] == "instance-1"
        assert context["should_execute"] is True
        assert context["terminate"] is False


class TestHILFlowScenarios:
    """HIL 流程场景测试"""

    @pytest.mark.asyncio
    async def test_low_confidence_approve_flow(self, processor, service):
        """低置信度 -> 批准 -> 继续执行"""
        # 场景：模型置信度 0.5，低于阈值触发 HIL
        ticket = await service.create_ticket(
            instance_id="instance-1",
            tenant_id="tenant-1",
            step_no=1,
            reason="Low confidence: 0.5",
            risk_level="MEDIUM",
            planned_action={
                "action_type": "click",
                "selector": "#submit",
                "confidence": 0.5,
            },
        )

        # 用户批准
        result = await processor.process_decision(
            ticket=ticket,
            decision=HilTicketDecision.APPROVED,
            user_id="user-1",
            human_feedback="Verified safe",
        )

        # 应该继续执行
        assert result.should_execute is True
        assert result.terminate_instance is False
        assert result.resume_from_node == "execute"

    @pytest.mark.asyncio
    async def test_high_risk_reject_flow(self, processor, service):
        """高风险 -> 拒绝 -> 终止"""
        # 场景：高风险操作，用户认为不安全
        ticket = await service.create_ticket(
            instance_id="instance-1",
            tenant_id="tenant-1",
            step_no=3,
            reason="Payment operation",
            risk_level="HIGH",
            planned_action={
                "action_type": "type",
                "selector": "#card-number",
                "value": "4111111111111111",
            },
        )

        # 用户拒绝
        result = await processor.process_decision(
            ticket=ticket,
            decision=HilTicketDecision.REJECTED,
            user_id="user-1",
            human_feedback="Cannot input real card",
        )

        # 应该终止
        assert result.should_execute is False
        assert result.terminate_instance is True

    @pytest.mark.asyncio
    async def test_wrong_selector_modify_flow(self, processor, service):
        """错误 selector -> 修改 -> 继续执行"""
        # 场景：模型选择器错误，用户提供正确的
        ticket = await service.create_ticket(
            instance_id="instance-1",
            tenant_id="tenant-1",
            step_no=2,
            reason="Low confidence: 0.4",
            risk_level="MEDIUM",
            planned_action={
                "action_type": "click",
                "selector": ".btn-wrong",  # 错误的 selector
            },
        )

        # 用户修改 selector
        result = await processor.process_decision(
            ticket=ticket,
            decision=HilTicketDecision.MODIFIED,
            user_id="user-1",
            human_feedback="Use correct selector",
            modified_action={"selector": "#btn-primary"},
        )

        # 应该使用修改后的 selector 继续执行
        assert result.should_execute is True
        assert result.action_to_execute.selector == "#btn-primary"
        assert result.action_to_execute.confidence == 1.0

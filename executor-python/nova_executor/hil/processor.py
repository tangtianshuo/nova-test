"""
HIL 处理器
==========

处理 Human-in-the-Loop 决策的核心逻辑

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求

关键逻辑：
1. 决策类型判断与路由（approve/modify/reject）
2. modify 场景下的动作合并策略
3. 决策结果与原计划动作的融合规则
4. 执行恢复时的上下文重建
"""

import logging
from typing import Optional
from dataclasses import dataclass

from nova_executor.hil.ticket_service import (
    HilTicketService,
    HilTicket,
    HilTicketDecision,
    hil_ticket_service,
)
from nova_executor.types import ExecutionState, PlannedAction, ActionType
from nova_executor.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class ProcessedDecision:
    """
    处理后的决策结果

    属性:
        should_execute: 是否应该执行动作
        action_to_execute: 要执行的动作（None 表示终止）
        resume_from_node: 从哪个节点恢复执行
        terminate_instance: 是否终止实例
    """
    should_execute: bool
    action_to_execute: Optional[PlannedAction]
    resume_from_node: str
    terminate_instance: bool


class HilProcessor:
    """
    HIL 处理器

    核心职责：
    1. 处理三种决策：approve、reject、modify
    2. 融合人工决策与模型生成的原计划动作
    3. 确定执行恢复的节点
    4. 管理执行上下文重建
    """

    def __init__(self, ticket_service: Optional[HilTicketService] = None):
        self.ticket_service = ticket_service or hil_ticket_service

    async def process_decision(
        self,
        ticket: HilTicket,
        decision: HilTicketDecision,
        user_id: str,
        human_feedback: Optional[str] = None,
        modified_action: Optional[dict] = None,
    ) -> ProcessedDecision:
        """
        处理 HIL 决策

        这是 HIL 处理器的核心方法，根据不同的决策类型决定后续执行流程。

        Args:
            ticket: HIL 工单
            decision: 决策类型
            user_id: 用户 ID
            human_feedback: 人工反馈
            modified_action: 修改后的动作（用于 modify 决策）

        Returns:
            处理后的决策结果
        """
        logger.info(
            f"[HilProcessor] 处理决策: ticket={ticket.id}, "
            f"decision={decision.value}, user={user_id}"
        )

        # 解决工单
        resolved_ticket = await self.ticket_service.resolve_ticket(
            ticket_id=ticket.id,
            user_id=user_id,
            decision=decision,
            human_feedback=human_feedback,
            modified_action=modified_action,
        )

        if not resolved_ticket:
            logger.error(f"[HilProcessor] 工单解决失败: {ticket.id}")
            return ProcessedDecision(
                should_execute=False,
                action_to_execute=None,
                resume_from_node="end",
                terminate_instance=True,
            )

        # 根据决策类型处理
        if decision == HilTicketDecision.APPROVED:
            return self._process_approve(resolved_ticket)

        elif decision == HilTicketDecision.REJECTED:
            return self._process_reject(resolved_ticket)

        elif decision == HilTicketDecision.MODIFIED:
            return self._process_modify(resolved_ticket, modified_action)

        else:
            logger.warning(f"[HilProcessor] 未知决策类型: {decision}")
            return ProcessedDecision(
                should_execute=False,
                action_to_execute=None,
                resume_from_node="end",
                terminate_instance=True,
            )

    def _process_approve(self, ticket: HilTicket) -> ProcessedDecision:
        """
        处理 APPROVED 决策

        APPROVED 决策的处理逻辑：
        1. 直接使用原计划动作执行
        2. 跳过 check_hil 节点，从 execute 节点恢复
        3. 正常继续后续流程
        """
        logger.info(f"[HilProcessor] APPROVED: 使用原计划动作, ticket={ticket.id}")

        # 从原计划动作创建 PlannedAction
        planned_action = None
        if ticket.planned_action:
            planned_action = PlannedAction(
                action_type=ActionType(ticket.planned_action.get("action_type", "click")),
                selector=ticket.planned_action.get("selector"),
                value=ticket.planned_action.get("value"),
                confidence=1.0,  # 人工批准后置信度设为 1.0
                thought=f"Approved by human: {ticket.human_feedback or 'No feedback'}",
            )

        return ProcessedDecision(
            should_execute=True,
            action_to_execute=planned_action,
            resume_from_node="execute",  # 从 execute 节点恢复
            terminate_instance=False,
        )

    def _process_reject(self, ticket: HilTicket) -> ProcessedDecision:
        """
        处理 REJECTED 决策

        REJECTED 决策的处理逻辑：
        1. 不执行当前动作
        2. 终止实例
        3. 生成终止报告
        4. 记录拒绝原因
        """
        logger.info(f"[HilProcessor] REJECTED: 拒绝执行, ticket={ticket.id}")

        return ProcessedDecision(
            should_execute=False,
            action_to_execute=None,
            resume_from_node="end",
            terminate_instance=True,
        )

    def _process_modify(
        self,
        ticket: HilTicket,
        modified_action: Optional[dict],
    ) -> ProcessedDecision:
        """
        处理 MODIFIED 决策

        MODIFIED 决策的处理逻辑（需要详细中文注释）：
        1. 用户修改了原计划动作的参数
        2. 动作类型保持不变，只修改参数（如 selector、value）
        3. 融合规则：
           - 如果用户提供了新的 selector，使用用户的
           - 如果用户提供了新的 value，使用用户的
           - 其他字段保持原计划动作的值
        4. 人工修改后置信度设为 1.0
        5. 从 execute 节点恢复执行

        Args:
            ticket: HIL 工单
            modified_action: 用户修改后的动作

        Returns:
            处理后的决策结果
        """
        logger.info(
            f"[HilProcessor] MODIFIED: 修改动作参数, ticket={ticket.id}"
        )

        if not ticket.planned_action:
            # 如果没有原计划动作，使用修改后的动作
            if modified_action:
                planned_action = PlannedAction(
                    action_type=ActionType(modified_action.get("action_type", "click")),
                    selector=modified_action.get("selector"),
                    value=modified_action.get("value"),
                    url=modified_action.get("url"),
                    confidence=1.0,
                    thought=f"Modified by human: {ticket.human_feedback or 'No feedback'}",
                )
            else:
                # 错误情况：MODIFIED 决策但没有动作
                logger.error(f"[HilProcessor] MODIFIED 决策缺少修改后的动作: {ticket.id}")
                return ProcessedDecision(
                    should_execute=False,
                    action_to_execute=None,
                    resume_from_node="end",
                    terminate_instance=True,
                )
        else:
            # 融合原计划动作和修改后的动作
            # 融合规则：用户提供的字段优先，否则使用原计划
            original = ticket.planned_action

            planned_action = PlannedAction(
                # 动作类型必须保持不变
                action_type=ActionType(original.get("action_type", "click")),
                # Selector：用户修改优先
                selector=(
                    modified_action.get("selector")
                    if modified_action and modified_action.get("selector")
                    else original.get("selector")
                ),
                # Value：用户修改优先
                value=(
                    modified_action.get("value")
                    if modified_action and modified_action.get("value")
                    else original.get("value")
                ),
                # URL：用户修改优先
                url=(
                    modified_action.get("url")
                    if modified_action and modified_action.get("url")
                    else original.get("url")
                ),
                # 置信度：人工修改后设为最高
                confidence=1.0,
                # 思考链：记录修改原因
                thought=f"Modified by human: {ticket.human_feedback or 'No feedback'}",
            )

        logger.info(
            f"[HilProcessor] 动作融合完成: "
            f"type={planned_action.action_type}, "
            f"selector={planned_action.selector}, "
            f"value={planned_action.value}"
        )

        return ProcessedDecision(
            should_execute=True,
            action_to_execute=planned_action,
            resume_from_node="execute",  # 从 execute 节点恢复
            terminate_instance=False,
        )

    def build_resume_context(
        self,
        ticket: HilTicket,
        processed_decision: ProcessedDecision,
    ) -> dict:
        """
        构建执行恢复上下文

        用于在 HIL 决策后重建状态机执行上下文

        Args:
            ticket: HIL 工单
            processed_decision: 处理后的决策

        Returns:
            恢复上下文字典
        """
        return {
            "ticket_id": ticket.id,
            "instance_id": ticket.instance_id,
            "decision": processed_decision.resume_from_node,
            "should_execute": processed_decision.should_execute,
            "action": (
                processed_decision.action_to_execute.model_dump()
                if processed_decision.action_to_execute
                else None
            ),
            "terminate": processed_decision.terminate_instance,
            "feedback": ticket.human_feedback,
            "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
        }


# 全局处理器实例
hil_processor = HilProcessor()

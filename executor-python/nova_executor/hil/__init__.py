"""
HIL 模块
========

Human-in-the-Loop 人机协作模块
"""

from nova_executor.hil.ticket_service import (
    HilTicketService,
    HilTicketStatus,
    HilTicketDecision,
    HilTicket,
    hil_ticket_service,
)
from nova_executor.hil.processor import HilProcessor, ProcessedDecision
from nova_executor.hil.checkpoint_service import (
    WorkerCheckpointService,
    WorkerCheckpoint,
    CheckpointStatus,
    InterruptionReason,
    RecoveryValidationResult,
    worker_checkpoint_service,
)

__all__ = [
    "HilTicketService",
    "HilTicketStatus",
    "HilTicketDecision",
    "HilProcessor",
    "ProcessedDecision",
    "WorkerCheckpointService",
    "WorkerCheckpoint",
    "CheckpointStatus",
    "InterruptionReason",
    "RecoveryValidationResult",
    "worker_checkpoint_service",
    "hil_ticket_service",
]

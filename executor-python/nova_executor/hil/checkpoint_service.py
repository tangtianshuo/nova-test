"""
Worker Checkpoint 服务
=====================

提供 Worker 中断保存和恢复的核心功能

FE-05-06: Agent 接管恢复机制

功能：
1. 中断时保存执行上下文到数据库
2. 从 HIL 中断状态恢复到继续执行
3. 恢复时的状态验证
4. 多 Worker 环境下的锁管理
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid
import hashlib

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CheckpointStatus(str, Enum):
    """检查点状态"""
    INTERRUPTED = "INTERRUPTED"
    RECOVERED = "RECOVERED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class InterruptionReason(str, Enum):
    """中断原因"""
    HIL_TIMEOUT = "HIL_TIMEOUT"
    WORKER_SHUTDOWN = "WORKER_SHUTDOWN"
    NETWORK_ERROR = "NETWORK_ERROR"
    SANDBOX_ERROR = "SANDBOX_ERROR"
    MANUAL_PAUSE = "MANUAL_PAUSE"
    MAX_STEPS_REACHED = "MAX_STEPS_REACHED"
    UNKNOWN = "UNKNOWN"


@dataclass
class WorkerCheckpoint:
    """
    Worker 检查点数据模型

    属性:
        id: 检查点 ID
        instance_id: 实例 ID
        ticket_id: HIL 工单 ID（如果有）
        current_node: 当前节点名称
        step_count: 当前步骤数
        execution_state: 执行状态快照 (JSON)
        planned_action: 计划动作 (JSON)
        screenshot_data: 截图数据 (base64)
        worker_id: 工作器 ID
        interrupted_at: 中断时间
        interrupted_reason: 中断原因
        hil_triggered: 是否触发了 HIL
        last_error: 最后错误信息
        retry_count: 重试次数
        status: 检查点状态
        version: 版本号（用于乐观锁）
        metadata: 额外元数据
    """
    id: str
    instance_id: str
    ticket_id: Optional[str] = None
    current_node: str = "init"
    step_count: int = 0
    execution_state: Dict[str, Any] = field(default_factory=dict)
    planned_action: Optional[Dict[str, Any]] = None
    screenshot_data: Optional[str] = None
    worker_id: Optional[str] = None
    interrupted_at: datetime = field(default_factory=datetime.now)
    interrupted_reason: Optional[str] = None
    hil_triggered: bool = False
    last_error: Optional[str] = None
    retry_count: int = 0
    status: CheckpointStatus = CheckpointStatus.INTERRUPTED
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkerCheckpoint":
        """从字典创建检查点"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            instance_id=data["instance_id"],
            ticket_id=data.get("ticket_id"),
            current_node=data.get("current_node", "init"),
            step_count=data.get("step_count", 0),
            execution_state=data.get("execution_state", {}),
            planned_action=data.get("planned_action"),
            screenshot_data=data.get("screenshot_data"),
            worker_id=data.get("worker_id"),
            interrupted_at=data.get("interrupted_at", datetime.now()),
            interrupted_reason=data.get("interrupted_reason"),
            hil_triggered=data.get("hil_triggered", False),
            last_error=data.get("last_error"),
            retry_count=data.get("retry_count", 0),
            status=CheckpointStatus(data.get("status", "INTERRUPTED")),
            version=data.get("version", 1),
            metadata=data.get("metadata", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "instance_id": self.instance_id,
            "ticket_id": self.ticket_id,
            "current_node": self.current_node,
            "step_count": self.step_count,
            "execution_state": self.execution_state,
            "planned_action": self.planned_action,
            "screenshot_data": self.screenshot_data,
            "worker_id": self.worker_id,
            "interrupted_at": self.interrupted_at.isoformat() if isinstance(self.interrupted_at, datetime) else self.interrupted_at,
            "interrupted_reason": self.interrupted_reason,
            "hil_triggered": self.hil_triggered,
            "last_error": self.last_error,
            "retry_count": self.retry_count,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "version": self.version,
            "metadata": self.metadata,
        }


class RecoveryValidationResult(BaseModel):
    """恢复验证结果"""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    can_recover: bool = True
    requires_user_confirmation: bool = False


class WorkerCheckpointService:
    """
    Worker 检查点服务

    核心功能：
    1. 保存执行上下文到检查点
    2. 从检查点恢复执行
    3. 验证恢复状态
    4. 管理检查点生命周期
    """

    def __init__(self):
        self._checkpoints: Dict[str, WorkerCheckpoint] = {}
        self._locks: Dict[str, Dict[str, Any]] = {}
        self._lock_timeout = timedelta(minutes=30)
        self._checkpoint_max_age = timedelta(hours=24)

    async def save_checkpoint(
        self,
        instance_id: str,
        execution_state: Dict[str, Any],
        current_node: str,
        step_count: int,
        worker_id: Optional[str] = None,
        ticket_id: Optional[str] = None,
        planned_action: Optional[Dict[str, Any]] = None,
        screenshot_data: Optional[str] = None,
        interrupted_reason: Optional[str] = None,
        hil_triggered: bool = False,
        last_error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkerCheckpoint:
        """
        保存检查点

        Args:
            instance_id: 实例 ID
            execution_state: 执行状态
            current_node: 当前节点
            step_count: 步骤数
            worker_id: 工作器 ID
            ticket_id: HIL 工单 ID
            planned_action: 计划动作
            screenshot_data: 截图数据
            interrupted_reason: 中断原因
            hil_triggered: 是否触发 HIL
            last_error: 最后错误
            metadata: 额外元数据

        Returns:
            创建的检查点
        """
        existing_checkpoint = await self.get_checkpoint(instance_id)
        
        if existing_checkpoint:
            existing_checkpoint.current_node = current_node
            existing_checkpoint.step_count = step_count
            existing_checkpoint.execution_state = execution_state
            existing_checkpoint.planned_action = planned_action
            existing_checkpoint.screenshot_data = screenshot_data
            existing_checkpoint.worker_id = worker_id
            existing_checkpoint.ticket_id = ticket_id
            existing_checkpoint.interrupted_reason = interrupted_reason
            existing_checkpoint.hil_triggered = hil_triggered
            existing_checkpoint.last_error = last_error
            existing_checkpoint.interrupted_at = datetime.now()
            existing_checkpoint.metadata = metadata or {}
            existing_checkpoint.retry_count += 1
            existing_checkpoint.version += 1
            existing_checkpoint.status = CheckpointStatus.INTERRUPTED
            
            logger.info(
                f"[Checkpoint] 更新检查点: {existing_checkpoint.id}, "
                f"instance={instance_id}, node={current_node}, "
                f"version={existing_checkpoint.version}"
            )
            
            return existing_checkpoint

        checkpoint_id = str(uuid.uuid4())

        checkpoint = WorkerCheckpoint(
            id=checkpoint_id,
            instance_id=instance_id,
            ticket_id=ticket_id,
            current_node=current_node,
            step_count=step_count,
            execution_state=execution_state,
            planned_action=planned_action,
            screenshot_data=screenshot_data,
            worker_id=worker_id,
            interrupted_reason=interrupted_reason,
            hil_triggered=hil_triggered,
            last_error=last_error,
            metadata=metadata or {},
        )

        self._checkpoints[checkpoint_id] = checkpoint
        logger.info(
            f"[Checkpoint] 保存检查点: {checkpoint_id}, "
            f"instance={instance_id}, node={current_node}"
        )

        return checkpoint

    async def get_checkpoint(
        self,
        instance_id: str,
        must_be_valid: bool = False
    ) -> Optional[WorkerCheckpoint]:
        """
        获取检查点

        Args:
            instance_id: 实例 ID
            must_be_valid: 是否必须验证通过

        Returns:
            检查点或 None
        """
        checkpoints = [
            c for c in self._checkpoints.values()
            if c.instance_id == instance_id
        ]

        if not checkpoints:
            return None

        checkpoint = max(checkpoints, key=lambda c: c.version)

        if must_be_valid:
            validation = await self.validate_checkpoint(checkpoint)
            if not validation.is_valid:
                logger.warning(
                    f"[Checkpoint] 检查点验证失败: {checkpoint.id}, "
                    f"errors={validation.errors}"
                )
                return None

        return checkpoint

    async def get_pending_checkpoints(
        self,
        limit: int = 100,
        include_expired: bool = False
    ) -> List[WorkerCheckpoint]:
        """
        获取待处理的检查点

        Args:
            limit: 返回数量限制
            include_expired: 是否包含已过期的

        Returns:
            检查点列表
        """
        now = datetime.now()
        checkpoints = [
            c for c in self._checkpoints.values()
            if c.status == CheckpointStatus.INTERRUPTED
        ]

        if not include_expired:
            checkpoints = [
                c for c in checkpoints
                if now - c.interrupted_at < self._checkpoint_max_age
            ]

        checkpoints.sort(key=lambda c: c.interrupted_at)
        return checkpoints[:limit]

    async def validate_checkpoint(
        self,
        checkpoint: WorkerCheckpoint
    ) -> RecoveryValidationResult:
        """
        验证检查点是否可以恢复

        Args:
            checkpoint: 检查点

        Returns:
            验证结果
        """
        errors = []
        warnings = []

        if not checkpoint.execution_state:
            errors.append("执行状态为空")
        else:
            required_fields = ["instance_id", "tenant_id", "task_id"]
            for field in required_fields:
                if field not in checkpoint.execution_state:
                    errors.append(f"缺少必需字段: {field}")

        if checkpoint.instance_id not in [c.instance_id for c in self._checkpoints.values()]:
            errors.append("实例 ID 不存在于系统中")

        age = datetime.now() - checkpoint.interrupted_at
        if age > self._checkpoint_max_age:
            warnings.append(f"检查点已过期 ({age.days} 天)")

        if checkpoint.step_count < 0:
            errors.append("步骤数不能为负数")

        if checkpoint.retry_count >= 5:
            warnings.append("重试次数过多，可能存在持久性问题")

        return RecoveryValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            can_recover=len(errors) == 0,
            requires_user_confirmation=len(warnings) > 0,
        )

    async def acquire_recovery_lock(
        self,
        checkpoint_id: str,
        worker_id: str
    ) -> bool:
        """
        获取恢复锁

        Args:
            checkpoint_id: 检查点 ID
            worker_id: 工作器 ID

        Returns:
            是否成功获取锁
        """
        if checkpoint_id in self._locks:
            lock_info = self._locks[checkpoint_id]
            if lock_info["worker_id"] != worker_id:
                if datetime.now() - lock_info["acquired_at"] < self._lock_timeout:
                    logger.warning(
                        f"[Checkpoint] 检查点已被其他工作器锁定: "
                        f"{checkpoint_id}, worker={lock_info['worker_id']}"
                    )
                    return False

        self._locks[checkpoint_id] = {
            "worker_id": worker_id,
            "acquired_at": datetime.now(),
        }

        logger.info(f"[Checkpoint] 获取恢复锁: {checkpoint_id}, worker={worker_id}")
        return True

    async def release_recovery_lock(
        self,
        checkpoint_id: str,
        worker_id: str
    ) -> bool:
        """
        释放恢复锁

        Args:
            checkpoint_id: 检查点 ID
            worker_id: 工作器 ID

        Returns:
            是否成功释放锁
        """
        if checkpoint_id not in self._locks:
            return True

        lock_info = self._locks[checkpoint_id]
        if lock_info["worker_id"] != worker_id:
            logger.warning(
                f"[Checkpoint] 无权释放锁: {checkpoint_id}, "
                f"expected={lock_info['worker_id']}, got={worker_id}"
            )
            return False

        del self._locks[checkpoint_id]
        logger.info(f"[Checkpoint] 释放恢复锁: {checkpoint_id}")
        return True

    async def mark_as_recovered(
        self,
        checkpoint_id: str
    ) -> bool:
        """
        标记检查点已恢复

        Args:
            checkpoint_id: 检查点 ID

        Returns:
            是否成功
        """
        checkpoint = self._checkpoints.get(checkpoint_id)
        if not checkpoint:
            logger.error(f"[Checkpoint] 检查点不存在: {checkpoint_id}")
            return False

        checkpoint.status = CheckpointStatus.RECOVERED
        logger.info(f"[Checkpoint] 标记为已恢复: {checkpoint_id}")
        return True

    async def mark_as_failed(
        self,
        checkpoint_id: str,
        error: str
    ) -> bool:
        """
        标记检查点为失败

        Args:
            checkpoint_id: 检查点 ID
            error: 错误信息

        Returns:
            是否成功
        """
        checkpoint = self._checkpoints.get(checkpoint_id)
        if not checkpoint:
            logger.error(f"[Checkpoint] 检查点不存在: {checkpoint_id}")
            return False

        checkpoint.status = CheckpointStatus.FAILED
        checkpoint.last_error = error
        logger.info(f"[Checkpoint] 标记为失败: {checkpoint_id}, error={error}")
        return True

    async def cleanup_expired_checkpoints(self) -> int:
        """
        清理过期的检查点

        Returns:
            清理的检查点数量
        """
        now = datetime.now()
        expired_ids = [
            c.id for c in self._checkpoints.values()
            if c.status in [CheckpointStatus.RECOVERED, CheckpointStatus.FAILED]
            and now - c.interrupted_at > timedelta(days=7)
        ]

        for checkpoint_id in expired_ids:
            del self._checkpoints[checkpoint_id]

        logger.info(f"[Checkpoint] 清理过期检查点: {len(expired_ids)} 个")
        return len(expired_ids)

    async def build_recovery_context(
        self,
        checkpoint: WorkerCheckpoint
    ) -> Dict[str, Any]:
        """
        构建恢复上下文

        Args:
            checkpoint: 检查点

        Returns:
            恢复上下文
        """
        validation = await self.validate_checkpoint(checkpoint)

        return {
            "checkpoint_id": checkpoint.id,
            "instance_id": checkpoint.instance_id,
            "ticket_id": checkpoint.ticket_id,
            "current_node": checkpoint.current_node,
            "step_count": checkpoint.step_count,
            "execution_state": checkpoint.execution_state,
            "planned_action": checkpoint.planned_action,
            "screenshot_data": checkpoint.screenshot_data,
            "hil_triggered": checkpoint.hil_triggered,
            "last_error": checkpoint.last_error,
            "retry_count": checkpoint.retry_count,
            "interrupted_at": checkpoint.interrupted_at.isoformat() if isinstance(checkpoint.interrupted_at, datetime) else checkpoint.interrupted_at,
            "validation": {
                "is_valid": validation.is_valid,
                "can_recover": validation.can_recover,
                "requires_confirmation": validation.requires_user_confirmation,
                "warnings": validation.warnings,
            },
        }


worker_checkpoint_service = WorkerCheckpointService()

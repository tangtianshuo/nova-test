"""
Worker Checkpoint 服务测试
==========================

FE-05-06: Agent 接管恢复机制测试
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from nova_executor.hil.checkpoint_service import (
    WorkerCheckpointService,
    WorkerCheckpoint,
    CheckpointStatus,
    InterruptionReason,
    RecoveryValidationResult,
)


@pytest.fixture
def checkpoint_service():
    """创建检查点服务实例"""
    return WorkerCheckpointService()


@pytest.fixture
def sample_checkpoint_data():
    """创建示例检查点数据"""
    return {
        "instance_id": "test-instance-001",
        "current_node": "check_hil",
        "step_count": 3,
        "execution_state": {
            "instance_id": "test-instance-001",
            "tenant_id": "test-tenant-001",
            "task_id": "test-task-001",
            "target_url": "https://example.com",
            "current_node": "check_hil",
            "step_count": 3,
            "max_steps": 10,
            "planned_action": {
                "action_type": "click",
                "selector": "#submit",
                "confidence": 0.5,
            },
        },
        "planned_action": {
            "action_type": "click",
            "selector": "#submit",
            "confidence": 0.5,
        },
        "worker_id": "worker-001",
        "ticket_id": "ticket-001",
        "hil_triggered": True,
        "interrupted_reason": "HIL_TIMEOUT",
    }


class TestCheckpointCreation:
    """检查点创建测试"""

    @pytest.mark.asyncio
    async def test_save_checkpoint_creates_new_checkpoint(
        self,
        checkpoint_service,
        sample_checkpoint_data
    ):
        """验证保存检查点创建新检查点"""
        checkpoint = await checkpoint_service.save_checkpoint(
            instance_id=sample_checkpoint_data["instance_id"],
            execution_state=sample_checkpoint_data["execution_state"],
            current_node=sample_checkpoint_data["current_node"],
            step_count=sample_checkpoint_data["step_count"],
            worker_id=sample_checkpoint_data["worker_id"],
            ticket_id=sample_checkpoint_data["ticket_id"],
            planned_action=sample_checkpoint_data["planned_action"],
            hil_triggered=sample_checkpoint_data["hil_triggered"],
            interrupted_reason=sample_checkpoint_data["interrupted_reason"],
        )

        assert checkpoint is not None
        assert checkpoint.instance_id == sample_checkpoint_data["instance_id"]
        assert checkpoint.current_node == sample_checkpoint_data["current_node"]
        assert checkpoint.step_count == sample_checkpoint_data["step_count"]
        assert checkpoint.hil_triggered == sample_checkpoint_data["hil_triggered"]
        assert checkpoint.status == CheckpointStatus.INTERRUPTED

    @pytest.mark.asyncio
    async def test_save_checkpoint_with_screenshot(
        self,
        checkpoint_service
    ):
        """验证保存带截图的检查点"""
        screenshot_data = "base64_encoded_screenshot_data"
        
        checkpoint = await checkpoint_service.save_checkpoint(
            instance_id="test-instance-002",
            execution_state={"instance_id": "test-instance-002"},
            current_node="execute",
            step_count=5,
            screenshot_data=screenshot_data,
        )

        assert checkpoint.screenshot_data == screenshot_data


class TestCheckpointRetrieval:
    """检查点获取测试"""

    @pytest.mark.asyncio
    async def test_get_checkpoint_returns_latest_version(
        self,
        checkpoint_service,
        sample_checkpoint_data
    ):
        """验证获取检查点返回最新版本"""
        checkpoint1 = await checkpoint_service.save_checkpoint(
            instance_id=sample_checkpoint_data["instance_id"],
            execution_state=sample_checkpoint_data["execution_state"],
            current_node="check_hil",
            step_count=3,
        )
        
        initial_version = checkpoint1.version

        checkpoint2 = await checkpoint_service.save_checkpoint(
            instance_id=sample_checkpoint_data["instance_id"],
            execution_state=sample_checkpoint_data["execution_state"],
            current_node="execute",
            step_count=4,
        )

        retrieved = await checkpoint_service.get_checkpoint(
            sample_checkpoint_data["instance_id"]
        )

        assert retrieved is not None
        assert retrieved.current_node == "execute"
        assert retrieved.step_count == 4
        assert retrieved.version == initial_version + 1
        assert retrieved is checkpoint1

    @pytest.mark.asyncio
    async def test_get_nonexistent_checkpoint_returns_none(
        self,
        checkpoint_service
    ):
        """验证获取不存在的检查点返回 None"""
        retrieved = await checkpoint_service.get_checkpoint("nonexistent-instance")
        assert retrieved is None


class TestCheckpointValidation:
    """检查点验证测试"""

    @pytest.mark.asyncio
    async def test_validate_valid_checkpoint(
        self,
        checkpoint_service,
        sample_checkpoint_data
    ):
        """验证有效检查点验证通过"""
        checkpoint = await checkpoint_service.save_checkpoint(
            instance_id=sample_checkpoint_data["instance_id"],
            execution_state=sample_checkpoint_data["execution_state"],
            current_node=sample_checkpoint_data["current_node"],
            step_count=sample_checkpoint_data["step_count"],
        )

        validation = await checkpoint_service.validate_checkpoint(checkpoint)

        assert validation.is_valid is True
        assert validation.can_recover is True
        assert len(validation.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_checkpoint_missing_execution_state(
        self,
        checkpoint_service
    ):
        """验证缺少执行状态的检查点验证失败"""
        checkpoint = await checkpoint_service.save_checkpoint(
            instance_id="test-instance-003",
            execution_state={},
            current_node="init",
            step_count=0,
        )

        validation = await checkpoint_service.validate_checkpoint(checkpoint)

        assert validation.is_valid is False
        assert len(validation.errors) > 0
        assert any("执行状态为空" in error for error in validation.errors)

    @pytest.mark.asyncio
    async def test_validate_checkpoint_missing_required_fields(
        self,
        checkpoint_service
    ):
        """验证缺少必需字段的检查点验证失败"""
        checkpoint = await checkpoint_service.save_checkpoint(
            instance_id="test-instance-004",
            execution_state={"instance_id": "test-instance-004"},
            current_node="init",
            step_count=0,
        )

        validation = await checkpoint_service.validate_checkpoint(checkpoint)

        assert validation.is_valid is False
        assert any("tenant_id" in error for error in validation.errors)
        assert any("task_id" in error for error in validation.errors)

    @pytest.mark.asyncio
    async def test_validate_checkpoint_negative_step_count(
        self,
        checkpoint_service
    ):
        """验证负数步骤数检查点验证失败"""
        checkpoint = await checkpoint_service.save_checkpoint(
            instance_id="test-instance-005",
            execution_state={
                "instance_id": "test-instance-005",
                "tenant_id": "tenant-1",
                "task_id": "task-1",
            },
            current_node="init",
            step_count=-1,
        )

        validation = await checkpoint_service.validate_checkpoint(checkpoint)

        assert validation.is_valid is False
        assert any("步骤数不能为负数" in error for error in validation.errors)


class TestRecoveryLock:
    """恢复锁测试"""

    @pytest.mark.asyncio
    async def test_acquire_recovery_lock_success(
        self,
        checkpoint_service,
        sample_checkpoint_data
    ):
        """验证获取恢复锁成功"""
        checkpoint = await checkpoint_service.save_checkpoint(
            instance_id=sample_checkpoint_data["instance_id"],
            execution_state=sample_checkpoint_data["execution_state"],
            current_node=sample_checkpoint_data["current_node"],
            step_count=sample_checkpoint_data["step_count"],
        )

        acquired = await checkpoint_service.acquire_recovery_lock(
            checkpoint.id,
            "worker-002"
        )

        assert acquired is True

    @pytest.mark.asyncio
    async def test_acquire_recovery_lock_already_locked(
        self,
        checkpoint_service,
        sample_checkpoint_data
    ):
        """验证已被锁定的检查点获取锁失败"""
        checkpoint = await checkpoint_service.save_checkpoint(
            instance_id=sample_checkpoint_data["instance_id"],
            execution_state=sample_checkpoint_data["execution_state"],
            current_node=sample_checkpoint_data["current_node"],
            step_count=sample_checkpoint_data["step_count"],
        )

        await checkpoint_service.acquire_recovery_lock(checkpoint.id, "worker-001")
        acquired = await checkpoint_service.acquire_recovery_lock(
            checkpoint.id,
            "worker-002"
        )

        assert acquired is False

    @pytest.mark.asyncio
    async def test_release_recovery_lock_success(
        self,
        checkpoint_service,
        sample_checkpoint_data
    ):
        """验证释放恢复锁成功"""
        checkpoint = await checkpoint_service.save_checkpoint(
            instance_id=sample_checkpoint_data["instance_id"],
            execution_state=sample_checkpoint_data["execution_state"],
            current_node=sample_checkpoint_data["current_node"],
            step_count=sample_checkpoint_data["step_count"],
        )

        await checkpoint_service.acquire_recovery_lock(checkpoint.id, "worker-001")
        released = await checkpoint_service.release_recovery_lock(
            checkpoint.id,
            "worker-001"
        )

        assert released is True

        acquired = await checkpoint_service.acquire_recovery_lock(
            checkpoint.id,
            "worker-002"
        )
        assert acquired is True


class TestCheckpointStatus:
    """检查点状态测试"""

    @pytest.mark.asyncio
    async def test_mark_as_recovered(
        self,
        checkpoint_service,
        sample_checkpoint_data
    ):
        """验证标记为已恢复"""
        checkpoint = await checkpoint_service.save_checkpoint(
            instance_id=sample_checkpoint_data["instance_id"],
            execution_state=sample_checkpoint_data["execution_state"],
            current_node=sample_checkpoint_data["current_node"],
            step_count=sample_checkpoint_data["step_count"],
        )

        result = await checkpoint_service.mark_as_recovered(checkpoint.id)

        assert result is True
        updated = await checkpoint_service.get_checkpoint(
            sample_checkpoint_data["instance_id"]
        )
        assert updated.status == CheckpointStatus.RECOVERED

    @pytest.mark.asyncio
    async def test_mark_as_failed(
        self,
        checkpoint_service,
        sample_checkpoint_data
    ):
        """验证标记为失败"""
        checkpoint = await checkpoint_service.save_checkpoint(
            instance_id=sample_checkpoint_data["instance_id"],
            execution_state=sample_checkpoint_data["execution_state"],
            current_node=sample_checkpoint_data["current_node"],
            step_count=sample_checkpoint_data["step_count"],
        )

        error_message = "Execution failed due to timeout"
        result = await checkpoint_service.mark_as_failed(
            checkpoint.id,
            error_message
        )

        assert result is True
        updated = await checkpoint_service.get_checkpoint(
            sample_checkpoint_data["instance_id"]
        )
        assert updated.status == CheckpointStatus.FAILED
        assert updated.last_error == error_message


class TestPendingCheckpoints:
    """待处理检查点测试"""

    @pytest.mark.asyncio
    async def test_get_pending_checkpoints_returns_interrupted_only(
        self,
        checkpoint_service,
        sample_checkpoint_data
    ):
        """验证只返回中断状态的检查点"""
        checkpoint1 = await checkpoint_service.save_checkpoint(
            instance_id=sample_checkpoint_data["instance_id"],
            execution_state=sample_checkpoint_data["execution_state"],
            current_node=sample_checkpoint_data["current_node"],
            step_count=sample_checkpoint_data["step_count"],
        )

        checkpoint2 = await checkpoint_service.save_checkpoint(
            instance_id="test-instance-recovered",
            execution_state={"instance_id": "test-instance-recovered"},
            current_node="end",
            step_count=10,
        )
        await checkpoint_service.mark_as_recovered(checkpoint2.id)

        pending = await checkpoint_service.get_pending_checkpoints()

        assert len(pending) == 1
        assert pending[0].id == checkpoint1.id


class TestRecoveryContext:
    """恢复上下文测试"""

    @pytest.mark.asyncio
    async def test_build_recovery_context(
        self,
        checkpoint_service,
        sample_checkpoint_data
    ):
        """验证构建恢复上下文"""
        checkpoint = await checkpoint_service.save_checkpoint(
            instance_id=sample_checkpoint_data["instance_id"],
            execution_state=sample_checkpoint_data["execution_state"],
            current_node=sample_checkpoint_data["current_node"],
            step_count=sample_checkpoint_data["step_count"],
            planned_action=sample_checkpoint_data["planned_action"],
            hil_triggered=sample_checkpoint_data["hil_triggered"],
        )

        context = await checkpoint_service.build_recovery_context(checkpoint)

        assert context["instance_id"] == sample_checkpoint_data["instance_id"]
        assert context["current_node"] == sample_checkpoint_data["current_node"]
        assert context["step_count"] == sample_checkpoint_data["step_count"]
        assert context["hil_triggered"] == sample_checkpoint_data["hil_triggered"]
        assert context["validation"]["is_valid"] is True
        assert context["planned_action"] == sample_checkpoint_data["planned_action"]


class TestHILRecoveryScenario:
    """HIL 恢复场景测试"""

    @pytest.mark.asyncio
    async def test_hil_timeout_recovery_flow(
        self,
        checkpoint_service
    ):
        """测试 HIL 超时恢复流程"""
        instance_id = "hil-timeout-instance"

        checkpoint = await checkpoint_service.save_checkpoint(
            instance_id=instance_id,
            execution_state={
                "instance_id": instance_id,
                "tenant_id": "test-tenant",
                "task_id": "test-task",
                "current_node": "waiting_hil",
                "step_count": 5,
                "planned_action": {
                    "action_type": "click",
                    "selector": "#dangerous-action",
                    "confidence": 0.3,
                },
            },
            current_node="waiting_hil",
            step_count=5,
            hil_triggered=True,
            interrupted_reason="HIL_TIMEOUT",
        )

        validation = await checkpoint_service.validate_checkpoint(checkpoint)
        assert validation.is_valid is True
        assert validation.can_recover is True

        context = await checkpoint_service.build_recovery_context(checkpoint)
        assert context["hil_triggered"] is True
        assert context["current_node"] == "waiting_hil"

        await checkpoint_service.mark_as_recovered(checkpoint.id)
        updated = await checkpoint_service.get_checkpoint(instance_id)
        assert updated.status == CheckpointStatus.RECOVERED

    @pytest.mark.asyncio
    async def test_worker_shutdown_recovery_flow(
        self,
        checkpoint_service
    ):
        """测试工作器关闭恢复流程"""
        instance_id = "worker-shutdown-instance"

        checkpoint = await checkpoint_service.save_checkpoint(
            instance_id=instance_id,
            execution_state={
                "instance_id": instance_id,
                "tenant_id": "test-tenant",
                "task_id": "test-task",
                "current_node": "execute",
                "step_count": 3,
            },
            current_node="execute",
            step_count=3,
            worker_id="worker-001",
            interrupted_reason="WORKER_SHUTDOWN",
        )

        validation = await checkpoint_service.validate_checkpoint(checkpoint)
        assert validation.is_valid is True

        lock_acquired = await checkpoint_service.acquire_recovery_lock(
            checkpoint.id,
            "worker-002"
        )
        assert lock_acquired is True

        await checkpoint_service.release_recovery_lock(checkpoint.id, "worker-002")

    @pytest.mark.asyncio
    async def test_max_steps_recovery_flow(
        self,
        checkpoint_service
    ):
        """测试达到最大步骤数恢复流程"""
        instance_id = "max-steps-instance"

        checkpoint = await checkpoint_service.save_checkpoint(
            instance_id=instance_id,
            execution_state={
                "instance_id": instance_id,
                "tenant_id": "test-tenant",
                "task_id": "test-task",
                "current_node": "verify",
                "step_count": 10,
                "max_steps": 10,
            },
            current_node="verify",
            step_count=10,
            interrupted_reason="MAX_STEPS_REACHED",
        )

        validation = await checkpoint_service.validate_checkpoint(checkpoint)
        assert validation.is_valid is True
        assert validation.warnings == []


class TestCheckpointSerialization:
    """检查点序列化测试"""

    @pytest.mark.asyncio
    async def test_checkpoint_to_dict(
        self,
        checkpoint_service,
        sample_checkpoint_data
    ):
        """验证检查点转字典"""
        checkpoint = await checkpoint_service.save_checkpoint(
            instance_id=sample_checkpoint_data["instance_id"],
            execution_state=sample_checkpoint_data["execution_state"],
            current_node=sample_checkpoint_data["current_node"],
            step_count=sample_checkpoint_data["step_count"],
        )

        data = checkpoint.to_dict()

        assert data["instance_id"] == sample_checkpoint_data["instance_id"]
        assert data["current_node"] == sample_checkpoint_data["current_node"]
        assert isinstance(data["interrupted_at"], str)

    @pytest.mark.asyncio
    async def test_checkpoint_from_dict(
        self,
        checkpoint_service,
        sample_checkpoint_data
    ):
        """验证从字典创建检查点"""
        original = await checkpoint_service.save_checkpoint(
            instance_id=sample_checkpoint_data["instance_id"],
            execution_state=sample_checkpoint_data["execution_state"],
            current_node=sample_checkpoint_data["current_node"],
            step_count=sample_checkpoint_data["step_count"],
        )

        data = original.to_dict()
        restored = WorkerCheckpoint.from_dict(data)

        assert restored.instance_id == original.instance_id
        assert restored.current_node == original.current_node
        assert restored.step_count == original.step_count
        assert restored.execution_state == original.execution_state

/**
 * Worker 服务
 * 
 * 负责从 Redis 队列消费任务实例并启动状态机执行。
 * 这是 AaaS 执行面的入口点。
 * 
 * 工作流程：
 * 1. 启动时连接到 Redis 队列
 * 2. 监听 queue:agent_tasks 队列
 * 3. 收到任务后，创建 ExecutionContext 并启动状态机
 * 4. 状态机执行完成后，更新实例状态并清理资源
 * 5. FE-05-06: 实现 Agent 接管恢复机制
 */
import { taskQueue, AgentTaskMessage } from '../../queue';
import { SandboxManager } from './sandbox.manager';
import { ExecutionGraph, createExecutionGraph } from '../state_machine/graph';
import { instanceRepository } from '../../db/repositories';
import { workerCheckpointRepository } from '../../db/repositories/hil_ticket.repository';
import { InstanceStatus, ExecutionState } from '../types';
import { NodeName } from '../types';

const WORKER_ID = `worker-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

export class WorkerService {
  private sandboxManager: SandboxManager;
  private executionGraph: ExecutionGraph;
  private isRunning: boolean = false;

  constructor() {
    this.sandboxManager = new SandboxManager();
    this.executionGraph = createExecutionGraph();
  }

  /**
   * 启动 Worker 服务
   * 开始监听任务队列
   */
  async start(): Promise<void> {
    console.log('[Worker] 启动 Worker 服务...');
    this.isRunning = true;
    await this.recoverInterruptedTasks();
    await this.consumeTasks();
  }

  /**
   * 停止 Worker 服务
   */
  async stop(): Promise<void> {
    console.log('[Worker] 停止 Worker 服务...');
    this.isRunning = false;
    await this.sandboxManager.cleanupAll();
  }

  /**
   * 恢复被中断的任务
   * 
   * FE-05-06: 从数据库恢复中断的检查点
   */
  private async recoverInterruptedTasks(): Promise<void> {
    console.log('[Worker] 检查中断的任务...');
    
    try {
      const checkpoints = await workerCheckpointRepository.findPendingCheckpoints(50);
      
      for (const checkpoint of checkpoints) {
        console.log(`[Worker] 恢复中断任务: ${checkpoint.instanceId}`);
        await this.recoverFromCheckpoint(checkpoint);
      }
    } catch (error) {
      console.error('[Worker] 恢复中断任务失败:', error);
    }
  }

  /**
   * 从检查点恢复任务
   * 
   * @param checkpoint 检查点
   */
  private async recoverFromCheckpoint(checkpoint: any): Promise<void> {
    const { instanceId } = checkpoint;

    try {
      const lockAcquired = await this.acquireCheckpointLock(checkpoint.id);
      if (!lockAcquired) {
        console.log(`[Worker] 检查点已被其他工作器锁定: ${checkpoint.id}`);
        return;
      }

      await instanceRepository.updateStatus(instanceId, InstanceStatus.RUNNING);

      const instance = await instanceRepository.findById(instanceId);
      if (!instance) {
        throw new Error(`实例不存在: ${instanceId}`);
      }

      const recoveryState: ExecutionState = {
        instanceId,
        currentNode: checkpoint.currentNode as NodeName,
        stepCount: checkpoint.stepCount,
        maxSteps: 10,
        hilTriggered: checkpoint.hilTriggered,
      };

      const sandbox = await this.sandboxManager.createSandbox({
        instanceId,
        targetUrl: instance.task?.targetUrl || 'about:blank',
      });

      const checkpointData = checkpoint.executionState as any;
      if (checkpointData) {
        recoveryState.plannedAction = checkpointData.planned_action;
        recoveryState.lastScreenshot = checkpoint.screenshotData;
      }

      await this.executionGraph.execute(recoveryState, sandbox);

      await workerCheckpointRepository.markAsRecovered(checkpoint.id);
      await instanceRepository.updateStatus(instanceId, InstanceStatus.COMPLETED);
      
      console.log(`[Worker] 任务恢复完成: ${instanceId}`);
    } catch (error) {
      console.error(`[Worker] 任务恢复失败: ${instanceId}`, error);
      await workerCheckpointRepository.markAsFailed(
        checkpoint.id,
        error instanceof Error ? error.message : String(error)
      );
      await instanceRepository.updateStatus(instanceId, InstanceStatus.FAILED);
    } finally {
      await this.sandboxManager.destroySandbox(instanceId);
    }
  }

  /**
   * 获取检查点锁
   * 
   * @param checkpointId 检查点 ID
   * @returns 是否成功获取锁
   */
  private async acquireCheckpointLock(checkpointId: string): Promise<boolean> {
    try {
      const updated = await workerCheckpointRepository.updateWithOptimisticLock(
        checkpointId,
        { 
          workerId: WORKER_ID,
          status: 'LOCKED',
        },
        1
      );
      return updated !== null;
    } catch (error) {
      console.error('[Worker] 获取检查点锁失败:', error);
      return false;
    }
  }

  /**
   * 保存执行检查点
   * 
   * @param state 执行状态
   * @param interruptedReason 中断原因
   */
  async saveCheckpoint(
    state: ExecutionState,
    interruptedReason: string
  ): Promise<void> {
    try {
      const existingCheckpoint = await workerCheckpointRepository.findByInstanceId(
        state.instanceId
      );

      if (existingCheckpoint) {
        await workerCheckpointRepository.update(existingCheckpoint.id, {
          currentNode: state.currentNode,
          stepCount: state.stepCount,
          executionState: state as any,
          hilTriggered: state.hilTriggered,
          lastError: state.error,
          retryCount: (existingCheckpoint as any).retryCount + 1,
          interruptedReason,
          version: (existingCheckpoint as any).version + 1,
        });
      } else {
        await workerCheckpointRepository.create({
          instanceId: state.instanceId,
          currentNode: state.currentNode,
          stepCount: state.stepCount,
          executionState: state as any,
          plannedAction: state.plannedAction as any,
          workerId: WORKER_ID,
          interruptedReason,
          hilTriggered: state.hilTriggered,
          lastError: state.error,
          metadata: {
            maxSteps: state.maxSteps,
            retryCount: 0,
          },
        });
      }

      console.log(`[Worker] 保存检查点: ${state.instanceId}, node=${state.currentNode}`);
    } catch (error) {
      console.error(`[Worker] 保存检查点失败: ${state.instanceId}`, error);
    }
  }

  /**
   * 消费任务队列
   * 阻塞式等待新任务
   */
  private async consumeTasks(): Promise<void> {
    while (this.isRunning) {
      try {
        const task = await taskQueue.consumeTask(5);
        if (task) {
          console.log(`[Worker] 收到任务: ${task.instanceId}`);
          await this.processTask(task);
        }
      } catch (error) {
        console.error('[Worker] 消费任务失败:', error);
        await this.sleep(1000);
      }
    }
  }

  /**
   * 处理单个任务
   * 
   * @param task 任务消息
   */
  private async processTask(task: AgentTaskMessage): Promise<void> {
    const { instanceId, tenantId } = task;
    void tenantId;

    try {
      const checkpoint = await workerCheckpointRepository.findByInstanceId(instanceId);
      
      if (checkpoint && checkpoint.status === 'INTERRUPTED') {
        console.log(`[Worker] 从检查点恢复任务: ${instanceId}`);
        await this.recoverFromCheckpoint(checkpoint);
        return;
      }

      await instanceRepository.updateStatus(instanceId, InstanceStatus.RUNNING);

      const instance = await instanceRepository.findById(instanceId);
      if (!instance) {
        throw new Error(`实例不存在: ${instanceId}`);
      }

      const initialState: ExecutionState = {
        instanceId,
        currentNode: 'init',
        stepCount: 0,
        maxSteps: 10,
        hilTriggered: false,
      };

      const sandbox = await this.sandboxManager.createSandbox({
        instanceId,
        targetUrl: instance.task?.targetUrl || 'about:blank',
      });

      await this.executionGraph.execute(initialState, sandbox);

      await instanceRepository.updateStatus(instanceId, InstanceStatus.COMPLETED);
      console.log(`[Worker] 任务完成: ${instanceId}`);
    } catch (error) {
      console.error(`[Worker] 任务执行失败: ${instanceId}`, error);
      await this.saveCheckpoint(
        {
          instanceId,
          currentNode: 'error',
          stepCount: 0,
          maxSteps: 10,
          error: error instanceof Error ? error.message : String(error),
        },
        'EXECUTION_ERROR'
      );
      await instanceRepository.updateStatus(instanceId, InstanceStatus.FAILED);
    } finally {
      await this.sandboxManager.destroySandbox(instanceId);
    }
  }

  /**
   * 休眠辅助函数
   */
  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

export const workerService = new WorkerService();
export default workerService;

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
 */
import { taskQueue, AgentTaskMessage } from '../../queue';
import { SandboxManager } from './sandbox.manager';
import { ExecutionGraph, createExecutionGraph } from '../state_machine/graph';
import { instanceRepository } from '../../db/repositories';
import { InstanceStatus, ExecutionState } from '../types';

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
      // 更新实例状态为运行中
      await instanceRepository.updateStatus(instanceId, InstanceStatus.RUNNING);

      // 获取任务配置
      const instance = await instanceRepository.findById(instanceId);
      if (!instance) {
        throw new Error(`实例不存在: ${instanceId}`);
      }

      // 初始化执行状态
      const initialState: ExecutionState = {
        instanceId,
        currentNode: 'init',
        stepCount: 0,
        maxSteps: 10,
        hilTriggered: false,
      };

      // 创建沙箱
      const sandbox = await this.sandboxManager.createSandbox({
        instanceId,
        targetUrl: 'about:blank',
      });

      // 执行状态机
      await this.executionGraph.execute(initialState, sandbox);

      // 执行完成，更新状态
      await instanceRepository.updateStatus(instanceId, InstanceStatus.COMPLETED);
      console.log(`[Worker] 任务完成: ${instanceId}`);
    } catch (error) {
      console.error(`[Worker] 任务执行失败: ${instanceId}`, error);
      await instanceRepository.updateStatus(instanceId, InstanceStatus.FAILED);
    } finally {
      // 清理沙箱资源
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

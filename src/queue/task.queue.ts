/**
 * 任务队列服务
 * 管理 Agent 任务队列和执行流 Pub/Sub
 */
import Redis from 'ioredis';
import { redis } from './redis.client';

export const QUEUE_KEYS = {
  AGENT_TASKS: 'queue:agent_tasks',
  AGENT_STREAM: (instanceId: string) => `pubsub:agent_stream:${instanceId}`,
} as const;

export interface AgentTaskMessage {
  taskId: string;
  tenantId: string;
  instanceId: string;
  timestamp: number;
}

export class TaskQueueService {
  /**
   * 发布任务到 Agent 任务队列
   */
  async publishTask(task: AgentTaskMessage): Promise<string> {
    const message = JSON.stringify(task);
    await redis.lpush(QUEUE_KEYS.AGENT_TASKS, message);
    return task.instanceId;
  }

  /**
   * 从队列获取任务（阻塞式）
   */
  async consumeTask(timeout: number = 0): Promise<AgentTaskMessage | null> {
    const result = await redis.brpop(QUEUE_KEYS.AGENT_TASKS, timeout);
    if (!result) return null;
    return JSON.parse(result[1]) as AgentTaskMessage;
  }

  /**
   * 发布执行流事件
   */
  async publishStreamEvent(instanceId: string, event: unknown): Promise<number> {
    const channel = QUEUE_KEYS.AGENT_STREAM(instanceId);
    return redis.publish(channel, JSON.stringify(event));
  }

  /**
   * 订阅执行流事件
   */
  async subscribeToStream(
    instanceId: string,
    callback: (event: unknown) => void
  ): Promise<void> {
    const subscriber = new Redis({
      host: process.env.REDIS_HOST || 'localhost',
      port: parseInt(process.env.REDIS_PORT || '6379', 10),
      password: process.env.REDIS_PASSWORD || undefined,
    });

    const channel = QUEUE_KEYS.AGENT_STREAM(instanceId);
    await subscriber.subscribe(channel);

    subscriber.on('message', (ch, message) => {
      if (ch === channel) {
        try {
          const event = JSON.parse(message);
          callback(event);
        } catch {
          console.error('[Redis] 解析事件失败:', message);
        }
      }
    });
  }

  /**
   * 获取队列长度
   */
  async getQueueLength(): Promise<number> {
    return redis.llen(QUEUE_KEYS.AGENT_TASKS);
  }
}

export const taskQueue = new TaskQueueService();
export default taskQueue;

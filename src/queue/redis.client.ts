/**
 * Redis 客户端单例
 * 用于任务队列和 Pub/Sub 通信
 */
import Redis from 'ioredis';

const globalForRedis = globalThis as unknown as {
  redis: Redis | undefined;
};

export function createRedisClient(): Redis {
  const redis = new Redis({
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT || '6379', 10),
    password: process.env.REDIS_PASSWORD || undefined,
    maxRetriesPerRequest: 3,
    enableReadyCheck: true,
    enableOfflineQueue: true,
    lazyConnect: true,
  });

  redis.on('error', (err) => {
    console.error('[Redis] 连接错误:', err.message);
  });

  redis.on('connect', () => {
    console.log('[Redis] 连接成功');
  });

  return redis;
}

export const redis = globalForRedis.redis ?? createRedisClient();

if (process.env.NODE_ENV !== 'production') {
  globalForRedis.redis = redis;
}

export default redis;

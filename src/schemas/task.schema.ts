/**
 * TaskSchema - 任务定义结构
 * 职责：定义自动化测试任务的基础配置和约束条件
 * @version 1.0.0
 */

import type { BaseSchema, SchemaVersion } from '../types/common.types';

/**
 * 任务约束条件
 * 定义任务执行的边界和限制
 */
export interface TaskConstraints {
  max_steps: number;
  forbidden_domains: string[];
  timeout_seconds?: number;
  retry_count?: number;
}

/**
 * TaskSchema 接口定义
 * 完整的任务配置结构
 */
export interface TaskSchema extends BaseSchema {
  schema_version: SchemaVersion;
  task_id: string;
  name: string;
  url: string;
  objective: string;
  constraints: TaskConstraints;
  tags?: string[];
  metadata?: Record<string, unknown>;
}

/**
 * 创建默认 TaskSchema 的工厂函数
 * @param overrides - 部分字段覆盖
 * @returns 完整的 TaskSchema 对象
 */
export function createTaskSchema(overrides: Partial<Omit<TaskSchema, 'schema_version' | 'created_at' | 'updated_at'>>): TaskSchema {
  const now = new Date().toISOString();
  return {
    schema_version: '1.0.0',
    created_at: now,
    updated_at: now,
    tenant_id: '',
    task_id: '',
    name: '',
    url: '',
    objective: '',
    constraints: {
      max_steps: 18,
      forbidden_domains: [],
    },
    ...overrides,
  };
}

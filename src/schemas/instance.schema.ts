/**
 * InstanceSchema - 实例运行时结构
 * 职责：定义任务执行实例的运行时状态和历史记录
 * @version 1.0.0
 */

import type { BaseSchema, ExecutionStatus, SchemaVersion, Timestamp } from '../types/common.types';

/**
 * InstanceSchema 接口定义
 * 完整的实例运行时结构
 */
export interface InstanceSchema extends BaseSchema {
  schema_version: SchemaVersion;
  instance_id: string;
  task_id: string;
  status: ExecutionStatus;
  started_at: Timestamp | null;
  completed_at: Timestamp | null;
  step_count: number;
  hil_count: number;
  defect_count: number;
  error_message?: string | null;
  metadata?: Record<string, unknown>;
}

/**
 * 创建默认 InstanceSchema 的工厂函数
 * @param overrides - 部分字段覆盖
 * @returns 完整的 InstanceSchema 对象
 */
export function createInstanceSchema(overrides: Partial<Omit<InstanceSchema, 'schema_version' | 'created_at' | 'updated_at'>>): InstanceSchema {
  const now = new Date().toISOString();
  return {
    schema_version: '1.0.0',
    created_at: now,
    updated_at: now,
    tenant_id: '',
    instance_id: '',
    task_id: '',
    status: 'PENDING',
    started_at: null,
    completed_at: null,
    step_count: 0,
    hil_count: 0,
    defect_count: 0,
    ...overrides,
  };
}

/**
 * ActionSchema - Vision 输出/Executor 输入结构
 * 职责：定义视觉感知模型输出的动作结构，供执行器解析和执行
 * @version 1.0.0
 */

import type { BaseSchema, SchemaVersion, Timestamp, BoundingBox, ActionType, Confidence } from '../types/common.types';

/**
 * ActionSchema 接口定义
 * Vision 模型输出的完整动作结构
 */
export interface ActionSchema extends BaseSchema {
  schema_version: SchemaVersion;
  action_id: string;
  instance_id: string;
  step_no: number;
  thought: string;
  action_type: ActionType;
  target: {
    selector?: string | null;
    x?: number | null;
    y?: number | null;
    bbox?: BoundingBox | null;
  };
  params: Record<string, unknown>;
  confidence: Confidence;
  expected_result: string;
  candidates?: ActionCandidate[];
  generated_at: Timestamp;
  model_version?: string;
}

/**
 * 候选动作
 * 当置信度较低时，提供多个候选方案
 */
export interface ActionCandidate {
  action_type: ActionType;
  target: {
    selector?: string | null;
    x?: number | null;
    y?: number | null;
    bbox?: BoundingBox | null;
  };
  params: Record<string, unknown>;
  confidence: Confidence;
  reason: string;
}

/**
 * 创建默认 ActionSchema 的工厂函数
 * @param overrides - 部分字段覆盖
 * @returns 完整的 ActionSchema 对象
 */
export function createActionSchema(overrides: Partial<Omit<ActionSchema, 'schema_version' | 'created_at' | 'updated_at'>>): ActionSchema {
  const now = new Date().toISOString();
  return {
    schema_version: '1.0.0',
    created_at: now,
    updated_at: now,
    tenant_id: '',
    action_id: '',
    instance_id: '',
    step_no: 0,
    thought: '',
    action_type: 'wait',
    target: {},
    params: {},
    confidence: 0,
    expected_result: '',
    generated_at: now,
    ...overrides,
  };
}

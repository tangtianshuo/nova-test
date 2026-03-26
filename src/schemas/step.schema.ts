/**
 * StepSchema - 步骤执行结构
 * 职责：定义单个执行步骤的详细信息，包括动作、验证结果和标注数据
 * @version 1.0.0
 */

import type { BaseSchema, SchemaVersion, Timestamp, BoundingBox, Point, ActionType } from '../types/common.types';

/**
 * 步骤动作定义
 * Vision 模型输出的动作结构
 */
export interface StepAction {
  thought: string;
  action_type: ActionType;
  target: {
    selector?: string | null;
    x?: number | null;
    y?: number | null;
    bbox?: BoundingBox | null;
  };
  params: Record<string, unknown>;
  confidence: number;
  expected_result: string;
}

/**
 * 验证结果
 * 执行后的断言检查结果
 */
export interface StepVerify {
  is_success: boolean;
  is_defect: boolean;
  message: string;
  details?: Record<string, unknown>;
}

/**
 * 标注层数据
 * 用于绘制截图上的视觉标注
 */
export interface StepOverlay {
  base_w: number;
  base_h: number;
  boxes: BoundingBox[];
  point?: Point | null;
}

/**
 * StepSchema 接口定义
 * 完整的步骤执行结构
 */
export interface StepSchema extends BaseSchema {
  schema_version: SchemaVersion;
  step_id: string;
  instance_id: string;
  step_no: number;
  node: 'init' | 'explore' | 'execute' | 'verify' | 'check_hil';
  screenshot_url: string;
  overlay: StepOverlay | null;
  action: StepAction;
  verify: StepVerify | null;
  executed_at: Timestamp;
  duration_ms: number;
}

/**
 * 创建默认 StepSchema 的工厂函数
 * @param overrides - 部分字段覆盖
 * @returns 完整的 StepSchema 对象
 */
export function createStepSchema(overrides: Partial<Omit<StepSchema, 'schema_version' | 'created_at' | 'updated_at'>>): StepSchema {
  const now = new Date().toISOString();
  return {
    schema_version: '1.0.0',
    created_at: now,
    updated_at: now,
    tenant_id: '',
    step_id: '',
    instance_id: '',
    step_no: 0,
    node: 'init',
    screenshot_url: '',
    overlay: null,
    action: {
      thought: '',
      action_type: 'wait',
      target: {},
      params: {},
      confidence: 0,
      expected_result: '',
    },
    verify: null,
    executed_at: now,
    duration_ms: 0,
    ...overrides,
  };
}

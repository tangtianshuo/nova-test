/**
 * EventSchema - WS 推流事件结构
 * 职责：定义 WebSocket 推送的事件格式，用于实时同步实例状态和步骤更新
 * @version 1.0.0
 */

import type { BaseSchema, SchemaVersion, Timestamp, ExecutionStatus } from '../types/common.types';
import type { StepAction, StepVerify, StepOverlay } from './step.schema';

/**
 * 事件类型枚举
 * 定义不同类型的推送事件
 */
export type EventType =
  | 'instance_started'
  | 'instance_completed'
  | 'instance_failed'
  | 'step_started'
  | 'step_completed'
  | 'action_proposed'
  | 'hil_triggered'
  | 'hil_resolved'
  | 'log_appended'
  | 'error_occurred';

/**
 * 事件数据载荷
 * 根据事件类型携带不同的数据
 */
export type EventPayload =
  | { type: 'instance_started'; instance_id: string; task_id: string }
  | { type: 'instance_completed'; instance_id: string; status: ExecutionStatus; verdict: 'SUCCESS' | 'FAILED' }
  | { type: 'instance_failed'; instance_id: string; error_message: string }
  | { type: 'step_started'; instance_id: string; step_no: number; node: string }
  | { type: 'step_completed'; instance_id: string; step_no: number; action: StepAction; verify: StepVerify | null }
  | { type: 'action_proposed'; instance_id: string; step_no: number; action: StepAction; overlay: StepOverlay | null }
  | { type: 'hil_triggered'; instance_id: string; ticket_id: string; reason: string; risk_level: 'LOW' | 'MEDIUM' | 'HIGH' }
  | { type: 'hil_resolved'; instance_id: string; ticket_id: string; decision: 'approve' | 'reject' | 'modify' }
  | { type: 'log_appended'; instance_id: string; level: 'INFO' | 'WARN' | 'ERROR'; message: string }
  | { type: 'error_occurred'; instance_id: string; error_code: string; error_message: string };

/**
 * EventSchema 接口定义
 * WebSocket 推送事件的完整结构
 */
export interface EventSchema extends BaseSchema {
  schema_version: SchemaVersion;
  event_id: string;
  event_type: EventType;
  instance_id: string;
  tenant_id: string;
  payload: EventPayload;
  timestamp: Timestamp;
  sequence_no: number;
}

/**
 * 创建默认 EventSchema 的工厂函数
 * @param overrides - 部分字段覆盖
 * @returns 完整的 EventSchema 对象
 */
export function createEventSchema(overrides: Partial<Omit<EventSchema, 'schema_version' | 'created_at' | 'updated_at'>>): EventSchema {
  const now = new Date().toISOString();
  return {
    schema_version: '1.0.0',
    created_at: now,
    updated_at: now,
    tenant_id: '',
    event_id: '',
    event_type: 'log_appended',
    instance_id: '',
    payload: { type: 'log_appended', instance_id: '', level: 'INFO', message: '' },
    timestamp: now,
    sequence_no: 0,
    ...overrides,
  };
}

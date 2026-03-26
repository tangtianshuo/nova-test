/**
 * HilTicketSchema - HIL 人工干预工单结构
 * 职责：定义人机介入工单的完整结构，包括触发原因、风险等级和决策结果
 * @version 1.0.0
 */

import type { BaseSchema, SchemaVersion, Timestamp, RiskLevel, HilDecision } from '../types/common.types';
import type { StepAction, StepOverlay } from './step.schema';

/**
 * HIL 工单状态
 */
export type HilTicketStatus = 'WAITING' | 'APPROVED' | 'REJECTED' | 'MODIFIED' | 'EXPIRED';

/**
 * HilTicketSchema 接口定义
 * 完整的 HIL 工单结构
 */
export interface HilTicketSchema extends BaseSchema {
  schema_version: SchemaVersion;
  ticket_id: string;
  instance_id: string;
  step_no: number;
  status: HilTicketStatus;
  trigger_reason: string;
  risk_level: RiskLevel;
  planned_action: StepAction;
  screenshot_url: string;
  overlay: StepOverlay | null;
  decision: HilDecision | null;
  modified_action: StepAction | null;
  decided_by: string | null;
  decided_at: Timestamp | null;
  expires_at: Timestamp | null;
  audit_trail: HilAuditEntry[];
}

/**
 * HIL 审计记录条目
 * 记录工单的生命周期事件
 */
export interface HilAuditEntry {
  timestamp: Timestamp;
  action: 'created' | 'viewed' | 'approved' | 'rejected' | 'modified' | 'expired';
  actor: string;
  details?: Record<string, unknown>;
}

/**
 * 创建默认 HilTicketSchema 的工厂函数
 * @param overrides - 部分字段覆盖
 * @returns 完整的 HilTicketSchema 对象
 */
export function createHilTicketSchema(overrides: Partial<Omit<HilTicketSchema, 'schema_version' | 'created_at' | 'updated_at'>>): HilTicketSchema {
  const now = new Date().toISOString();
  const expiresAt = new Date(Date.now() + 30 * 60 * 1000).toISOString();
  return {
    schema_version: '1.0.0',
    created_at: now,
    updated_at: now,
    tenant_id: '',
    ticket_id: '',
    instance_id: '',
    step_no: 0,
    status: 'WAITING',
    trigger_reason: '',
    risk_level: 'MEDIUM',
    planned_action: {
      thought: '',
      action_type: 'wait',
      target: {},
      params: {},
      confidence: 0,
      expected_result: '',
    },
    screenshot_url: '',
    overlay: null,
    decision: null,
    modified_action: null,
    decided_by: null,
    decided_at: null,
    expires_at: expiresAt,
    audit_trail: [],
    ...overrides,
  };
}

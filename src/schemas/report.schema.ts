/**
 * ReportSchema - 报告输出结构
 * 职责：定义执行报告的完整结构，包含摘要、缺陷列表和详细步骤
 * @version 1.0.0
 */

import type { BaseSchema, SchemaVersion, Timestamp, ExecutionStatus } from '../types/common.types';
import type { StepAction, StepVerify, StepOverlay } from './step.schema';

/**
 * 报告结论
 */
export type ReportVerdict = 'SUCCESS' | 'FAILED' | 'PARTIAL' | 'DRAFT';

/**
 * 缺陷记录
 * 记录执行过程中发现的问题
 */
export interface ReportDefect {
  step_no: number;
  title: string;
  detail: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  screenshot_url?: string;
  overlay?: StepOverlay | null;
  timestamp: Timestamp;
}

/**
 * 报告步骤摘要
 * 简化的步骤信息用于报告展示
 */
export interface ReportStepSummary {
  step_no: number;
  node: string;
  action: StepAction;
  verify: StepVerify | null;
  screenshot_url: string;
  overlay: StepOverlay | null;
  executed_at: Timestamp;
  duration_ms: number;
}

/**
 * 报告统计
 */
export interface ReportStatistics {
  total_steps: number;
  passed_steps: number;
  failed_steps: number;
  hil_count: number;
  defect_count: number;
  total_duration_ms: number;
  average_step_duration_ms: number;
}

/**
 * ReportSchema 接口定义
 * 完整的执行报告结构
 */
export interface ReportSchema extends BaseSchema {
  schema_version: SchemaVersion;
  report_id: string;
  instance_id: string;
  task_id: string;
  verdict: ReportVerdict;
  status: ExecutionStatus;
  summary: string;
  statistics: ReportStatistics;
  defects: ReportDefect[];
  steps: ReportStepSummary[];
  started_at: Timestamp;
  completed_at: Timestamp | null;
  generated_at: Timestamp;
  export_formats: ('JSON' | 'PDF' | 'EXCEL')[];
  metadata?: Record<string, unknown>;
}

/**
 * 创建默认 ReportSchema 的工厂函数
 * @param overrides - 部分字段覆盖
 * @returns 完整的 ReportSchema 对象
 */
export function createReportSchema(overrides: Partial<Omit<ReportSchema, 'schema_version' | 'created_at' | 'updated_at'>>): ReportSchema {
  const now = new Date().toISOString();
  return {
    schema_version: '1.0.0',
    created_at: now,
    updated_at: now,
    tenant_id: '',
    report_id: '',
    instance_id: '',
    task_id: '',
    verdict: 'DRAFT',
    status: 'PENDING',
    summary: '',
    statistics: {
      total_steps: 0,
      passed_steps: 0,
      failed_steps: 0,
      hil_count: 0,
      defect_count: 0,
      total_duration_ms: 0,
      average_step_duration_ms: 0,
    },
    defects: [],
    steps: [],
    started_at: now,
    completed_at: null,
    generated_at: now,
    export_formats: ['JSON'],
    ...overrides,
  };
}

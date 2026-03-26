/**
 * Schema 校验器模块
 * 职责：提供统一的 Schema 校验入口，支持正向校验和负向校验
 * @version 1.0.0
 */

import { z } from 'zod';
import { isVersionSupported, isValidVersionFormat } from './version.strategy';

export type SchemaType =
  | 'task'
  | 'instance'
  | 'step'
  | 'action'
  | 'event'
  | 'hil_ticket'
  | 'report';

export interface ValidationResult<T = unknown> {
  valid: boolean;
  errors: ValidationError[];
  data?: T;
}

export interface ValidationError {
  path: string;
  message: string;
  code: string;
}

const TaskSchemaZod = z.object({
  schema_version: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  tenant_id: z.string().min(1, 'tenant_id 不能为空'),
  task_id: z.string().min(1, 'task_id 不能为空'),
  name: z.string().min(1, 'name 不能为空'),
  url: z.string().url('url 必须是有效的 URL'),
  objective: z.string().min(1, 'objective 不能为空'),
  constraints: z.object({
    max_steps: z.number().int().min(1).max(100),
    forbidden_domains: z.array(z.string()),
    timeout_seconds: z.number().int().positive().optional(),
    retry_count: z.number().int().min(0).optional(),
  }),
  tags: z.array(z.string()).optional(),
  metadata: z.record(z.string(), z.unknown()).optional(),
});

const InstanceSchemaZod = z.object({
  schema_version: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  tenant_id: z.string().min(1, 'tenant_id 不能为空'),
  instance_id: z.string().min(1, 'instance_id 不能为空'),
  task_id: z.string().min(1, 'task_id 不能为空'),
  status: z.enum(['PENDING', 'RUNNING', 'PAUSED_HIL', 'SUCCESS', 'FAILED']),
  started_at: z.string().nullable(),
  completed_at: z.string().nullable(),
  step_count: z.number().int().min(0),
  hil_count: z.number().int().min(0),
  defect_count: z.number().int().min(0),
  error_message: z.string().nullable().optional(),
  metadata: z.record(z.string(), z.unknown()).optional(),
});

const StepSchemaZod = z.object({
  schema_version: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  tenant_id: z.string().min(1, 'tenant_id 不能为空'),
  step_id: z.string().min(1, 'step_id 不能为空'),
  instance_id: z.string().min(1, 'instance_id 不能为空'),
  step_no: z.number().int().positive(),
  node: z.enum(['init', 'explore', 'execute', 'verify', 'hil', 'end']),
  screenshot_url: z.string(),
  overlay: z.object({
    base_w: z.number().positive(),
    base_h: z.number().positive(),
    boxes: z.array(z.object({
      x: z.number(),
      y: z.number(),
      w: z.number().positive(),
      h: z.number().positive(),
    })),
    point: z.object({
      x: z.number(),
      y: z.number(),
    }).optional(),
  }).nullable(),
  action: z.object({
    thought: z.string(),
    action_type: z.enum(['click', 'type', 'scroll', 'wait', 'end']),
    target: z.object({
      selector: z.string().optional(),
      x: z.number().optional(),
      y: z.number().optional(),
      bbox: z.object({
        x: z.number(),
        y: z.number(),
        w: z.number().positive(),
        h: z.number().positive(),
      }).optional(),
    }),
    params: z.record(z.string(), z.unknown()),
    confidence: z.number().min(0).max(1),
    expected_result: z.string(),
  }),
  verify: z.object({
    is_success: z.boolean(),
    is_defect: z.boolean(),
    message: z.string(),
  }).nullable(),
  executed_at: z.string(),
  duration_ms: z.number().int().nonnegative(),
});

const ActionSchemaZod = z.object({
  schema_version: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  tenant_id: z.string().min(1, 'tenant_id 不能为空'),
  action_id: z.string().min(1, 'action_id 不能为空'),
  instance_id: z.string().min(1, 'instance_id 不能为空'),
  step_no: z.number().int().positive(),
  thought: z.string(),
  action_type: z.enum(['click', 'type', 'scroll', 'wait', 'end']),
  target: z.object({
    selector: z.string().optional(),
    x: z.number().optional(),
    y: z.number().optional(),
    bbox: z.object({
      x: z.number(),
      y: z.number(),
      w: z.number().positive(),
      h: z.number().positive(),
    }).optional(),
  }),
  params: z.record(z.string(), z.unknown()),
  confidence: z.number().min(0).max(1),
  expected_result: z.string(),
  candidates: z.array(z.object({
      thought: z.string(),
      action_type: z.enum(['click', 'type', 'scroll', 'wait', 'end']),
      target: z.object({
        selector: z.string().optional(),
        x: z.number().optional(),
        y: z.number().optional(),
      }),
      params: z.record(z.string(), z.unknown()),
      confidence: z.number().min(0).max(1),
    })).optional(),
  generated_at: z.string(),
  model_version: z.string(),
});

const EventSchemaZod = z.object({
  schema_version: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  tenant_id: z.string().min(1, 'tenant_id 不能为空'),
  event_id: z.string().min(1, 'event_id 不能为空'),
  event_type: z.enum([
    'instance_started',
    'instance_completed',
    'instance_failed',
    'step_started',
    'step_completed',
    'action_proposed',
    'hil_triggered',
    'hil_resolved',
    'log_appended',
    'error_occurred',
  ]),
  instance_id: z.string().min(1, 'instance_id 不能为空'),
  payload: z.record(z.string(), z.unknown()),
  timestamp: z.string(),
  sequence_no: z.number().int().nonnegative(),
});

const HilTicketSchemaZod = z.object({
  schema_version: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  tenant_id: z.string().min(1, 'tenant_id 不能为空'),
  ticket_id: z.string().min(1, 'ticket_id 不能为空'),
  instance_id: z.string().min(1, 'instance_id 不能为空'),
  step_no: z.number().int().positive(),
  status: z.enum(['WAITING', 'APPROVED', 'REJECTED', 'MODIFIED', 'EXPIRED']),
  reason: z.string().min(1, 'reason 不能为空'),
  risk_level: z.enum(['LOW', 'MEDIUM', 'HIGH']),
  planned_action: z.object({
    thought: z.string(),
    action_type: z.enum(['click', 'type', 'scroll', 'wait', 'end']),
    target: z.object({
      selector: z.string().optional(),
      x: z.number().optional(),
      y: z.number().optional(),
      bbox: z.object({
        x: z.number(),
        y: z.number(),
        w: z.number().positive(),
        h: z.number().positive(),
      }).optional(),
    }),
    params: z.record(z.string(), z.unknown()),
    confidence: z.number().min(0).max(1),
    expected_result: z.string(),
  }),
  screenshot_url: z.string(),
  overlay: z.object({
    base_w: z.number().positive(),
    base_h: z.number().positive(),
    boxes: z.array(z.object({
      x: z.number(),
      y: z.number(),
      w: z.number().positive(),
      h: z.number().positive(),
    })),
    point: z.object({
      x: z.number(),
      y: z.number(),
    }).optional(),
  }).nullable(),
  decision: z.enum(['approve', 'reject', 'modify']).nullable(),
  modified_action: z.record(z.string(), z.unknown()).nullable(),
  decided_by: z.string().nullable(),
  decided_at: z.string().nullable(),
  expires_at: z.string().nullable(),
  audit_trail: z.array(z.object({
      action: z.string(),
      actor: z.string(),
      timestamp: z.string(),
      details: z.record(z.string(), z.unknown()).optional(),
    })),
});

const ReportSchemaZod = z.object({
  schema_version: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  tenant_id: z.string().min(1, 'tenant_id 不能为空'),
  report_id: z.string().min(1, 'report_id 不能为空'),
  instance_id: z.string().min(1, 'instance_id 不能为空'),
  task_id: z.string().min(1, 'task_id 不能为空'),
  verdict: z.enum(['SUCCESS', 'FAILED', 'PARTIAL', 'DRAFT']),
  status: z.enum(['PENDING', 'RUNNING', 'PAUSED_HIL', 'SUCCESS', 'FAILED']),
  summary: z.string(),
  statistics: z.object({
    total_steps: z.number().int().min(0),
    passed_steps: z.number().int().min(0),
    failed_steps: z.number().int().min(0),
    hil_count: z.number().int().min(0),
    defect_count: z.number().int().min(0),
    total_duration_ms: z.number().int().nonnegative(),
    average_step_duration_ms: z.number().int().nonnegative(),
  }),
  defects: z.array(z.object({
    step_no: z.number().int().positive(),
    title: z.string(),
    detail: z.string(),
    severity: z.enum(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
    screenshot_url: z.string().optional(),
    overlay: z.record(z.string(), z.unknown()).nullable().optional(),
  })),
  steps: z.array(z.object({
    step_no: z.number().int().positive(),
    node: z.string(),
    screenshot_url: z.string(),
    overlay: z.record(z.string(), z.unknown()).nullable().optional(),
    action: z.record(z.string(), z.unknown()),
    verify: z.record(z.string(), z.unknown()).nullable().optional(),
    executed_at: z.string(),
    duration_ms: z.number().int().nonnegative(),
  })),
  started_at: z.string(),
  completed_at: z.string().nullable(),
  generated_at: z.string(),
  export_formats: z.array(z.enum(['JSON', 'HTML', 'PDF', 'JUNIT', 'EXCEL'])).optional(),
  metadata: z.record(z.string(), z.unknown()).optional(),
});

const schemaMap: Record<SchemaType, z.ZodTypeAny> = {
  task: TaskSchemaZod,
  instance: InstanceSchemaZod,
  step: StepSchemaZod,
  action: ActionSchemaZod,
  event: EventSchemaZod,
  hil_ticket: HilTicketSchemaZod,
  report: ReportSchemaZod,
};
function getSchemaKeys(schemaType: SchemaType): Set<string> {
  const keysMap: Record<SchemaType, string[]> = {
    task: ['schema_version', 'created_at', 'updated_at', 'tenant_id', 'task_id', 'name', 'url', 'objective', 'constraints', 'tags', 'metadata'],
    instance: ['schema_version', 'created_at', 'updated_at', 'tenant_id', 'instance_id', 'task_id', 'status', 'started_at', 'completed_at', 'step_count', 'hil_count', 'defect_count', 'error_message', 'metadata'],
    step: ['schema_version', 'created_at', 'updated_at', 'tenant_id', 'step_id', 'instance_id', 'step_no', 'node', 'screenshot_url', 'overlay', 'action', 'verify', 'executed_at', 'duration_ms'],
    action: ['schema_version', 'created_at', 'updated_at', 'tenant_id', 'action_id', 'instance_id', 'step_no', 'thought', 'action_type', 'target', 'params', 'confidence', 'expected_result', 'candidates', 'generated_at', 'model_version'],
    event: ['schema_version', 'created_at', 'updated_at', 'tenant_id', 'event_id', 'event_type', 'instance_id', 'payload', 'timestamp', 'sequence_no'],
    hil_ticket: ['schema_version', 'created_at', 'updated_at', 'tenant_id', 'ticket_id', 'instance_id', 'step_no', 'status', 'reason', 'risk_level', 'planned_action', 'screenshot_url', 'overlay', 'decision', 'modified_action', 'decided_by', 'decided_at', 'expires_at', 'audit_trail'],
    report: ['schema_version', 'created_at', 'updated_at', 'tenant_id', 'report_id', 'instance_id', 'task_id', 'verdict', 'status', 'summary', 'statistics', 'defects', 'steps', 'started_at', 'completed_at', 'generated_at', 'export_formats', 'metadata'],
  };
  return new Set(keysMap[schemaType] || []);
}
export function validateSchema<T = unknown>(
  data: unknown,
  schemaType: SchemaType,
  options: { strict?: boolean; skipVersionCheck?: boolean } = {}
): ValidationResult<T> {
  const { strict = false, skipVersionCheck = false } = options;
  const errors: ValidationError[] = [];
  if (!data || typeof data !== 'object') {
    return {
      valid: false,
      errors: [{ path: 'root', message: '数据必须是非空对象', code: 'INVALID_TYPE' }],
    };
  }
  const dataObj = data as Record<string, unknown>;
  if (!skipVersionCheck) {
    if (!dataObj.schema_version || typeof dataObj.schema_version !== 'string') {
      return {
        valid: false,
        errors: [{ path: 'schema_version', message: '缺少 schema_version 字段', code: 'MISSING_VERSION' }],
      };
    }
    if (!isValidVersionFormat(dataObj.schema_version as string)) {
      return {
        valid: false,
        errors: [{ path: 'schema_version', message: 'schema_version 格式无效，应为 x.y.z 格式', code: 'INVALID_VERSION_FORMAT' }],
      };
    }
    if (!isVersionSupported(dataObj.schema_version as string)) {
      return {
        valid: false,
        errors: [{ path: 'schema_version', message: `不支持的版本: ${dataObj.schema_version}`, code: 'UNSUPPORTED_VERSION' }],
      };
    }
  }
  if (strict) {
    const allowedKeys = getSchemaKeys(schemaType);
    const dataKeys = Object.keys(dataObj);
    const extraKeys = dataKeys.filter((key) => !allowedKeys.has(key));
    if (extraKeys.length > 0) {
      for (const key of extraKeys) {
        errors.push({
          path: key,
          message: `严格模式下不允许额外字段: ${key}`,
          code: 'EXTRA_FIELD',
        });
      }
      return { valid: false, errors };
    }
  }
  const schema = schemaMap[schemaType];
  if (!schema) {
    return {
      valid: false,
      errors: [{ path: 'root', message: `未知的 Schema 类型: ${schemaType}`, code: 'UNKNOWN_SCHEMA_TYPE' }],
    };
  }
  const result = schema.safeParse(data);
  if (result.success) {
    return { valid: true, errors: [], data: result.data as T };
  }
  const zodErrors = result.error;
  for (const issue of zodErrors.issues) {
    const path = issue.path.map(String).join('.');
    errors.push({
      path: path || 'root',
      message: issue.message,
      code: 'VALIDATION_ERROR',
    });
  }
  return { valid: false, errors };
}
export function validateBatch<T = unknown>(
  items: unknown[],
  schemaType: SchemaType
): { results: ValidationResult<T>[]; allValid: boolean } {
  const results = items.map((item) => validateSchema<T>(item, schemaType));
  const allValid = results.every((r) => r.valid);
  return { results, allValid };
}

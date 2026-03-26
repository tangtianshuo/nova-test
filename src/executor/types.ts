/**
 * AaaS 执行器核心类型定义
 */

/**
 * 实例执行状态枚举
 */
export enum InstanceStatus {
  PENDING = 'PENDING',
  INITIALIZED = 'INITIALIZED',
  RUNNING = 'RUNNING',
  WAITING_HIL = 'WAITING_HIL',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  TERMINATED = 'TERMINATED',
}

/**
 * 节点执行结果
 */
export interface NodeResult {
  nodeName: string;
  success: boolean;
  nextNode: string;
  state: ExecutionState;
  error?: string;
}

/**
 * 执行状态
 */
export interface ExecutionState {
  instanceId: string;
  currentNode: string;
  stepCount: number;
  maxSteps: number;
  lastScreenshot?: string;
  plannedAction?: PlannedAction;
  hilTriggered: boolean;
  error?: string;
}

/**
 * 计划动作
 */
export interface PlannedAction {
  actionType: 'click' | 'type' | 'navigate' | 'scroll' | 'screenshot' | 'wait';
  selector?: string;
  value?: string;
  url?: string;
  confidence: number;
  thought: string;
}

/**
 * 执行结果
 */
export interface ExecutionResult {
  success: boolean;
  screenshot?: string;
  error?: string;
  defectDetected?: boolean;
  defectDetails?: string;
}

/**
 * 验证结果
 */
export interface VerificationResult {
  isSuccess: boolean;
  isDefect: boolean;
  message: string;
  screenshot?: string;
}

/**
 * HIL 触发条件
 */
export enum HilTriggerReason {
  LOW_CONFIDENCE = 'LOW_CONFIDENCE',
  PARSE_FAILURE = 'PARSE_FAILURE',
  UNKNOWN_ELEMENT = 'UNKNOWN_ELEMENT',
  EXECUTION_FAILURE = 'EXECUTION_FAILURE',
}

/**
 * HIL 决策
 */
export enum HilDecision {
  APPROVE = 'APPROVED',
  REJECT = 'REJECTED',
  MODIFIED = 'MODIFIED',
}

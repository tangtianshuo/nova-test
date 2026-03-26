/**
 * 公共类型定义
 * 职责：定义跨模块共享的基础类型，为 Schema 和业务逻辑提供类型支持
 */

/**
 * Schema 版本类型
 * 支持语义化版本控制，便于向后兼容
 */
export type SchemaVersion = `${number}.${number}.${number}` | `${number}.${number}`;

/**
 * 所有 Schema 的基础接口
 * 包含通用字段：版本号、时间戳、租户ID
 */
export interface BaseSchema {
  schema_version: SchemaVersion;
  created_at: string;
  updated_at: string;
  tenant_id: string;
}

/**
 * 癯境坐标
 * 用于标注层绘制和点击位置
 */
export interface BoundingBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

/**
 * 坐标点
 * 用于表示点击位置或中心点
 */
export interface Point {
  x: number;
  y: number;
}

/**
 * 动作目标
 * 描述操作的目标元素或位置
 */
export interface ActionTarget {
  selector?: string | null;
  x?: number | null;
  y?: number | null;
  bbox?: BoundingBox | null;
}

/**
 * 置信度类型
 * 取值范围：0.0 - 1.0
 */
export type Confidence = number;

/**
 * 风险等级
 * 用于 HIL 触发条件判断
 */
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

/**
 * HIL 决策类型
 * 人工干预后的决策结果
 */
export type HilDecision = 'approve' | 'reject' | 'modify';

/**
 * 执行状态枚举
 * 表示实例或步骤的运行状态
 */
export type ExecutionStatus =
  | 'PENDING'
  | 'RUNNING'
  | 'PAUSED_HIL'
  | 'SUCCESS'
  | 'FAILED';

/**
 * 动作类型枚举
 * Vision 模型输出的动作类型
 */
export type ActionType = 'click' | 'type' | 'scroll' | 'wait' | 'end';

/**
 * 时间戳字符串格式
 * ISO 8601 格式
 */
export type Timestamp = string;

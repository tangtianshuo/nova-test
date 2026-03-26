/**
 * 版本策略模块
 * 职责：定义 Schema 版本兼容性规则，支持多版本共存和向后兼容
 * @version 1.0.0
 */

import type { SchemaVersion } from '../../types/common.types';

/**
 * 当前支持的 Schema 版本列表
 * 新增版本需在此注册
 */
export const SUPPORTED_VERSIONS: SchemaVersion[] = [
  '1.0.0',
];

/**
 * 版本兼容性规则
 * 定义版本之间的兼容关系
 */
export const VERSION_COMPATIBILITY: Record<SchemaVersion, SchemaVersion[]> = {
  '1.0.0': ['1.0.0'],
};

/**
 * 检查版本是否被支持
 * @param version - 待检查的版本号
 * @returns 是否为支持的版本
 */
export function isVersionSupported(version: string): boolean {
  return SUPPORTED_VERSIONS.includes(version as SchemaVersion);
}

/**
 * 获取兼容的版本列表
 * @param version - 基准版本
 * @returns 兼容的版本列表
 */
export function getCompatibleVersions(version: string): SchemaVersion[] {
  return VERSION_COMPATIBILITY[version as SchemaVersion] || [];
}

/**
 * 比较两个版本号
 * @param v1 - 版本1
 * @param v2 - 版本2
 * @returns -1: v1 < v2, 0: v1 == v2, 1: v1 > v2
 */
export function compareVersions(v1: string, v2: string): number {
  const parts1 = v1.split('.').map(Number);
  const parts2 = v2.split('.').map(Number);

  for (let i = 0; i < 3; i++) {
    const p1 = parts1[i] || 0;
    const p2 = parts2[i] || 0;
    if (p1 < p2) return -1;
    if (p1 > p2) return 1;
  }
  return 0;
}

/**
 * 解析版本号为数字数组
 * @param version - 版本字符串
 * @returns [major, minor, patch] 数组
 */
export function parseVersion(version: string): [number, number, number] {
  const parts = version.split('.').map(Number);
  return [parts[0] || 0, parts[1] || 0, parts[2] || 0];
}

/**
 * 验证版本号格式
 * @param version - 待验证的版本字符串
 * @returns 是否为有效的版本格式
 */
export function isValidVersionFormat(version: string): boolean {
  const pattern = /^\d+\.\d+(\.\d+)?$/;
  return pattern.test(version);
}

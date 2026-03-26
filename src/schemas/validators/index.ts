/**
 * Validators 模块导出入口
 * 职责：统一导出校验器和版本策略
 */

export {
  isVersionSupported,
  getCompatibleVersions,
  compareVersions,
  parseVersion,
  isValidVersionFormat,
  SUPPORTED_VERSIONS,
  VERSION_COMPATIBILITY,
} from './version.strategy';

export {
  validateSchema,
  validateBatch,
  SchemaType,
  ValidationResult,
  ValidationError,
} from './schema.validator';

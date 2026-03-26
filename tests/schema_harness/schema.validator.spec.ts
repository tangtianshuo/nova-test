/**
 * Schema Harness 测试套件
 * 职责：验证 Schema 校验器的正向和负向校验能力
 */

import { validateSchema, validateBatch, ValidationError } from '../../src/schemas/validators';
import { isVersionSupported, isValidVersionFormat } from '../../src/schemas/validators/version.strategy';

import validTask from './fixtures/valid/task.valid.json';
import validInstance from './fixtures/valid/instance.valid.json';
import validStep from './fixtures/valid/step.valid.json';
import validAction from './fixtures/valid/action.valid.json';
import validEvent from './fixtures/valid/event.valid.json';
import validHilTicket from './fixtures/valid/hil_ticket.valid.json';
import validReport from './fixtures/valid/report.valid.json';
import invalidTaskMissingField from './fixtures/invalid/task.missing_field.json';
import invalidTaskInvalidVersion from './fixtures/invalid/task.invalid_version.json';
import invalidTaskTypeMismatch from './fixtures/invalid/task.type_mismatch.json';
import invalidInstanceMissingField from './fixtures/invalid/instance.missing_field.json';
import invalidStepMissingField from './fixtures/invalid/step.missing_field.json';
import invalidActionMissingField from './fixtures/invalid/action.missing_field.json';
import invalidEventMissingField from './fixtures/invalid/event.missing_field.json';
import invalidHilTicketMissingField from './fixtures/invalid/hil_ticket.missing_field.json';
import invalidReportMissingField from './fixtures/invalid/report.missing_field.json';

describe('Schema Validator', () => {
  describe('Version Strategy', () => {
    it('should accept valid version format', () => {
      expect(isValidVersionFormat('1.0.0')).toBe(true);
      expect(isValidVersionFormat('1.0')).toBe(true);
      expect(isValidVersionFormat('2.3.4')).toBe(true);
    });
    it('should reject invalid version format', () => {
      expect(isValidVersionFormat('1')).toBe(false);
      expect(isValidVersionFormat('abc')).toBe(false);
      expect(isValidVersionFormat('')).toBe(false);
    });
    it('should support current versions', () => {
      expect(isVersionSupported('1.0.0')).toBe(true);
    });
    it('should reject unsupported versions', () => {
      expect(isVersionSupported('99.99.99')).toBe(false);
      expect(isVersionSupported('0.0.1')).toBe(false);
    });
  });
  describe('Positive Validation - Valid Schemas', () => {
    it('should accept valid TaskSchema', () => {
      const result = validateSchema(validTask, 'task');
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });
    it('should accept valid InstanceSchema', () => {
      const result = validateSchema(validInstance, 'instance');
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });
    it('should accept valid StepSchema', () => {
      const result = validateSchema(validStep, 'step');
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });
    it('should accept valid ActionSchema', () => {
      const result = validateSchema(validAction, 'action');
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });
    it('should accept valid EventSchema', () => {
      const result = validateSchema(validEvent, 'event');
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });
    it('should accept valid HilTicketSchema', () => {
      const result = validateSchema(validHilTicket, 'hil_ticket');
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });
    it('should accept valid ReportSchema', () => {
      const result = validateSchema(validReport, 'report');
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });
  });
  describe('Negative Validation - Invalid Schemas', () => {
    it('should reject TaskSchema with missing required field', () => {
      const result = validateSchema(invalidTaskMissingField, 'task');
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
      const hasObjectiveOrUrlError = result.errors.some((e: ValidationError) => 
        e.path.includes('objective') || e.path.includes('url')
      );
      expect(hasObjectiveOrUrlError).toBe(true);
    });
    it('should reject TaskSchema with invalid version', () => {
      const result = validateSchema(invalidTaskInvalidVersion, 'task');
      expect(result.valid).toBe(false);
      const hasVersionError = result.errors.some((e: ValidationError) => 
        e.code.includes('VERSION') || e.code.includes('UNSUPPORTED')
      );
      expect(hasVersionError).toBe(true);
    });
    it('should reject TaskSchema with type mismatch', () => {
      const result = validateSchema(invalidTaskTypeMismatch, 'task');
      expect(result.valid).toBe(false);
      const hasTypeError = result.errors.some((e: ValidationError) => 
        e.path.includes('task_id') || e.path.includes('constraints')
      );
      expect(hasTypeError).toBe(true);
    });
    it('should reject InstanceSchema with missing required field', () => {
      const result = validateSchema(invalidInstanceMissingField, 'instance');
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
    });
    it('should reject StepSchema with missing required field', () => {
      const result = validateSchema(invalidStepMissingField, 'step');
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
    });
    it('should reject ActionSchema with missing required field', () => {
      const result = validateSchema(invalidActionMissingField, 'action');
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
    });
    it('should reject EventSchema with missing required field', () => {
      const result = validateSchema(invalidEventMissingField, 'event');
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
    });
    it('should reject HilTicketSchema with missing required field', () => {
      const result = validateSchema(invalidHilTicketMissingField, 'hil_ticket');
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
    });
    it('should reject ReportSchema with missing required field', () => {
      const result = validateSchema(invalidReportMissingField, 'report');
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
    });
  });
  describe('Batch Validation', () => {
    it('should validate multiple items at once', () => {
      const items = [validTask, { ...validTask, task_id: 'task-002' }, { ...validTask, task_id: 'task-003' }];
      const results = validateBatch(items, 'task');
      expect(results.allValid).toBe(true);
      expect(results.results).toHaveLength(3);
    });
    it('should fail batch if any item is invalid', () => {
      const items = [validTask, invalidTaskMissingField, { ...validTask, task_id: 'task-002' }];
      const results = validateBatch(items, 'task');
      expect(results.allValid).toBe(false);
      expect(results.results[0].valid).toBe(true);
      expect(results.results[1].valid).toBe(false);
    });
  });
  describe('Strict Mode', () => {
    it('should reject extra fields in strict mode', () => {
      const dataWithExtra = {
        ...validTask,
        extra_field: 'this should not be here',
      };
      const result = validateSchema(dataWithExtra, 'task', { strict: true });
      expect(result.valid).toBe(false);
    });
    it('should accept extra fields in non-strict mode', () => {
      const dataWithExtra = {
        ...validTask,
        extra_field: 'this is allowed',
      };
      const result = validateSchema(dataWithExtra, 'task', { strict: false });
      expect(result.valid).toBe(true);
    });
  });
});

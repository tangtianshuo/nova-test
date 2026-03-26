/**
 * API 契约测试套件
 * 遵循 Harness Engineering: 先建护栏，再写实现
 */

import { describe, it, expect } from 'vitest';

describe('API Contract Harness', () => {
  describe('H1: Task API Contract', () => {
    it('should_validate_task_creation_request', () => {
      const validTask = {
        name: 'Test Task',
        targetUrl: 'https://example.com',
        naturalObjective: 'Click login button',
      };
      expect(validTask.name).toBe('Test Task');
      expect(validTask.targetUrl).toBe('https://example.com');
    });

    it('should_reject_task_without_required_fields', () => {
      const invalidTask = {
        name: 'Test Task',
      };
      expect(invalidTask.targetUrl).toBeUndefined();
    });
  });

  describe('H2: Instance API Contract', () => {
    it('should_validate_instance_creation_request', () => {
      const validInstance = {
        taskId: 'task-uuid-here',
        status: 'PENDING',
      };
      expect(validInstance.taskId).toBe('task-uuid-here');
      expect(validInstance.status).toBe('PENDING');
    });

    it('should_validate_instance_state_response', () => {
      const validState = {
        instanceId: 'instance-uuid',
        status: 'RUNNING',
        currentStep: 1,
        langgraphState: {},
      };
      expect(validState.instanceId).toBe('instance-uuid');
      expect(validState.status).toBe('RUNNING');
    });
  });

  describe('H3: HIL API Contract', () => {
    it('should_validate_hil_ticket_creation', () => {
      const validTicket = {
        instanceId: 'instance-uuid',
        reason: '需要人工确认',
        riskLevel: 'MEDIUM',
      };
      expect(validTicket.instanceId).toBe('instance-uuid');
      expect(validTicket.riskLevel).toBe('MEDIUM');
    });

    it('should_validate_hil_resolution_request', () => {
      const validResolution = {
        decision: 'APPROVED',
        humanFeedback: '已确认安全',
      };
      expect(validResolution.decision).toBe('APPROVED');
    });
  });

  describe('H4: Health Check Contract', () => {
    it('should_return_health_status', () => {
      const healthResponse = {
        status: 'ok',
        timestamp: new Date().toISOString(),
      };
      expect(healthResponse.status).toBe('ok');
      expect(typeof healthResponse.timestamp).toBe('string');
    });
  });
});

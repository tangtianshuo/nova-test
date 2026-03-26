/**
 * 适配器 Harness 测试
 */
import { describe, it, expect } from 'vitest';
import { MockVisionAdapter } from '../../src/executor/adapters/vision.adapter';
import { MockVerifierAdapter } from '../../src/executor/adapters/verifier.adapter';

describe('Adapter Harness', () => {
  describe('H1: Vision Adapter', () => {
    it('should_generate_valid_planned_action', async () => {
      const adapter = new MockVisionAdapter();
      const result = await adapter.analyzePage(
        'base64_screenshot',
        '<html>test</html>',
        'test-instance'
      );

      expect(result).toBeDefined();
      expect(result.actionType).toBeDefined();
      expect(['click', 'type', 'navigate', 'scroll']).toContain(result.actionType);
      expect(result.confidence).toBeGreaterThanOrEqual(0);
      expect(result.confidence).toBeLessThanOrEqual(1);
      expect(result.thought).toBeDefined();
    });

    it('should_include_selector_for_click_actions', async () => {
      const adapter = new MockVisionAdapter();
      const result = await adapter.analyzePage(
        'base64_screenshot',
        '<html>test</html>',
        'test-instance'
      );

      if (result.actionType === 'click') {
        expect(result.selector).toBeDefined();
      }
    });
  });

  describe('H2: Verifier Adapter', () => {
    it('should_return_verification_result', async () => {
      const adapter = new MockVerifierAdapter();
      const result = await adapter.verifyExecution(
        'base64_screenshot',
        'previous_screenshot',
        { actionType: 'click', selector: '#btn', confidence: 0.9, thought: 'Test' },
        'test-instance'
      );

      expect(result).toBeDefined();
      expect(typeof result.isSuccess).toBe('boolean');
      expect(typeof result.isDefect).toBe('boolean');
      expect(result.message).toBeDefined();
    });
  });
});

describe('Type Definitions Harness', () => {
  describe('H1: InstanceStatus', () => {
    it('should_have_all_required_statuses', async () => {
      const types = await import('../../src/executor/types');
      
      expect(types.InstanceStatus.PENDING).toBe('PENDING');
      expect(types.InstanceStatus.INITIALIZED).toBe('INITIALIZED');
      expect(types.InstanceStatus.RUNNING).toBe('RUNNING');
      expect(types.InstanceStatus.WAITING_HIL).toBe('WAITING_HIL');
      expect(types.InstanceStatus.COMPLETED).toBe('COMPLETED');
      expect(types.InstanceStatus.FAILED).toBe('FAILED');
      expect(types.InstanceStatus.TERMINATED).toBe('TERMINATED');
    });
  });

  describe('H2: HilDecision', () => {
    it('should_have_all_required_decisions', async () => {
      const types = await import('../../src/executor/types');
      
      expect(types.HilDecision.APPROVE).toBe('APPROVED');
      expect(types.HilDecision.REJECT).toBe('REJECTED');
      expect(types.HilDecision.MODIFIED).toBe('MODIFIED');
    });
  });
});

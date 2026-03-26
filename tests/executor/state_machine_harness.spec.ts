/**
 * 节点 Harness 测试
 * 遵循 Harness Engineering: 先建护栏，再写实现
 */
import { describe, it, expect, vi } from 'vitest';
import { ExecutionState, SandboxContext, PlannedAction } from '../../src/executor/types';
import { decideNextNode, shouldEnterHil, HIL_CONFIG } from '../../src/executor/state_machine/routing';

describe('State Machine Routing Harness', () => {
  describe('H1: 节点路由', () => {
    it('should_route_init_to_explore', () => {
      const state: ExecutionState = {
        instanceId: 'test-instance',
        currentNode: 'init',
        stepCount: 0,
        maxSteps: 10,
        hilTriggered: false,
      };
      const next = decideNextNode(state);
      expect(next).toBe('explore');
    });

    it('should_route_explore_to_check_hil', () => {
      const state: ExecutionState = {
        instanceId: 'test-instance',
        currentNode: 'explore',
        stepCount: 0,
        maxSteps: 10,
        hilTriggered: false,
        plannedAction: {
          actionType: 'click',
          selector: '#btn',
          confidence: 0.9,
          thought: 'Test',
        },
      };
      const next = decideNextNode(state);
      expect(next).toBe('check_hil');
    });

    it('should_route_check_hil_to_execute_when_approved', () => {
      const state: ExecutionState = {
        instanceId: 'test-instance',
        currentNode: 'check_hil',
        stepCount: 1,
        maxSteps: 10,
        hilTriggered: false,
        plannedAction: {
          actionType: 'click',
          selector: '#btn',
          confidence: 0.9,
          thought: 'Test',
        },
      };
      const next = decideNextNode(state);
      expect(next).toBe('execute');
    });

    it('should_route_execute_to_verify', () => {
      const state: ExecutionState = {
        instanceId: 'test-instance',
        currentNode: 'execute',
        stepCount: 1,
        maxSteps: 10,
        hilTriggered: false,
      };
      const next = decideNextNode(state);
      expect(next).toBe('verify');
    });

    it('should_route_verify_to_explore', () => {
      const state: ExecutionState = {
        instanceId: 'test-instance',
        currentNode: 'verify',
        stepCount: 1,
        maxSteps: 10,
        hilTriggered: false,
      };
      const next = decideNextNode(state);
      expect(next).toBe('explore');
    });
  });

  describe('H2: HIL 触发判断', () => {
    it('should_enter_hil_when_confidence_below_threshold', () => {
      const state: ExecutionState = {
        instanceId: 'test-instance',
        currentNode: 'check_hil',
        stepCount: 0,
        maxSteps: 10,
        hilTriggered: false,
        plannedAction: {
          actionType: 'click',
          selector: '#btn',
          confidence: 0.5, // 低于阈值 0.7
          thought: 'Low confidence action',
        },
      };
      expect(shouldEnterHil(state)).toBe(true);
    });

    it('should_not_enter_hil_when_confidence_above_threshold', () => {
      const state: ExecutionState = {
        instanceId: 'test-instance',
        currentNode: 'check_hil',
        stepCount: 0,
        maxSteps: 10,
        hilTriggered: false,
        plannedAction: {
          actionType: 'click',
          selector: '#btn',
          confidence: 0.9, // 高于阈值
          thought: 'High confidence action',
        },
      };
      expect(shouldEnterHil(state)).toBe(false);
    });

    it('should_enter_hil_when_no_planned_action', () => {
      const state: ExecutionState = {
        instanceId: 'test-instance',
        currentNode: 'check_hil',
        stepCount: 0,
        maxSteps: 10,
        hilTriggered: false,
        plannedAction: undefined,
      };
      expect(shouldEnterHil(state)).toBe(true);
    });

    it('should_enter_hil_when_click_without_selector', () => {
      const state: ExecutionState = {
        instanceId: 'test-instance',
        currentNode: 'check_hil',
        stepCount: 0,
        maxSteps: 10,
        hilTriggered: false,
        plannedAction: {
          actionType: 'click',
          confidence: 0.9,
          thought: 'Click without selector',
        },
      };
      expect(shouldEnterHil(state)).toBe(true);
    });

    it('should_enter_hil_when_invalid_action_type', () => {
      const state: ExecutionState = {
        instanceId: 'test-instance',
        currentNode: 'check_hil',
        stepCount: 0,
        maxSteps: 10,
        hilTriggered: false,
        plannedAction: {
          actionType: 'invalid_action' as any,
          confidence: 0.9,
          thought: 'Invalid action',
        },
      };
      expect(shouldEnterHil(state)).toBe(true);
    });
  });

  describe('H3: 终止条件', () => {
    it('should_terminate_when_max_steps_reached', () => {
      const state: ExecutionState = {
        instanceId: 'test-instance',
        currentNode: 'execute',
        stepCount: 10, // 等于 maxSteps
        maxSteps: 10,
        hilTriggered: false,
      };
      const next = decideNextNode(state);
      expect(next).toBe('end');
    });

    it('should_terminate_when_error_occurs', () => {
      const state: ExecutionState = {
        instanceId: 'test-instance',
        currentNode: 'execute',
        stepCount: 5,
        maxSteps: 10,
        hilTriggered: false,
        error: 'Execution failed',
      };
      const next = decideNextNode(state);
      expect(next).toBe('end');
    });

    it('should_terminate_when_hil_triggered', () => {
      const state: ExecutionState = {
        instanceId: 'test-instance',
        currentNode: 'check_hil',
        stepCount: 3,
        maxSteps: 10,
        hilTriggered: true,
        plannedAction: {
          actionType: 'click',
          selector: '#btn',
          confidence: 0.5,
          thought: 'Low confidence',
        },
      };
      const next = decideNextNode(state);
      expect(next).toBe('end');
    });
  });

  describe('H4: HIL 配置', () => {
    it('should_have_correct_confidence_threshold', () => {
      expect(HIL_CONFIG.CONFIDENCE_THRESHOLD).toBe(0.7);
    });

    it('should_have_correct_max_retries', () => {
      expect(HIL_CONFIG.MAX_RETRIES).toBe(3);
    });
  });
});

/**
 * Replay Harness 测试
 * 用于复现关键场景
 */
import { describe, it, expect } from 'vitest';
import { ExecutionState } from '../../src/executor/types';
import { decideNextNode, shouldEnterHil } from '../../src/executor/state_machine/routing';

describe('Replay Harness', () => {
  describe('H1: 成功执行场景', () => {
    it('should_route_through_execution_flow', () => {
      // 模拟成功执行流程: init -> explore -> check_hil -> execute -> verify
      const flow = [
        { node: 'init', expectedNext: 'explore' },
        { node: 'explore', expectedNext: 'check_hil', action: { confidence: 0.9, actionType: 'click', selector: '#btn' } },
        { node: 'check_hil', expectedNext: 'execute' },
        { node: 'execute', expectedNext: 'verify' },
      ];

      flow.forEach((step) => {
        const state: ExecutionState = {
          instanceId: 'test-instance',
          currentNode: step.node,
          stepCount: step.stepCount ?? 0,
          maxSteps: step.maxSteps ?? 10,
          hilTriggered: false,
          plannedAction: step.action,
        };

        const next = decideNextNode(state);
        expect(next).toBe(step.expectedNext);
      });
    });
  });

  describe('H2: HIL 触发场景', () => {
    it('should_trigger_hil_on_low_confidence', () => {
      const state: ExecutionState = {
        instanceId: 'test-instance',
        currentNode: 'check_hil',
        stepCount: 2,
        maxSteps: 10,
        hilTriggered: false,
        plannedAction: {
          actionType: 'click',
          selector: '#unknown',
          confidence: 0.5, // 低置信度
          thought: 'Not sure about this action',
        },
      };

      expect(shouldEnterHil(state)).toBe(true);
      expect(state.hilTriggered).toBe(false); // 调用 decideNextNode 后才会设置 hilTriggered
    });

    it('should_trigger_hil_on_parse_failure', () => {
      const state: ExecutionState = {
        instanceId: 'test-instance',
        currentNode: 'check_hil',
        stepCount: 1,
        maxSteps: 10,
        hilTriggered: false,
        plannedAction: undefined, // 解析失败
      };

      expect(shouldEnterHil(state)).toBe(true);
    });
  });

  describe('H3: 缺陷检测场景', () => {
    it('should_terminate_on_error', () => {
      const state: ExecutionState = {
        instanceId: 'test-instance',
        currentNode: 'execute',
        stepCount: 5,
        maxSteps: 10,
        hilTriggered: false,
        error: 'Defect detected: Page shows error message',
      };

      const next = decideNextNode(state);
      expect(next).toBe('end');
    });
  });

  describe('H4: 多轮执行场景', () => {
    it('should_continue_exploring_after_successful_verify', () => {
      const state: ExecutionState = {
        instanceId: 'test-instance',
        currentNode: 'verify',
        stepCount: 3,
        maxSteps: 10,
        hilTriggered: false,
      };

      const next = decideNextNode(state);
      expect(next).toBe('explore');
    });

    it('should_terminate_at_max_steps', () => {
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
  });
});

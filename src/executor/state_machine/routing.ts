/**
 * 状态机节点路由逻辑
 * 
 * 根据当前状态决定下一个执行节点。
 * 
 * 路由规则：
 * - initialized -> explore: 初始化完成，开始探索
 * - explored -> check_hil: 探索完成，检查是否需要人工介入
 * - check_hil (批准) -> execute: 置信度足够，执行动作
 * - check_hil (拒绝) -> explore: 需要修改，重新探索
 * - check_hil (HIL触发) -> 暂停: 等待人工干预
 * - executed -> verify: 执行完成，进入验证
 * - verified (成功) -> explore 或 end: 验证通过，继续或结束
 * - verified (失败) -> explore: 验证失败，重试
 * - verified (缺陷) -> end: 检测到缺陷，终止
 */
import { ExecutionState } from '../types';

/**
 * 节点名称枚举
 */
export enum NodeName {
  INIT = 'init',
  EXPLORE = 'explore',
  CHECK_HIL = 'check_hil',
  EXECUTE = 'execute',
  VERIFY = 'verify',
  END = 'end',
}

/**
 * HIL 阈值配置
 */
export const HIL_CONFIG = {
  CONFIDENCE_THRESHOLD: 0.7,
  MAX_RETRIES: 3,
};

/**
 * 决定下一个节点
 */
export function decideNextNode(state: ExecutionState): string {
  const { currentNode, hilTriggered, stepCount, maxSteps, error } = state;

  // 检查终止条件
  if (stepCount >= maxSteps) {
    console.log('[Routing] 终止: 达到最大步数');
    return NodeName.END;
  }

  if (error) {
    console.log(`[Routing] 终止: ${error}`);
    return NodeName.END;
  }

  switch (currentNode) {
    case NodeName.INIT:
      return NodeName.EXPLORE;

    case NodeName.EXPLORE:
      return NodeName.CHECK_HIL;

    case NodeName.CHECK_HIL:
      if (hilTriggered) {
        console.log('[Routing] HIL 触发，暂停');
        return NodeName.END;
      }
      return NodeName.EXECUTE;

    case NodeName.EXECUTE:
      return NodeName.VERIFY;

    case NodeName.VERIFY:
      return NodeName.EXPLORE;

    default:
      console.warn(`[Routing] 未知节点: ${currentNode}`);
      return NodeName.END;
  }
}

/**
 * 判断是否应该进入 HIL
 * 
 * 触发条件：
 * 1. 置信度低于阈值
 * 2. 解析失败
 * 3. 遇到未知元素
 */
export function shouldEnterHil(state: ExecutionState, reason?: string): boolean {
  const { plannedAction } = state;

  if (!plannedAction) return true;

  if (reason) return true;

  if (plannedAction.confidence < HIL_CONFIG.CONFIDENCE_THRESHOLD) {
    console.log(`[Routing] 进入HIL: 置信度 ${plannedAction.confidence} 低于阈值 ${HIL_CONFIG.CONFIDENCE_THRESHOLD}`);
    return true;
  }

  if (!plannedAction.actionType || !['click', 'type', 'navigate', 'scroll', 'wait'].includes(plannedAction.actionType)) {
    console.log(`[Routing] 进入HIL: 无效的动作类型 ${plannedAction.actionType}`);
    return true;
  }

  if (plannedAction.actionType === 'click' && !plannedAction.selector) {
    console.log('[Routing] 进入HIL: 点击动作缺少 selector');
    return true;
  }

  return false;
}

/**
 * 判断是否应该结束执行
 */
export function shouldEndExecution(state: ExecutionState): boolean {
  if (state.stepCount >= state.maxSteps) {
    return true;
  }

  if (state.error) {
    return true;
  }

  return false;
}

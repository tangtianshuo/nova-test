/**
 * check_hil 节点
 * 
 * HIL 检查阶段，负责：
 * 1. 评估动作计划的置信度
 * 2. 检查是否需要人工介入
 * 3. 根据判断决定后续流程
 * 
 * 触发 HIL 的条件：
 * 1. 置信度低于阈值 (HIL_CONFIG.CONFIDENCE_THRESHOLD)
 * 2. 动作计划不完整或无效
 * 3. 模型输出解析失败
 */
import { ExecutionState, NodeResult, HilTriggerReason } from '../../types';
import { SandboxManager, SandboxContext } from '../../worker/sandbox.manager';
import { shouldEnterHil, HIL_CONFIG } from '../routing';
import { hilTicketRepository } from '../../../db/repositories';

export async function checkHilNode(
  state: ExecutionState,
  _sandbox: SandboxContext,
  _sandboxManager: SandboxManager
): Promise<NodeResult> {
  void _sandbox;
  void _sandboxManager;
  console.log(`[CheckHil] 检查 HIL: ${state.instanceId}`);

  const { plannedAction } = state;

  if (!plannedAction) {
    console.log('[CheckHil] 无动作计划，触发 HIL');
    
    // 创建 HIL 工单
    await createHilTicket(state, HilTriggerReason.PARSE_FAILURE);

    return {
      nodeName: 'check_hil',
      success: true,
      nextNode: 'end',
      state: {
        ...state,
        hilTriggered: true,
        currentNode: 'waiting_hil',
      },
    };
  }

  // 检查置信度
  if (plannedAction.confidence < HIL_CONFIG.CONFIDENCE_THRESHOLD) {
    console.log(`[CheckHil] 置信度 ${plannedAction.confidence} 低于阈值 ${HIL_CONFIG.CONFIDENCE_THRESHOLD}，触发 HIL`);
    
    await createHilTicket(state, HilTriggerReason.LOW_CONFIDENCE);

    return {
      nodeName: 'check_hil',
      success: true,
      nextNode: 'end',
      state: {
        ...state,
        hilTriggered: true,
        currentNode: 'waiting_hil',
      },
    };
  }

  // 检查动作有效性
  if (shouldEnterHil(state)) {
    console.log('[CheckHil] 动作无效，触发 HIL');
    
    await createHilTicket(state, HilTriggerReason.UNKNOWN_ELEMENT);

    return {
      nodeName: 'check_hil',
      success: true,
      nextNode: 'end',
      state: {
        ...state,
        hilTriggered: true,
        currentNode: 'waiting_hil',
      },
    };
  }

  console.log('[CheckHil] 置信度足够，直接执行');

  return {
    nodeName: 'check_hil',
    success: true,
    nextNode: 'execute',
    state: {
      ...state,
      hilTriggered: false,
      currentNode: 'checked',
    },
  };
}

/**
 * 创建 HIL 工单
 */
async function createHilTicket(state: ExecutionState, reason: HilTriggerReason): Promise<void> {
  try {
    await hilTicketRepository.create({
      tenantId: '', // 需要从上下文获取
      instanceId: state.instanceId,
      stepNo: state.stepCount,
      reason: `HIL Trigger: ${reason} - ${state.plannedAction?.thought || 'No thought'}`,
      riskLevel: state.plannedAction?.confidence < 0.5 ? 'HIGH' : 'MEDIUM',
      plannedAction: state.plannedAction
        ? {
            actionType: state.plannedAction.actionType,
            selector: state.plannedAction.selector,
            value: state.plannedAction.value,
          }
        : undefined,
      screenshotUrl: state.lastScreenshot,
    });
    console.log(`[CheckHil] HIL 工单已创建`);
  } catch (error) {
    console.error('[CheckHil] 创建 HIL 工单失败:', error);
  }
}

export default checkHilNode;

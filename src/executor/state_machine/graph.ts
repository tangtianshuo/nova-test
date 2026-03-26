/**
 * LangGraph 状态机
 * 
 * 状态机定义，包含节点路由和终止条件判断。
 * 
 * 状态转换图：
 * start -> init -> explore -> check_hil -> execute -> verify -> end
 *                  ^                                        |
 *                  |                                        v
 *                  +-------------------------------------- explore
 *                                          
 * check_hil 可能触发 HIL 暂停:
 * check_hil -> WAITING_HIL -> resume -> execute
 * 
 * 终止条件：
 * 1. stepCount >= maxSteps
 * 2. verify 节点返回 success 且 shouldEnd = true
 * 3. 检测到缺陷 (defectDetected = true)
 * 4. 执行失败且不可恢复
 */
import { ExecutionState } from '../types';
import { SandboxManager, SandboxContext } from '../worker/sandbox.manager';
import { instanceRepository, stepRepository } from '../../db/repositories';
import {
  initNode,
  exploreNode,
  checkHilNode,
  executeNode,
  verifyNode,
} from './nodes';
import { decideNextNode } from './routing';

/**
 * 节点映射
 */
const NODE_HANDLERS = {
  init: initNode,
  explore: exploreNode,
  check_hil: checkHilNode,
  execute: executeNode,
  verify: verifyNode,
};

export interface ExecutionGraph {
  execute(state: ExecutionState, sandbox: SandboxContext): Promise<void>;
}

export function createExecutionGraph(): ExecutionGraph {
  return {
    async execute(initialState: ExecutionState, sandbox: SandboxContext): Promise<void> {
      let state = initialState;
      const { instanceId } = state;
      const sandboxManager = new SandboxManager();

      console.log(`[Graph] 开始执行状态机: ${instanceId}`);

      while (true) {
        console.log(`[Graph] 当前节点: ${state.currentNode}, 步骤: ${state.stepCount}`);

        // 获取节点处理器
        const handler = NODE_HANDLERS[state.currentNode as keyof typeof NODE_HANDLERS];
        if (!handler) {
          console.error(`[Graph] 未知节点: ${state.currentNode}`);
          break;
        }

        try {
          // 执行节点
          const result = await handler(state, sandbox, sandboxManager);

          if (!result.success) {
            console.error(`[Graph] 节点执行失败: ${state.currentNode}`, result.error);
            break;
          }

          // 更新状态
          state = result.state;

          // 记录步骤到数据库
          await stepRepository.create({
            instanceId,
            stepNumber: state.stepCount,
            nodeName: state.currentNode,
            thought: state.plannedAction?.thought,
            actionType: state.plannedAction?.actionType,
            actionTarget: state.plannedAction?.selector
              ? { selector: state.plannedAction.selector }
              : undefined,
            actionParams: state.plannedAction?.value ? { value: state.plannedAction.value } : undefined,
            confidence: state.plannedAction?.confidence,
            screenshotUrl: state.lastScreenshot,
          });

          // 检查终止条件
          if (shouldTerminate(state)) {
            console.log(`[Graph] 满足终止条件，状态机结束: ${instanceId}`);
            break;
          }

          // 决定下一个节点
          const nextNode = decideNextNode(state);
          if (nextNode === 'end') {
            console.log(`[Graph] 正常结束: ${instanceId}`);
            break;
          }

          state = {
            ...state,
            currentNode: nextNode,
            stepCount: state.currentNode === 'execute' ? state.stepCount + 1 : state.stepCount,
          };
        } catch (error) {
          console.error(`[Graph] 节点执行异常: ${state.currentNode}`, error);
          state = {
            ...state,
            error: String(error),
            hilTriggered: true,
          };
          break;
        }
      }

      // 更新实例最终状态
      const finalStatus = state.error
        ? 'FAILED'
        : state.hilTriggered
          ? 'WAITING_HIL'
          : 'COMPLETED';

      await instanceRepository.updateStatus(instanceId, finalStatus);
      console.log(`[Graph] 状态机执行完成: ${instanceId}, 最终状态: ${finalStatus}`);
    },
  };
}

/**
 * 判断是否应该终止状态机
 * 
 * 终止条件：
 * 1. 达到最大步数
 * 2. 验证成功且shouldEnd
 * 3. 检测到缺陷
 * 4. 有不可恢复错误
 */
function shouldTerminate(state: ExecutionState): boolean {
  // 条件1: 达到最大步数
  if (state.stepCount >= state.maxSteps) {
    console.log('[Graph] 终止原因: 达到最大步数');
    return true;
  }

  // 条件2: 有错误
  if (state.error) {
    console.log(`[Graph] 终止原因: ${state.error}`);
    return true;
  }

  return false;
}

export default createExecutionGraph;

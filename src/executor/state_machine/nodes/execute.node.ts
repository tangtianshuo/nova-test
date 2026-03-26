/**
 * execute 节点
 * 
 * 执行阶段，负责：
 * 1. 根据 planned_action 执行具体动作
 * 2. 使用 Playwright 执行动作
 * 3. 捕获执行结果和截图
 * 4. 处理执行失败情况
 */
import { ExecutionState, NodeResult } from '../../types';
import { SandboxManager, SandboxContext } from '../../worker/sandbox.manager';
import { ExecutorAdapter, executorAdapter } from '../../adapters/executor.adapter';

export async function executeNode(
  state: ExecutionState,
  sandbox: SandboxContext,
  sandboxManager: SandboxManager,
  executor: ExecutorAdapter = executorAdapter
): Promise<NodeResult> {
  console.log(`[Execute] 执行动作: ${state.instanceId}`);

  const { plannedAction } = state;

  if (!plannedAction) {
    console.error('[Execute] 无动作计划');
    return {
      nodeName: 'execute',
      success: false,
      nextNode: 'end',
      state: {
        ...state,
        error: 'No planned action',
      },
    };
  }

  try {
    // 执行动作
    const result = await executor.executeAction(sandbox.page, plannedAction);

    // 更新截图
    let newScreenshot = state.lastScreenshot;
    if (result.screenshot) {
      newScreenshot = result.screenshot;
    }

    if (!result.success) {
      console.log(`[Execute] 执行失败: ${result.error}`);
      return {
        nodeName: 'execute',
        success: false,
        nextNode: 'end',
        state: {
          ...state,
          lastScreenshot: newScreenshot,
          error: result.error,
        },
      };
    }

    console.log('[Execute] 执行成功');
    return {
      nodeName: 'execute',
      success: true,
      nextNode: 'verify',
      state: {
        ...state,
        currentNode: 'executed',
        lastScreenshot: newScreenshot,
        stepCount: state.stepCount + 1,
      },
    };
  } catch (error) {
    console.error('[Execute] 执行异常:', error);
    return {
      nodeName: 'execute',
      success: false,
      nextNode: 'end',
      state: {
        ...state,
        error: String(error),
      },
    };
  }
}

export default executeNode;

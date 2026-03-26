/**
 * verify 节点
 * 
 * 验证阶段，负责：
 * 1. 验证执行结果是否符合预期
 * 2. 使用 Verifier 模型检测缺陷
 * 3. 判断是否需要继续执行或终止
 */
import { ExecutionState, NodeResult } from '../../types';
import { SandboxManager, SandboxContext } from '../../worker/sandbox.manager';
import { VerifierAdapter, verifierAdapter } from '../../adapters/verifier.adapter';

export async function verifyNode(
  state: ExecutionState,
  sandbox: SandboxContext,
  _sandboxManager: SandboxManager,
  verifier: VerifierAdapter = verifierAdapter
): Promise<NodeResult> {
  console.log(`[Verify] 验证结果: ${state.instanceId}`);

  try {
    // 获取当前截图
    const screenshotBuffer = await sandbox.page.screenshot({ type: 'png' });
    const screenshot = screenshotBuffer.toString('base64');

    // 调用 Verifier 验证结果
    const result = await verifier.verifyExecution(
      screenshot,
      state.lastScreenshot || '',
      state.plannedAction,
      state.instanceId
    );

    console.log(`[Verify] 验证结果: 成功=${result.isSuccess}, 缺陷=${result.isDefect}`);

    // 更新状态
    const newState: ExecutionState = {
      ...state,
      currentNode: result.isSuccess ? 'verified' : 'verification_failed',
      lastScreenshot: result.screenshot || screenshot,
    };

    // 根据验证结果决定后续流程
    if (result.isDefect) {
      console.log('[Verify] 检测到缺陷，终止执行');
      return {
        nodeName: 'verify',
        success: false,
        nextNode: 'end',
        state: {
          ...newState,
          error: `Defect detected: ${result.message}`,
        },
      };
    }

    if (result.isSuccess) {
      // 验证成功，检查是否应该结束
      if (state.stepCount >= state.maxSteps) {
        console.log('[Verify] 达到最大步数，结束执行');
        return {
          nodeName: 'verify',
          success: true,
          nextNode: 'end',
          state: newState,
        };
      }

      // 继续探索
      return {
        nodeName: 'verify',
        success: true,
        nextNode: 'explore',
        state: newState,
      };
    }

    // 验证失败但不是缺陷，重试验证
    return {
      nodeName: 'verify',
      success: true,
      nextNode: 'explore',
      state: newState,
    };
  } catch (error) {
    console.error('[Verify] 验证异常:', error);
    return {
      nodeName: 'verify',
      success: false,
      nextNode: 'end',
      state: {
        ...state,
        error: String(error),
      },
    };
  }
}

export default verifyNode;

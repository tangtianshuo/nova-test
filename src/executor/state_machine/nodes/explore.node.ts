/**
 * explore 节点
 * 
 * 探索阶段，负责：
 * 1. 分析当前页面状态
 * 2. 使用 Vision 模型生成动作计划
 * 3. 产出 planned_action
 */
import { ExecutionState, NodeResult } from '../../types';
import { SandboxManager, SandboxContext } from '../../worker/sandbox.manager';
import { VisionAdapter, visionAdapter } from '../../adapters/vision.adapter';

export async function exploreNode(
  state: ExecutionState,
  sandbox: SandboxContext,
  _sandboxManager: SandboxManager,
  visionClient: VisionAdapter = visionAdapter
): Promise<NodeResult> {
  console.log(`[Explore] 探索实例: ${state.instanceId}, 步骤: ${state.stepCount}`);

  try {
    // 获取页面内容
    const content = await sandbox.page.content();
    const screenshotBuffer = await sandbox.page.screenshot({ type: 'png' });
    const screenshot = screenshotBuffer.toString('base64');

    // 调用 Vision 模型分析页面
    const plannedAction = await visionClient.analyzePage(
      screenshot,
      content || '',
      state.instanceId
    );

    console.log(`[Explore] 动作计划: ${plannedAction.actionType}, 置信度: ${plannedAction.confidence}`);

    // 更新状态
    const newState: ExecutionState = {
      ...state,
      currentNode: 'explored',
      lastScreenshot: screenshot,
      plannedAction,
      hilTriggered: false,
    };

    return {
      nodeName: 'explore',
      success: true,
      nextNode: 'check_hil',
      state: newState,
    };
  } catch (error) {
    console.error('[Explore] 探索失败:', error);
    return {
      nodeName: 'explore',
      success: false,
      nextNode: 'end',
      state: {
        ...state,
        error: String(error),
        hilTriggered: true,
      },
    };
  }
}

export default exploreNode;

/**
 * init 节点
 * 
 * 初始化阶段，负责：
 * 1. 初始化浏览器环境
 * 2. 导航到目标页面
 * 3. 生成初始截图
 * 4. 设置初始状态
 */
import { ExecutionState, NodeResult } from '../../types';
import { SandboxManager, SandboxContext } from '../../worker/sandbox.manager';

export async function initNode(
  state: ExecutionState,
  sandbox: SandboxContext,
  _sandboxManager: SandboxManager
): Promise<NodeResult> {
  void _sandboxManager;
  console.log(`[Init] 初始化实例: ${state.instanceId}`);

  try {
    // 生成初始截图
    const screenshot = await sandbox.page.screenshot({
      type: 'png',
      fullPage: false,
    });
    const screenshotBase64 = screenshot.toString('base64');

    // 更新状态
    const newState: ExecutionState = {
      ...state,
      currentNode: 'initialized',
      lastScreenshot: screenshotBase64,
      stepCount: 0,
      hilTriggered: false,
    };

    console.log(`[Init] 初始化完成，截图大小: ${screenshotBase64.length} bytes`);

    return {
      nodeName: 'init',
      success: true,
      nextNode: 'explore',
      state: newState,
    };
  } catch (error) {
    console.error('[Init] 初始化失败:', error);
    return {
      nodeName: 'init',
      success: false,
      nextNode: 'end',
      state: {
        ...state,
        error: String(error),
      },
    };
  }
}

export default initNode;

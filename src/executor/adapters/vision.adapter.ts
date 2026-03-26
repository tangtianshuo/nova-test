/**
 * Vision 适配器接口
 *
 * 定义 Vision 模型（视觉推理）的调用规范。
 * 支持 Fara-7B 或其他视觉语言模型。
 */
import { PlannedAction } from '../types';

export interface VisionAdapter {
  /**
   * 分析页面并生成动作计划
   *
   * @param screenshot 页面截图 (base64)
   * @param htmlContent 页面 HTML 内容
   * @param instanceId 实例 ID
   * @returns 计划动作
   */
  analyzePage(screenshot: string, htmlContent: string, instanceId: string): Promise<PlannedAction>;
}

export class MockVisionAdapter implements VisionAdapter {
  async analyzePage(
    _screenshot: string,
    _htmlContent: string,
    instanceId: string
  ): Promise<PlannedAction> {
    console.log(`[MockVision] 分析页面: ${instanceId}`);

    // Mock 实现：生成随机动作
    const actionTypes = ['click', 'type', 'navigate', 'scroll'];
    const actionType = actionTypes[Math.floor(Math.random() * actionTypes.length)];

    const selectors = ['#submit', '.btn-primary', 'button[type="submit"]', 'a.next'];
    const selector = selectors[Math.floor(Math.random() * selectors.length)];

    return {
      actionType: actionType as PlannedAction['actionType'],
      selector: actionType === 'click' || actionType === 'type' ? selector : undefined,
      value: actionType === 'type' ? 'test input' : undefined,
      url: actionType === 'navigate' ? 'https://example.com/page2' : undefined,
      confidence: 0.5 + Math.random() * 0.5,
      thought: `Mock thought: I should ${actionType} on ${selector || 'the page'}`,
    };
  }
}

export const visionAdapter = new MockVisionAdapter();
export default visionAdapter;

/**
 * Executor 适配器接口
 * 
 * 定义浏览器执行器（Playwright）的调用规范。
 * 负责执行具体的用户动作。
 */
import type { Page } from 'playwright';
import { PlannedAction, ExecutionResult } from '../types';

export interface ExecutorAdapter {
  /**
   * 执行动作
   * 
   * @param page Playwright 页面对象
   * @param action 计划动作
   * @returns 执行结果
   */
  executeAction(page: Page, action: PlannedAction): Promise<ExecutionResult>;
}

export class MockExecutorAdapter implements ExecutorAdapter {
  async executeAction(page: Page, action: PlannedAction): Promise<ExecutionResult> {
    console.log(`[MockExecutor] 执行动作: ${action.actionType}`);

    try {
      switch (action.actionType) {
        case 'click':
          if (!action.selector) {
            return { success: false, error: 'Missing selector for click action' };
          }
          await page.click(action.selector, { timeout: 10000 });
          break;

        case 'type':
          if (!action.selector || !action.value) {
            return { success: false, error: 'Missing selector or value for type action' };
          }
          await page.fill(action.selector, action.value, { timeout: 10000 });
          break;

        case 'navigate':
          if (!action.url) {
            return { success: false, error: 'Missing URL for navigate action' };
          }
          await page.goto(action.url, { waitUntil: 'domcontentloaded', timeout: 30000 });
          break;

        case 'scroll':
          await page.evaluate(() => window.scrollBy(0, 300));
          break;

        case 'wait':
          await page.waitForTimeout(1000);
          break;

        case 'screenshot':
          break;

        default:
          return { success: false, error: `Unknown action type: ${action.actionType}` };
      }

      // 执行成功后截图
      const screenshotBuffer = await page.screenshot({ type: 'png' });
      const screenshot = screenshotBuffer.toString('base64');

      return {
        success: true,
        screenshot,
      };
    } catch (error) {
      const screenshotBuffer = await page.screenshot({ type: 'png' }).catch(() => undefined);
      const screenshot = screenshotBuffer?.toString('base64');
      return {
        success: false,
        error: String(error),
        screenshot,
      };
    }
  }
}

export const executorAdapter = new MockExecutorAdapter();
export default executorAdapter;

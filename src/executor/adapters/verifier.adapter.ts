/**
 * Verifier 适配器接口
 * 
 * 定义验证器（缺陷检测）的调用规范。
 * 负责验证执行结果和检测缺陷。
 */
import { PlannedAction, VerificationResult } from '../types';

export interface VerifierAdapter {
  /**
   * 验证执行结果
   * 
   * @param currentScreenshot 当前截图 (base64)
   * @param previousScreenshot 前一个截图 (base64)
   * @param action 执行的动作用于分析预期结果
   * @param instanceId 实例 ID
   * @returns 验证结果
   */
  verifyExecution(
    currentScreenshot: string,
    previousScreenshot: string,
    action: PlannedAction | undefined,
    instanceId: string
  ): Promise<VerificationResult>;
}

export class MockVerifierAdapter implements VerifierAdapter {
  async verifyExecution(
    currentScreenshot: string,
    _previousScreenshot: string,
    action: PlannedAction | undefined,
    instanceId: string
  ): Promise<VerificationResult> {
    console.log(`[MockVerifier] 验证执行: ${instanceId}`);

    // Mock 实现：随机生成验证结果
    // 90% 概率验证成功，10% 概率检测到缺陷
    const random = Math.random();

    if (random < 0.1) {
      return {
        isSuccess: false,
        isDefect: true,
        message: 'Mock defect: 页面显示错误信息 "Error 500"',
        screenshot: currentScreenshot,
      };
    }

    return {
      isSuccess: true,
      isDefect: false,
      message: action
        ? `成功执行 ${action.actionType}，页面状态正常`
        : '验证通过，页面状态正常',
      screenshot: currentScreenshot,
    };
  }
}

export const verifierAdapter = new MockVerifierAdapter();
export default verifierAdapter;

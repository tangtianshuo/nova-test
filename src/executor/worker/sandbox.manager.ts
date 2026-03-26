/**
 * 沙箱管理器
 * 
 * 负责管理浏览器沙箱实例的生命周期。
 * 每个实例对应一个独立的浏览器上下文，确保测试隔离。
 * 
 * 功能：
 * 1. 创建浏览器沙箱（使用 Playwright）
 * 2. 执行页面操作（导航、截图、点击等）
 * 3. 资源清理
 */
import { chromium, Browser, Page, BrowserContext } from 'playwright';

export interface SandboxConfig {
  instanceId: string;
  targetUrl: string;
}

export interface SandboxContext {
  instanceId: string;
  browser: Browser;
  context: BrowserContext;
  page: Page;
}

export interface ActionResult {
  success: boolean;
  screenshot?: string;
  error?: string;
}

export class SandboxManager {
  private sandboxes: Map<string, SandboxContext> = new Map();

  /**
   * 创建沙箱
   * 启动浏览器并导航到目标 URL
   */
  async createSandbox(config: SandboxConfig): Promise<SandboxContext> {
    console.log(`[Sandbox] 创建沙箱: ${config.instanceId}`);

    const browser = await chromium.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });

    const context = await browser.newContext({
      viewport: { width: 1280, height: 720 },
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    });

    const page = await context.newPage();

    try {
      await page.goto(config.targetUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
    } catch (error) {
      console.warn(`[Sandbox] 导航失败: ${config.targetUrl}`, error);
    }

    const sandbox: SandboxContext = {
      instanceId: config.instanceId,
      browser,
      context,
      page,
    };

    this.sandboxes.set(config.instanceId, sandbox);
    return sandbox;
  }

  /**
   * 获取沙箱
   */
  getSandbox(instanceId: string): SandboxContext | undefined {
    return this.sandboxes.get(instanceId);
  }

  /**
   * 销毁沙箱
   * 关闭浏览器并清理资源
   */
  async destroySandbox(instanceId: string): Promise<void> {
    const sandbox = this.sandboxes.get(instanceId);
    if (!sandbox) return;

    console.log(`[Sandbox] 销毁沙箱: ${instanceId}`);

    try {
      await sandbox.context.close();
      await sandbox.browser.close();
    } catch (error) {
      console.error(`[Sandbox] 销毁沙箱失败: ${instanceId}`, error);
    }

    this.sandboxes.delete(instanceId);
  }

  /**
   * 清理所有沙箱
   */
  async cleanupAll(): Promise<void> {
    console.log('[Sandbox] 清理所有沙箱...');
    const instanceIds = Array.from(this.sandboxes.keys());
    await Promise.all(instanceIds.map((id) => this.destroySandbox(id)));
  }

  /**
   * 截图
   */
  async screenshot(instanceId: string): Promise<string | undefined> {
    const sandbox = this.getSandbox(instanceId);
    if (!sandbox) return undefined;

    try {
      const buffer = await sandbox.page.screenshot({
        type: 'png',
        fullPage: false,
      });
      return buffer.toString('base64');
    } catch (error) {
      console.error(`[Sandbox] 截图失败: ${instanceId}`, error);
      return undefined;
    }
  }

  /**
   * 执行点击动作
   */
  async click(instanceId: string, selector: string): Promise<ActionResult> {
    const sandbox = this.getSandbox(instanceId);
    if (!sandbox) {
      return { success: false, error: '沙箱不存在' };
    }

    try {
      await sandbox.page.click(selector, { timeout: 10000 });
      const screenshot = await this.screenshot(instanceId);
      return { success: true, screenshot };
    } catch (error) {
      return { success: false, error: String(error), screenshot: await this.screenshot(instanceId) };
    }
  }

  /**
   * 执行输入动作
   */
  async type(instanceId: string, selector: string, value: string): Promise<ActionResult> {
    const sandbox = this.getSandbox(instanceId);
    if (!sandbox) {
      return { success: false, error: '沙箱不存在' };
    }

    try {
      await sandbox.page.fill(selector, value, { timeout: 10000 });
      const screenshot = await this.screenshot(instanceId);
      return { success: true, screenshot };
    } catch (error) {
      return { success: false, error: String(error), screenshot: await this.screenshot(instanceId) };
    }
  }

  /**
   * 导航到 URL
   */
  async navigate(instanceId: string, url: string): Promise<ActionResult> {
    const sandbox = this.getSandbox(instanceId);
    if (!sandbox) {
      return { success: false, error: '沙箱不存在' };
    }

    try {
      await sandbox.page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
      const screenshot = await this.screenshot(instanceId);
      return { success: true, screenshot };
    } catch (error) {
      return { success: false, error: String(error), screenshot: await this.screenshot(instanceId) };
    }
  }

  /**
   * 获取页面内容
   */
  async getContent(instanceId: string): Promise<string | undefined> {
    const sandbox = this.getSandbox(instanceId);
    if (!sandbox) return undefined;

    try {
      return await sandbox.page.content();
    } catch (error) {
      console.error(`[Sandbox] 获取内容失败: ${instanceId}`, error);
      return undefined;
    }
  }
}

export const sandboxManager = new SandboxManager();
export default sandboxManager;

"""
沙箱管理器
==========

管理 Playwright 浏览器沙箱实例的生命周期

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求：
- Magentic-UI 提供沙盒内的无头浏览器控制
- 每个实例对应一个独立的浏览器上下文，确保测试隔离
"""

import logging
import base64
from typing import Dict, Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from nova_executor.audit import get_audit_logger, AuditEventType, AuditOutcome

logger = logging.getLogger(__name__)
audit_logger = get_audit_logger()


class SandboxInstance:
    """沙箱实例"""

    def __init__(self, instance_id: str, context: BrowserContext, page: Page):
        self.instance_id = instance_id
        self.context = context
        self.page = page

    async def screenshot(self) -> str:
        """截图并返回 base64"""
        buffer = await self.page.screenshot(type="png", full_page=False)
        return base64.b64encode(buffer).decode("utf-8")

    async def click(self, selector: str, **kwargs):
        """点击元素"""
        await self.page.click(selector, **kwargs)

    async def fill(self, selector: str, value: str, **kwargs):
        """填写表单"""
        await self.page.fill(selector, value, **kwargs)

    async def goto(self, url: str, **kwargs):
        """导航到 URL"""
        await self.page.goto(url, **kwargs)

    async def wait_for_timeout(self, timeout: int):
        """等待"""
        await self.page.wait_for_timeout(timeout)

    async def evaluate(self, script: str):
        """执行 JavaScript"""
        await self.page.evaluate(script)

    async def close(self):
        """关闭沙箱"""
        try:
            await self.context.close()
        except Exception as e:
            logger.warning(f"[Sandbox] 关闭上下文失败: {e}")


class SandboxManager:
    """
    沙箱管理器

    负责管理浏览器沙箱实例的生命周期
    """

    def __init__(self):
        self.sandboxes: Dict[str, SandboxInstance] = {}
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None

    async def _ensure_browser(self):
        """确保浏览器已启动"""
        if self.browser is None:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )
            logger.info("[Sandbox] 浏览器已启动")

    async def create(
        self,
        instance_id: str,
        target_url: str,
        headless: bool = True,
        viewport_width: int = 1280,
        viewport_height: int = 720,
    ) -> SandboxInstance:
        """
        创建沙箱

        Args:
            instance_id: 实例 ID
            target_url: 目标 URL
            headless: 是否无头模式
            viewport_width: 视口宽度
            viewport_height: 视口高度

        Returns:
            沙箱实例
        """
        logger.info(f"[Sandbox] 创建沙箱: {instance_id}")

        await self._ensure_browser()

        context = await self.browser.new_context(
            viewport={"width": viewport_width, "height": viewport_height},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )

        page = await context.new_page()

        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            logger.warning(f"[Sandbox] 导航失败: {target_url}, {e}")

        sandbox = SandboxInstance(instance_id, context, page)
        self.sandboxes[instance_id] = sandbox

        audit_logger.log(
            event_type=AuditEventType.SANDBOX_CREATED,
            outcome=AuditOutcome.SUCCESS,
            context=None,
            resource_type="SANDBOX",
            resource_id=instance_id,
            metadata={
                "target_url": target_url,
                "headless": headless,
                "viewport": f"{viewport_width}x{viewport_height}",
            },
        )

        return sandbox

    def get_sandbox(self, instance_id: str) -> Optional[SandboxInstance]:
        """获取沙箱实例"""
        return self.sandboxes.get(instance_id)

    async def destroy(self, instance_id: str) -> bool:
        """
        销毁沙箱

        Args:
            instance_id: 实例 ID

        Returns:
            是否成功
        """
        sandbox = self.sandboxes.get(instance_id)
        if not sandbox:
            logger.warning(f"[Sandbox] 沙箱不存在: {instance_id}")
            return False

        logger.info(f"[Sandbox] 销毁沙箱: {instance_id}")

        try:
            await sandbox.close()
            del self.sandboxes[instance_id]

            audit_logger.log(
                event_type=AuditEventType.SANDBOX_DESTROYED,
                outcome=AuditOutcome.SUCCESS,
                context=None,
                resource_type="SANDBOX",
                resource_id=instance_id,
            )

            return True
        except Exception as e:
            logger.error(f"[Sandbox] 销毁沙箱失败: {e}")

            audit_logger.log(
                event_type=AuditEventType.SANDBOX_DESTROYED,
                outcome=AuditOutcome.FAILURE,
                context=None,
                resource_type="SANDBOX",
                resource_id=instance_id,
                error_message=str(e),
            )

            return False

    async def destroy_all(self):
        """销毁所有沙箱"""
        logger.info("[Sandbox] 销毁所有沙箱...")
        instance_ids = list(self.sandboxes.keys())
        for instance_id in instance_ids:
            await self.destroy(instance_id)

    async def close(self):
        """关闭浏览器"""
        logger.info("[Sandbox] 关闭浏览器...")

        await self.destroy_all()

        if self.browser:
            try:
                await self.browser.close()
            except Exception as e:
                logger.warning(f"[Sandbox] 关闭浏览器失败: {e}")
            self.browser = None

        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception as e:
                logger.warning(f"[Sandbox] 停止 Playwright 失败: {e}")
            self.playwright = None

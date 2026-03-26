"""
沙箱管理器测试
==============

验证沙箱创建和销毁和隔离
"""

import pytest
import base64
from unittest.mock import AsyncMock, MagicMock, patch

from nova_executor.sandbox import SandboxManager, SandboxInstance


from nova_executor.types import ActionType, PlannedAction


from nova_executor.config import get_settings


settings = get_settings()


class TestSandboxManager:
    """沙箱管理器测试"""

    def test_create_sandbox_manager(self):
        """验证创建沙箱管理器"""
        manager = SandboxManager()
        assert manager.sandboxes == {}
        assert manager.playwright is None
        assert manager.browser is None

    @pytest.mark.asyncio
    async def test_create_sandbox(self, mock_playwright_browser, mock_playwright_context):
        """验证创建沙箱"""
        manager = SandboxManager()
        manager.browser = mock_playwright_browser
        mock_playwright_browser.new_context = AsyncMock(return_value=mock_playwright_context)
        mock_playwright_context.new_page = AsyncMock()
        mock_playwright_context.screenshot = AsyncMock(return_value=b"fake_screenshot")
        mock_playwright_context.goto = AsyncMock()
        mock_playwright_context.click = AsyncMock()
        mock_playwright_context.fill = AsyncMock()
        sandbox = await manager.create(
            instance_id="test-instance",
            target_url="https://example.com",
        )
        assert sandbox.instance_id == "test-instance"
        assert sandbox.context == mock_playwright_context
        assert sandbox.page == mock_playwright_context
    @pytest.mark.asyncio
    async def test_get_sandbox(self):
        """验证获取沙箱"""
        manager = SandboxManager()
        mock_sandbox = MagicMock(spec=SandboxInstance)
        manager.sandboxes["test-instance"] = mock_sandbox
        result = manager.get_sandbox("test-instance")
        assert result == mock_sandbox
    def test_get_nonexistent_sandbox(self):
        """验证获取不存在的沙箱返回 None"""
        manager = SandboxManager()
        result = manager.get_sandbox("nonexistent")
        assert result is None
    @pytest.mark.asyncio
    async def test_destroy_sandbox(self):
        """验证销毁沙箱"""
        manager = SandboxManager()
        mock_sandbox = MagicMock()
        mock_sandbox.close = AsyncMock()
        manager.sandboxes["test-instance"] = mock_sandbox
        result = await manager.destroy("test-instance")
        assert result is True
        assert "test-instance" not in manager.sandboxes
        mock_sandbox.close.assert_called_once()
    @pytest.mark.asyncio
    async def test_destroy_nonexistent_sandbox(self):
        """验证销毁不存在的沙箱"""
        manager = SandboxManager()
        result = await manager.destroy("nonexistent")
        assert result is False
    @pytest.mark.asyncio
    async def test_destroy_all_sandboxes(self):
        """验证销毁所有沙箱"""
        manager = SandboxManager()
        mock_sandbox1 = MagicMock()
        mock_sandbox1.close = AsyncMock()
        mock_sandbox2 = MagicMock()
        mock_sandbox2.close = AsyncMock()
        manager.sandboxes = {
            "instance-1": mock_sandbox1,
            "instance-2": mock_sandbox2,
        }
        await manager.destroy_all()
        assert len(manager.sandboxes) == 00


class TestSandboxInstance:
    """沙箱实例测试"""

    @pytest.mark.asyncio
    async def test_screenshot(self, mock_playwright_page):
        """验证截图"""
        mock_playwright_page.screenshot = AsyncMock(return_value=b"test_image_data")
        instance = SandboxInstance("test", MagicMock(), mock_playwright_page)
        result = await instance.screenshot()
        assert result == base64.b64encode(b"test_image_data").decode("utf-8")
    @pytest.mark.asyncio
    async def test_click(self, mock_playwright_page):
        """验证点击"""
        mock_playwright_page.click = AsyncMock()
        instance = SandboxInstance("test", MagicMock(), mock_playwright_page)
        await instance.click("#btn", timeout=5000)
        mock_playwright_page.click.assert_called_once_with("#btn", timeout=5000)
    @pytest.mark.asyncio
    async def test_fill(self, mock_playwright_page):
        """验证填写表单"""
        mock_playwright_page.fill = AsyncMock()
        instance = SandboxInstance("test", MagicMock(), mock_playwright_page)
        await instance.fill("#input", "test value")
        mock_playwright_page.fill.assert_called_once_with("#input", "test value")
    @pytest.mark.asyncio
    async def test_goto(self, mock_playwright_page):
        """验证导航"""
        mock_playwright_page.goto = AsyncMock()
        instance = SandboxInstance("test", MagicMock(), mock_playwright_page)
        await instance.goto("https://example.com")
        mock_playwright_page.goto.assert_called_once_with("https://example.com")
    @pytest.mark.asyncio
    async def test_wait_for_timeout(self, mock_playwright_page):
        """验证等待超时"""
        mock_playwright_page.wait_for_timeout = AsyncMock()
        instance = SandboxInstance("test", MagicMock(), mock_playwright_page)
        await instance.wait_for_timeout(1000)
        mock_playwright_page.wait_for_timeout.assert_called_once_with(1000)
    @pytest.mark.asyncio
    async def test_evaluate(self, mock_playwright_page):
        """验证执行 JavaScript"""
        mock_playwright_page.evaluate = AsyncMock()
        instance = SandboxInstance("test", MagicMock(), mock_playwright_page)
        await instance.evaluate("window.scrollBy(0, 300)")
        mock_playwright_page.evaluate.assert_called_once_with("window.scrollBy(0, 300)")
    @pytest.mark.asyncio
    async def test_close(self, mock_playwright_context):
        """验证关闭沙箱"""
        mock_playwright_context.close = AsyncMock()
        instance = SandboxInstance("test", mock_playwright_context, MagicMock())
        await instance.close()
        mock_playwright_context.close.assert_called_once()

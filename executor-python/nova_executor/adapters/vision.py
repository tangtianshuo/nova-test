"""
Vision 适配器
=============

调用 Fara-7B 视觉模型进行页面分析和动作规划

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求：
- Fara-7B 作为视觉大脑（可部署在 GPU 节点/NPU 端侧）
"""

import logging
import json
import base64
from typing import Protocol, Optional
from abc import ABC, abstractmethod

import httpx
from openai import AsyncOpenAI

from nova_executor.types import PlannedAction, ActionType
from nova_executor.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class VisionAdapterBase(ABC):
    """Vision 适配器基类"""

    @abstractmethod
    async def analyze_page(
        self,
        screenshot: str,
        instance_id: str,
        target_url: str,
    ) -> PlannedAction:
        """分析页面并生成动作计划"""
        pass


class VisionAdapter(VisionAdapterBase):
    """
    Vision 适配器 - 调用 Fara-7B API

    通过 HTTP 调用远程 Fara-7B 推理服务
    """

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.fara_api_key,
            base_url=settings.fara_api_url.rsplit("/v1", 1)[0] if "/v1" in settings.fara_api_url else settings.fara_api_url,
        )
        self.model_name = settings.vision_model_name

    async def analyze_page(
        self,
        screenshot: str,
        instance_id: str,
        target_url: str,
    ) -> PlannedAction:
        """
        调用 Fara-7B 分析页面

        Args:
            screenshot: 页面截图 (base64)
            instance_id: 实例 ID
            target_url: 目标 URL

        Returns:
            计划动作
        """
        logger.info(f"[Vision] 分析页面: {instance_id}")

        try:
            # 构建 prompt
            prompt = self._build_prompt(target_url)

            # 如果有截图，转换为 data URL
            image_url = None
            if screenshot:
                image_data = base64.b64decode(screenshot)
                image_url = f"data:image/png;base64,{screenshot}"

            # 调用 API
            messages = [{"role": "user", "content": []}]

            if image_url:
                messages[0]["content"].append({
                    "type": "image_url",
                    "image_url": {"url": image_url}
                })

            messages[0]["content"].append({
                "type": "text",
                "text": prompt
            })

            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=500,
            )

            result_text = response.choices[0].message.content
            logger.debug(f"[Vision] 模型输出: {result_text}")

            # 解析输出
            return self._parse_response(result_text)

        except Exception as e:
            logger.exception(f"[Vision] 分析失败: {e}")
            raise

    def _build_prompt(self, target_url: str) -> str:
        """构建分析 prompt"""
        return f"""分析当前页面，并决定下一步动作。

目标: {target_url}

请分析页面并输出 JSON 格式的动作用下格式:
{{
    "action_type": "click|type|navigate|scroll|wait",
    "selector": "CSS selector (for click/type)",
    "value": "input value (for type)",
    "url": "target URL (for navigate)",
    "confidence": 0.0-1.0,
    "thought": "分析思路"
}}

请直接输出 JSON，不要有其他内容。"""

    def _parse_response(self, response: str) -> PlannedAction:
        """解析模型输出"""
        try:
            # 尝试提取 JSON
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            data = json.loads(json_str.strip())

            return PlannedAction(
                action_type=ActionType(data.get("action_type", "click")),
                selector=data.get("selector"),
                value=data.get("value"),
                url=data.get("url"),
                confidence=float(data.get("confidence", 0.5)),
                thought=data.get("thought", ""),
            )
        except Exception as e:
            logger.warning(f"[Vision] 解析失败，使用默认动作: {e}")
            return PlannedAction(
                action_type=ActionType.CLICK,
                selector="body",
                confidence=0.3,
                thought="解析失败，使用默认动作",
            )


class MockVisionAdapter(VisionAdapterBase):
    """
    Mock Vision 适配器

    用于开发和测试
    """

    async def analyze_page(
        self,
        screenshot: str,
        instance_id: str,
        target_url: str,
    ) -> PlannedAction:
        """生成随机动作计划"""
        import random

        logger.info(f"[MockVision] 分析页面: {instance_id}")

        action_types = [ActionType.CLICK, ActionType.TYPE, ActionType.SCROLL, ActionType.WAIT]
        selectors = ["#submit", ".btn-primary", "button[type='submit']", "a.next", "input[name='q']"]
        thoughts = [
            "点击提交按钮继续流程",
            "在搜索框中输入内容",
            "向下滚动查看更多内容",
            "等待页面加载完成",
        ]

        action_type = random.choice(action_types)
        selector = random.choice(selectors) if action_type in [ActionType.CLICK, ActionType.TYPE] else None
        value = "test input" if action_type == ActionType.TYPE else None
        confidence = 0.5 + random.random() * 0.5
        thought = random.choice(thoughts)

        return PlannedAction(
            action_type=action_type,
            selector=selector,
            value=value,
            confidence=confidence,
            thought=thought,
        )

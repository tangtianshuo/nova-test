"""
Nova Test AaaS 适配器
=====================

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求：
- VisionAdapter: Fara-7B 视觉推理
- ExecutorAdapter: Magentic-UI (Playwright) 浏览器控制
- VerifierAdapter: 缺陷检测
"""

from nova_executor.adapters.vision import VisionAdapter, MockVisionAdapter
from nova_executor.adapters.executor import ExecutorAdapter, MockExecutorAdapter
from nova_executor.adapters.verifier import VerifierAdapter, MockVerifierAdapter
from nova_executor.adapters.hil_ticket import HilTicketAdapter

__all__ = [
    "VisionAdapter",
    "MockVisionAdapter",
    "ExecutorAdapter",
    "MockExecutorAdapter",
    "VerifierAdapter",
    "MockVerifierAdapter",
    "HilTicketAdapter",
]

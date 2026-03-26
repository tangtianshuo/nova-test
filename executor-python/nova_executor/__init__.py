"""
Nova Test AaaS 执行引擎
=======================
基于 FastAPI + LangGraph 实现的智能体执行引擎

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求：
- FastAPI 提供高性能的 Agent 触发接口
- LangGraph 负责维护状态机流转
- Fara-7B 作为视觉大脑
- Magentic-UI (Playwright) 提供沙盒内的无头浏览器控制

Author: Nova Team
Version: 1.0.0
"""

__version__ = "1.0.0"

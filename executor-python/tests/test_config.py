"""
配置管理测试
============

验证配置加载和验证逻辑
"""

import os
import pytest
from unittest.mock import patch

from nova_executor.config import Settings, get_settings


class TestSettings:
    """配置测试"""

    def test_default_values(self):
        """验证默认配置值"""
        settings = Settings()

        assert settings.redis_url == "redis://localhost:6379"
        assert settings.redis_queue_key == "queue:agent_tasks"
        assert settings.max_steps == 10
        assert settings.hil_confidence_threshold == 0.7
        assert settings.browser_headless is True
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8002

    def test_environment_override(self):
        """验证环境变量覆盖配置"""
        with patch.dict(os.environ, {
            "REDIS_URL": "redis://custom:6380",
            "MAX_STEPS": "20",
            "HIL_CONFIDENCE_THRESHOLD": "0.8",
        }):
            settings = Settings()
            assert settings.redis_url == "redis://custom:6380"
            assert settings.max_steps == 20
            assert settings.hil_confidence_threshold == 0.8

    def test_hil_confidence_threshold_range(self):
        """验证 HIL 置信度阈值在有效范围内"""
        settings = Settings()
        assert 0.0 <= settings.hil_confidence_threshold <= 1.0

    def test_max_steps_positive(self):
        """验证最大步数为正数"""
        settings = Settings()
        assert settings.max_steps > 0

    def test_api_port_valid(self):
        """验证 API 端口有效"""
        settings = Settings()
        assert 1 <= settings.api_port <= 65535

    def test_browser_viewport_dimensions(self):
        """验证浏览器视口尺寸"""
        settings = Settings()
        assert settings.browser_viewport_width > 0
        assert settings.browser_viewport_height > 0


class TestGetSettings:
    """获取配置单例测试"""

    def test_returns_singleton(self):
        """验证返回单例"""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_clear_cache(self):
        """验证清除缓存后返回新实例"""
        get_settings.cache_clear()
        settings1 = get_settings()
        get_settings.cache_clear()
        settings2 = get_settings()
        assert settings1 is not settings2


class TestConfigValidation:
    """配置验证测试"""

    def test_s3_config_has_defaults(self):
        """验证 S3 配置有默认值"""
        settings = Settings()
        assert settings.s3_endpoint is not None
        assert settings.s3_bucket is not None

    def test_fara_api_config(self):
        """验证 Fara API 配置"""
        settings = Settings()
        assert settings.fara_api_url is not None
        assert settings.vision_model_name is not None

    def test_log_level_default(self):
        """验证日志级别默认值"""
        settings = Settings()
        assert settings.log_level == "INFO"

    def test_redis_config_complete(self):
        """验证 Redis 配置完整"""
        settings = Settings()
        assert settings.redis_url is not None
        assert settings.redis_queue_key is not None
        assert settings.redis_stream_prefix is not None

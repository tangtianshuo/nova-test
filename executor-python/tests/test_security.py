"""
安全模块测试
============

测试敏感信息检测和脱敏功能
"""

import pytest
from nova_executor.security.patterns import (
    SensitiveType,
    SensitivePattern,
    SENSITIVE_PATTERNS,
    PATTERN_REGISTRY,
    get_patterns_by_severity,
    get_pattern_by_type,
    compile_all_patterns,
)
from nova_executor.security.sanitizer import (
    SanitizationLevel,
    SensitiveMatch,
    ScanResult,
    SensitiveSanitizer,
    get_sanitizer,
    sanitize_message,
    scan_for_secrets,
)


class TestSensitivePatterns:
    """测试敏感信息模式"""

    def test_patterns_count(self):
        """测试模式数量"""
        assert len(SENSITIVE_PATTERNS) > 0
        assert len(SENSITIVE_PATTERNS) >= 15

    def test_all_patterns_have_type(self):
        """测试所有模式都有类型"""
        for pattern in SENSITIVE_PATTERNS:
            assert pattern.type is not None
            assert isinstance(pattern.type, SensitiveType)

    def test_all_patterns_have_regex(self):
        """测试所有模式都可以编译为正则"""
        for pattern in SENSITIVE_PATTERNS:
            regex = pattern.to_regex()
            assert regex is not None

    def test_pattern_registry_completeness(self):
        """测试模式注册表完整性"""
        assert len(PATTERN_REGISTRY) == len(SENSITIVE_PATTERNS)
        for pattern in SENSITIVE_PATTERNS:
            assert pattern.type in PATTERN_REGISTRY

    def test_get_patterns_by_severity(self):
        """测试按严重程度获取模式"""
        high_patterns = get_patterns_by_severity("high")
        assert len(high_patterns) > 0

        critical_patterns = get_patterns_by_severity("critical")
        assert len(critical_patterns) > 0

        for pattern in high_patterns:
            assert pattern.severity == "high"

    def test_get_pattern_by_type(self):
        """测试按类型获取模式"""
        api_key_pattern = get_pattern_by_type(SensitiveType.API_KEY)
        assert api_key_pattern is not None
        assert api_key_pattern.type == SensitiveType.API_KEY

        none_pattern = get_pattern_by_type("non_existent")
        assert none_pattern is None

    def test_compile_all_patterns(self):
        """测试编译所有模式"""
        compiled = compile_all_patterns()
        assert len(compiled) == len(SENSITIVE_PATTERNS)

        for pattern_type, regex in compiled.items():
            assert isinstance(regex.pattern, str)


class TestSensitiveSanitizer:
    """测试敏感信息脱敏处理器"""

    def test_sanitizer_initialization(self):
        """测试脱敏器初始化"""
        sanitizer = SensitiveSanitizer()
        assert sanitizer is not None
        assert sanitizer.sanitization_level == SanitizationLevel.PARTIAL

    def test_scan_api_key(self):
        """测试扫描 API Key"""
        sanitizer = SensitiveSanitizer()
        result = sanitizer.scan_text("api_key='sk-1234567890abcdefghij'")

        assert not result.is_clean
        assert len(result.matches) > 0

        api_key_matches = [m for m in result.matches if m.match_type == SensitiveType.API_KEY]
        assert len(api_key_matches) > 0

    def test_scan_password(self):
        """测试扫描密码"""
        sanitizer = SensitiveSanitizer()
        result = sanitizer.scan_text("password='MySecretPass123'")

        assert not result.is_clean
        assert len(result.matches) > 0

    def test_scan_jwt_token(self):
        """测试扫描 JWT Token"""
        sanitizer = SensitiveSanitizer()
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        result = sanitizer.scan_text(jwt)

        assert not result.is_clean
        jwt_matches = [m for m in result.matches if m.match_type == SensitiveType.JWT_TOKEN]
        assert len(jwt_matches) > 0

    def test_scan_clean_text(self):
        """测试扫描干净文本"""
        sanitizer = SensitiveSanitizer()
        result = sanitizer.scan_text("This is a clean log message")

        assert result.is_clean
        assert len(result.matches) == 0

    def test_scan_database_url(self):
        """测试扫描数据库 URL"""
        sanitizer = SensitiveSanitizer()
        result = sanitizer.scan_text("postgresql://user:pass@localhost:5432/db")

        assert not result.is_clean
        assert len(result.matches) > 0

    def test_scan_multiple_secrets(self):
        """测试扫描多个敏感信息"""
        sanitizer = SensitiveSanitizer()
        text = "api_key='sk-1234567890abcdef' password='secret123' token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'"
        result = sanitizer.scan_text(text)

        assert not result.is_clean
        assert len(result.matches) >= 2

    def test_sanitize_partial(self):
        """测试部分脱敏"""
        sanitizer = SensitiveSanitizer(SanitizationLevel.PARTIAL)
        result = sanitizer.sanitize_text("password='MySecretPass123'")

        assert "MySecretPass123" not in result
        assert "*" in result

    def test_sanitize_full(self):
        """测试完全脱敏"""
        sanitizer = SensitiveSanitizer(SanitizationLevel.FULL)
        result = sanitizer.sanitize_text("password='MySecretPass123'")

        assert "MySecretPass123" not in result
        assert "[REDACTED_PASSWORD]" in result

    def test_sanitize_minimal(self):
        """测试最小脱敏"""
        sanitizer = SensitiveSanitizer(SanitizationLevel.MINIMAL)
        result = sanitizer.sanitize_text("password='MySecretPass123'")

        assert "MySecretPass123" not in result

    def test_sanitize_dict(self):
        """测试字典脱敏"""
        sanitizer = SensitiveSanitizer()

        data = {
            "username": "testuser",
            "password": "secret123",
            "api_key": "sk-123456",
            "data": {
                "token": "abc123"
            }
        }

        result = sanitizer.sanitize_dict(data)

        assert result["username"] == "testuser"
        assert result["password"] == "[REDACTED]"
        assert result["api_key"] == "[REDACTED]"
        assert result["data"]["token"] == "[REDACTED]"

    def test_sanitize_log(self):
        """测试日志脱敏"""
        sanitizer = SensitiveSanitizer()

        result = sanitizer.sanitize_log("User logged in with password=secret123", "INFO")

        assert "secret123" not in result

    def test_sanitize_empty_string(self):
        """测试空字符串脱敏"""
        sanitizer = SensitiveSanitizer()
        result = sanitizer.sanitize_text("")

        assert result == ""

    def test_scan_response_dict(self):
        """测试扫描响应字典"""
        sanitizer = SensitiveSanitizer()

        response = {
            "status": "success",
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "user": {
                "password": "secret123"
            }
        }

        result = sanitizer.scan_response(response)

        assert not result.is_clean
        assert len(result.matches) > 0

    def test_scan_response_bytes(self):
        """测试扫描字节响应"""
        sanitizer = SensitiveSanitizer()

        response = b'{"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"}'
        result = sanitizer.scan_response(response)

        assert not result.is_clean

    def test_scan_high_severity_only(self):
        """测试仅扫描高严重程度"""
        sanitizer = SensitiveSanitizer()

        text = "api_key='sk-1234567890abcdefghij' email='test@example.com'"
        result = sanitizer.scan_text(text, scan_high_severity_only=True)

        assert not result.is_clean
        high_severity = result.get_high_severity_matches()
        assert len(high_severity) > 0

    def test_scan_result_summary(self):
        """测试扫描结果摘要"""
        sanitizer = SensitiveSanitizer()
        result = sanitizer.scan_text("api_key='sk-123' password='secret'")

        summary = result.get_summary()

        assert "total_matches" in summary
        assert "is_clean" in summary
        assert "severity_counts" in summary
        assert "match_types" in summary

    def test_scan_result_add_match(self):
        """测试扫描结果添加匹配"""
        result = ScanResult(text="test")
        assert result.is_clean

        match = SensitiveMatch(
            match_type=SensitiveType.API_KEY,
            matched_text="sk-123",
            start=0,
            end=6,
            pattern_name="API Key",
            severity="high",
            masked_text="***",
        )

        result.add_match(match)

        assert not result.is_clean
        assert len(result.matches) == 1
        assert result.severity_counts["high"] == 1

    def test_scan_result_get_high_severity(self):
        """测试获取高严重程度匹配"""
        result = ScanResult(text="test")

        high_match = SensitiveMatch(
            match_type=SensitiveType.API_KEY,
            matched_text="sk-123",
            start=0,
            end=6,
            pattern_name="API Key",
            severity="high",
            masked_text="***",
        )

        low_match = SensitiveMatch(
            match_type=SensitiveType.EMAIL,
            matched_text="test@example.com",
            start=10,
            end=26,
            pattern_name="Email",
            severity="low",
            masked_text="te***@example.com",
        )

        result.add_match(high_match)
        result.add_match(low_match)

        high_matches = result.get_high_severity_matches()
        assert len(high_matches) == 1
        assert high_matches[0].severity == "high"


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_get_sanitizer(self):
        """测试获取全局脱敏器"""
        sanitizer1 = get_sanitizer()
        sanitizer2 = get_sanitizer()

        assert sanitizer1 is sanitizer2

    def test_sanitize_message(self):
        """测试便捷脱敏函数"""
        result = sanitize_message("password='MySecretPass'")

        assert "MySecretPass" not in result

    def test_scan_for_secrets(self):
        """测试便捷扫描函数"""
        result = scan_for_secrets("password='MySecretPass123'")

        assert not result.is_clean
        assert len(result.matches) > 0

    def test_sanitize_message_full_level(self):
        """测试不同脱敏级别"""
        result = sanitize_message("password='MySecretPass'", level=SanitizationLevel.FULL)

        assert "MySecretPass" not in result


class TestEdgeCases:
    """测试边界情况"""

    def test_scan_unicode(self):
        """测试 Unicode 文本扫描"""
        sanitizer = SensitiveSanitizer()
        result = sanitizer.scan_text("密码='中文密码123' password='MySecret'")

        assert not result.is_clean

    def test_scan_overlapping_matches(self):
        """测试重叠匹配"""
        sanitizer = SensitiveSanitizer()
        text = "api_key='sk-1234567890abcdefghij'"
        result = sanitizer.scan_text(text)

        assert len(result.matches) > 0

    def test_sanitize_very_long_secret(self):
        """测试非常长的密钥"""
        sanitizer = SensitiveSanitizer()
        long_secret = "a" * 1000
        text = f"password='{long_secret}'"

        result = sanitizer.sanitize_text(text)

        assert "*" in result
        assert "a" * 1000 not in result

    def test_sanitize_dict_with_none(self):
        """测试包含 None 的字典"""
        sanitizer = SensitiveSanitizer()

        data = {
            "username": None,
            "password": "secret",
        }

        result = sanitizer.sanitize_dict(data)

        assert result["username"] is None
        assert result["password"] == "[REDACTED]"

    def test_sanitize_dict_with_numbers(self):
        """测试包含数字的字典"""
        sanitizer = SensitiveSanitizer()

        data = {
            "user_id": 12345,
            "api_key": "sk-123456",
        }

        result = sanitizer.sanitize_dict(data)

        assert result["user_id"] == 12345
        assert result["api_key"] == "[REDACTED]"

    def test_scan_none_text(self):
        """测试 None 文本"""
        sanitizer = SensitiveSanitizer()

        result = sanitizer.sanitize_text(None)

        assert result is None


class TestLogIntegration:
    """测试日志集成"""

    def test_logger_sanitization_enabled(self):
        """测试日志器启用脱敏"""
        from nova_executor.logging.logger import Logger

        logger = Logger("test", enable_sanitization=True)
        assert logger.enable_sanitization is True
        assert logger._sanitizer is not None

    def test_logger_sanitization_disabled(self):
        """测试日志器禁用脱敏"""
        from nova_executor.logging.logger import Logger

        logger = Logger("test", enable_sanitization=False)
        assert logger.enable_sanitization is False
        assert logger._sanitizer is None

    def test_logger_sanitize_message(self):
        """测试日志器脱敏消息"""
        from nova_executor.logging.logger import Logger

        logger = Logger("test", enable_sanitization=True)
        message = "password='MySecretPass'"

        sanitized, has_sensitive = logger._sanitize_message(message, "INFO")

        assert has_sensitive is True
        assert "MySecretPass" not in sanitized

    def test_logger_sanitize_clean_message(self):
        """测试日志器脱敏干净消息"""
        from nova_executor.logging.logger import Logger

        logger = Logger("test", enable_sanitization=True)
        message = "This is a clean log message"

        sanitized, has_sensitive = logger._sanitize_message(message, "INFO")

        assert has_sensitive is False
        assert sanitized == message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

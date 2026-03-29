"""
敏感信息脱敏处理器
==================

提供敏感信息的检测、匹配和脱敏处理功能
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from enum import Enum

from .patterns import (
    SENSITIVE_PATTERNS,
    SensitiveType,
    SensitivePattern,
    compile_all_patterns,
)


class SanitizationLevel(str, Enum):
    """脱敏级别"""
    FULL = "full"
    PARTIAL = "partial"
    MINIMAL = "minimal"


@dataclass
class SensitiveMatch:
    """
    敏感信息匹配结果

    Attributes:
        match_type: 匹配类型
        matched_text: 匹配的原始文本
        start: 匹配起始位置
        end: 匹配结束位置
        pattern_name: 模式名称
        severity: 严重程度
        masked_text: 脱敏后的文本
    """
    match_type: SensitiveType
    matched_text: str
    start: int
    end: int
    pattern_name: str
    severity: str
    masked_text: str


@dataclass
class ScanResult:
    """
    扫描结果

    Attributes:
        text: 原始文本
        matches: 敏感信息匹配列表
        is_clean: 是否未检测到敏感信息
        severity_counts: 各严重程度的匹配数量
    """
    text: str
    matches: List[SensitiveMatch] = field(default_factory=list)
    is_clean: bool = True
    severity_counts: Dict[str, int] = field(default_factory=dict)

    def add_match(self, match: SensitiveMatch):
        """添加匹配结果"""
        self.matches.append(match)
        self.is_clean = False
        self.severity_counts[match.severity] = self.severity_counts.get(match.severity, 0) + 1

    def get_high_severity_matches(self) -> List[SensitiveMatch]:
        """获取高严重程度的匹配"""
        return [m for m in self.matches if m.severity in ("high", "critical")]

    def get_summary(self) -> Dict[str, Any]:
        """获取扫描摘要"""
        return {
            "total_matches": len(self.matches),
            "is_clean": self.is_clean,
            "severity_counts": self.severity_counts,
            "match_types": [m.match_type.value for m in self.matches],
        }


class SensitiveSanitizer:
    """
    敏感信息脱敏处理器

    提供：
    1. 敏感信息检测
    2. 脱敏处理
    3. 日志和响应扫描
    """

    def __init__(self, sanitization_level: SanitizationLevel = SanitizationLevel.PARTIAL):
        """
        初始化脱敏处理器

        Args:
            sanitization_level: 脱敏级别
                - FULL: 完全脱敏，显示 [REDACTED]
                - PARTIAL: 部分脱敏，保留前后各1-2个字符
                - MINIMAL: 最小脱敏，仅替换中间部分
        """
        self.sanitization_level = sanitization_level
        self.compiled_patterns = compile_all_patterns()

    def _mask_text(self, text: str, pattern: SensitivePattern) -> str:
        """
        根据脱敏级别生成脱敏文本

        Args:
            text: 原始匹配文本
            pattern: 匹配的模式

        Returns:
            脱敏后的文本
        """
        if self.sanitization_level == SanitizationLevel.FULL:
            return f"[REDACTED_{pattern.type.value.upper()}]"

        length = len(text)
        if length <= 4:
            return "*" * length

        if self.sanitization_level == SanitizationLevel.MINIMAL:
            visible_chars = min(2, length // 4)
            return text[:visible_chars] + "*" * (length - visible_chars * 2) + text[-visible_chars:]

        visible_chars = min(3, length // 4)
        return text[:visible_chars] + "*" * (length - visible_chars * 2) + text[-visible_chars:]

    def scan_text(self, text: str, scan_high_severity_only: bool = False) -> ScanResult:
        """
        扫描文本中的敏感信息

        Args:
            text: 待扫描的文本
            scan_high_severity_only: 是否仅扫描高严重程度的模式

        Returns:
            ScanResult 扫描结果
        """
        result = ScanResult(text=text)

        for pattern in SENSITIVE_PATTERNS:
            if scan_high_severity_only and pattern.severity not in ("high", "critical"):
                continue

            regex = self.compiled_patterns.get(pattern.type)
            if not regex:
                continue

            for match in regex.finditer(text):
                matched_text = match.group(0)
                masked_text = self._mask_text(matched_text, pattern)

                sensitive_match = SensitiveMatch(
                    match_type=pattern.type,
                    matched_text=matched_text,
                    start=match.start(),
                    end=match.end(),
                    pattern_name=pattern.name,
                    severity=pattern.severity,
                    masked_text=masked_text,
                )
                result.add_match(sensitive_match)

        return result

    def sanitize_text(self, text: str, scan_high_severity_only: bool = False) -> str:
        """
        扫描并脱敏文本中的敏感信息

        Args:
            text: 待处理的文本
            scan_high_severity_only: 是否仅扫描高严重程度的模式

        Returns:
            脱敏后的文本
        """
        if not text:
            return text

        result = self.scan_text(text, scan_high_severity_only)

        if not result.matches:
            return text

        sanitized_parts = []
        last_end = 0

        sorted_matches = sorted(result.matches, key=lambda m: m.start)

        for match in sorted_matches:
            sanitized_parts.append(text[last_end:match.start])
            sanitized_parts.append(match.masked_text)
            last_end = match.end

        sanitized_parts.append(text[last_end:])

        return "".join(sanitized_parts)

    def sanitize_dict(self, data: Dict[str, Any], sensitive_keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        递归脱敏字典中的敏感字段

        Args:
            data: 待处理的字典
            sensitive_keys: 敏感字段名称列表

        Returns:
            脱敏后的字典
        """
        if sensitive_keys is None:
            sensitive_keys = [
                "password", "passwd", "pwd", "secret", "token",
                "api_key", "apiKey", "api_key", "apikey",
                "access_token", "accessToken",
                "auth_token", "authToken",
                "secret_key", "secretKey",
                "private_key", "privateKey",
                "credential", "credentials",
                "authorization", "Authorization",
            ]

        result = {}

        for key, value in data.items():
            key_lower = key.lower()

            if key_lower in sensitive_keys:
                result[key] = "[REDACTED]"
            elif isinstance(value, dict):
                result[key] = self.sanitize_dict(value, sensitive_keys)
            elif isinstance(value, str):
                scan_result = self.scan_text(value, scan_high_severity_only=True)
                if scan_result.is_clean:
                    result[key] = value
                else:
                    result[key] = self.sanitize_text(value, scan_high_severity_only=True)
            elif isinstance(value, list):
                result[key] = [
                    self.sanitize_dict(item, sensitive_keys) if isinstance(item, dict)
                    else self.sanitize_text(str(item), scan_high_severity_only=True) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                result[key] = value

        return result

    def sanitize_log(self, log_message: str, log_level: str = "INFO") -> str:
        """
        脱敏日志消息

        Args:
            log_message: 日志消息
            log_level: 日志级别

        Returns:
            脱敏后的日志消息
        """
        scan_high_severity_only = log_level in ("DEBUG", "INFO")
        return self.sanitize_text(log_message, scan_high_severity_only=scan_high_severity_only)

    def scan_response(self, response_data: Union[Dict, str, bytes]) -> ScanResult:
        """
        扫描 API 响应中的敏感信息

        Args:
            response_data: 响应数据

        Returns:
            ScanResult 扫描结果
        """
        if isinstance(response_data, bytes):
            response_data = response_data.decode("utf-8", errors="ignore")

        if isinstance(response_data, dict):
            response_text = self._flatten_dict_to_text(response_data)
        else:
            response_text = str(response_data)

        return self.scan_text(response_text, scan_high_severity_only=False)

    def _flatten_dict_to_text(self, data: Dict[str, Any], separator: str = " ") -> str:
        """
        将字典展平为文本

        Args:
            data: 字典数据
            separator: 分隔符

        Returns:
            展平后的文本
        """
        parts = []

        def flatten(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    parts.append(f"{key}: {value}")
                    flatten(value)
            elif isinstance(obj, list):
                for item in obj:
                    flatten(item)
            else:
                parts.append(str(obj))

        flatten(data)
        return separator.join(parts)


_default_sanitizer: Optional[SensitiveSanitizer] = None


def get_sanitizer(sanitization_level: SanitizationLevel = SanitizationLevel.PARTIAL) -> SensitiveSanitizer:
    """
    获取全局脱敏处理器实例

    Args:
        sanitization_level: 脱敏级别

    Returns:
        SensitiveSanitizer 实例
    """
    global _default_sanitizer
    if _default_sanitizer is None:
        _default_sanitizer = SensitiveSanitizer(sanitization_level)
    return _default_sanitizer


def sanitize_message(message: str, level: SanitizationLevel = SanitizationLevel.PARTIAL) -> str:
    """
    便捷函数：快速脱敏消息

    Args:
        message: 待处理的消息
        level: 脱敏级别

    Returns:
        脱敏后的消息
    """
    sanitizer = get_sanitizer(level)
    return sanitizer.sanitize_text(message, scan_high_severity_only=False)


def scan_for_secrets(text: str) -> ScanResult:
    """
    便捷函数：快速扫描敏感信息

    Args:
        text: 待扫描的文本

    Returns:
        ScanResult 扫描结果
    """
    sanitizer = get_sanitizer()
    return sanitizer.scan_text(text)

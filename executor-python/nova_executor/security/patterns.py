"""
敏感信息模式库
=============

定义常见敏感信息的正则表达式模式，用于检测和脱敏处理
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional


class SensitiveType(str, Enum):
    """敏感信息类型枚举"""
    API_KEY = "api_key"
    TOKEN = "token"
    PASSWORD = "password"
    SECRET_KEY = "secret_key"
    PRIVATE_KEY = "private_key"
    ACCESS_KEY = "access_key"
    AUTH_TOKEN = "auth_token"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"
    DATABASE_URL = "database_url"
    DATABASE_CONNECTION = "database_connection"
    JWT_TOKEN = "jwt_token"
    OAUTH_TOKEN = "oauth_token"
    AWS_ACCESS_KEY = "aws_access_key"
    AWS_SECRET_KEY = "aws_secret_key"
    SSH_KEY = "ssh_key"
    GITHUB_TOKEN = "github_token"
    CREDIT_CARD = "credit_card"
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"


@dataclass
class SensitivePattern:
    """
    敏感信息模式定义

    Attributes:
        type: 敏感信息类型
        pattern: 正则表达式模式
        name: 模式名称
        description: 模式描述
        examples: 示例
        severity: 严重程度 (high/medium/low)
    """
    type: SensitiveType
    pattern: str
    name: str
    description: str
    examples: List[str]
    severity: str = "high"

    def to_regex(self) -> re.Pattern:
        """编译正则表达式"""
        return re.compile(self.pattern, re.IGNORECASE)


SENSITIVE_PATTERNS: List[SensitivePattern] = [
    # API Key 模式
    SensitivePattern(
        type=SensitiveType.API_KEY,
        pattern=r'(?i)(api[_-]?key|apikey|api[_-]?secret)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
        name="Generic API Key",
        description="通用 API Key",
        examples=["api_key='sk-1234567890abcdef'", "apiKey: abc123def456"],
        severity="high"
    ),
    # Token 模式
    SensitivePattern(
        type=SensitiveType.TOKEN,
        pattern=r'(?i)(token|access[_-]?token)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{20,})["\']?',
        name="Access Token",
        description="访问令牌",
        examples=["token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'", "access_token: abc123"],
        severity="high"
    ),
    # Bearer Token
    SensitivePattern(
        type=SensitiveType.BEARER_TOKEN,
        pattern=r'(?i)bearer\s+([a-zA-Z0-9_\-\.]+)',
        name="Bearer Token",
        description="Bearer 认证令牌",
        examples=["Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"],
        severity="high"
    ),
    # JWT Token
    SensitivePattern(
        type=SensitiveType.JWT_TOKEN,
        pattern=r'eyJ[a-zA-Z0-9_\-]+\.eyJ[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+',
        name="JWT Token",
        description="JSON Web Token",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"],
        severity="high"
    ),
    # 密码模式
    SensitivePattern(
        type=SensitiveType.PASSWORD,
        pattern=r'(?i)(password|passwd|pwd|secret)["\']?\s*[:=]\s*["\']?([^"\'\s]{8,})["\']?',
        name="Password",
        description="密码字段",
        examples=["password='MySecretPass123'", "pwd: admin123"],
        severity="high"
    ),
    # 密钥模式
    SensitivePattern(
        type=SensitiveType.SECRET_KEY,
        pattern=r'(?i)(secret[_-]?key|secretkey)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{16,})["\']?',
        name="Secret Key",
        description="密钥",
        examples=["SECRET_KEY='sk_live_abc123def456'", "secret_key: xyz789"],
        severity="high"
    ),
    # AWS Access Key
    SensitivePattern(
        type=SensitiveType.AWS_ACCESS_KEY,
        pattern=r'(?i)(aws[_-]?access[_-]?key[_-]?id)["\']?\s*[:=]\s*["\']?([A-Z0-9]{16,})["\']?',
        name="AWS Access Key",
        description="AWS 访问密钥",
        examples=["AWS_ACCESS_KEY_ID='AKIAIOSFODNN7EXAMPLE'"],
        severity="high"
    ),
    # AWS Secret Key
    SensitivePattern(
        type=SensitiveType.AWS_SECRET_KEY,
        pattern=r'(?i)aws[_-]?secret[_-]?key["\']?\s*[:=]\s*["\']?([a-zA-Z0-9/+=]{40})["\']?',
        name="AWS Secret Key",
        description="AWS 私有密钥",
        examples=["AWS_SECRET_ACCESS_KEY='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'"],
        severity="high"
    ),
    # GitHub Token
    SensitivePattern(
        type=SensitiveType.GITHUB_TOKEN,
        pattern=r'(?i)github[_-]?(token|personal[_-]?access[_-]?token)["\']?\s*[:=]\s*["\']?(ghp_[a-zA-Z0-9]{36}|gho_[a-zA-Z0-9]{36})["\']?',
        name="GitHub Token",
        description="GitHub 个人访问令牌",
        examples=["GITHUB_TOKEN='ghp_1234567890abcdefghijklmnopqrstuvwxyz'"],
        severity="high"
    ),
    # 数据库连接 URL
    SensitivePattern(
        type=SensitiveType.DATABASE_URL,
        pattern=r'(?i)(database[_-]?url|db[_-]?url|mongodb[_-]?url|postgres[_-]?url|mysql[_-]?url)["\']?\s*[:=]\s*["\']?(mysql|postgres|mongodb|sqlite)://[^\s"\']+["\']?',
        name="Database URL",
        description="数据库连接 URL",
        examples=["DATABASE_URL='postgresql://user:pass@localhost:5432/db'"],
        severity="high"
    ),
    # 数据库连接字符串（包含密码）
    SensitivePattern(
        type=SensitiveType.DATABASE_CONNECTION,
        pattern=r'(mysql|postgres|postgresql|mongodb|sqlite)://[^:]+:[^@]+@',
        name="Database Connection String",
        description="数据库连接字符串",
        examples=["postgresql://admin:secret123@localhost:5432/mydb"],
        severity="high"
    ),
    # OAuth Token
    SensitivePattern(
        type=SensitiveType.OAUTH_TOKEN,
        pattern=r'(?i)(oauth[_-]?token|oauth[_-]?access[_-]?token)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
        name="OAuth Token",
        description="OAuth 访问令牌",
        examples=["oauth_token='ya29.a0AfH6SMBx...'", "oauth_access_token: abc123"],
        severity="high"
    ),
    # Basic Auth
    SensitivePattern(
        type=SensitiveType.BASIC_AUTH,
        pattern=r'(?i)authorization["\']?\s*[:=]\s*["\']?basic\s+([a-zA-Z0-9+/=]+)',
        name="Basic Authentication",
        description="Basic 认证信息",
        examples=["Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ="],
        severity="high"
    ),
    # 私钥
    SensitivePattern(
        type=SensitiveType.PRIVATE_KEY,
        pattern=r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----',
        name="Private Key",
        description="私有密钥",
        examples=["-----BEGIN RSA PRIVATE KEY-----"],
        severity="critical"
    ),
    # SSH 密钥
    SensitivePattern(
        type=SensitiveType.SSH_KEY,
        pattern=r'-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----',
        name="SSH Private Key",
        description="SSH 私有密钥",
        examples=["-----BEGIN OPENSSH PRIVATE KEY-----"],
        severity="critical"
    ),
    # 信用卡号
    SensitivePattern(
        type=SensitiveType.CREDIT_CARD,
        pattern=r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',
        name="Credit Card Number",
        description="信用卡号码",
        examples=["4111111111111111", "5500000000000004"],
        severity="critical"
    ),
    # 邮箱地址（降低敏感度，作为辅助检测）
    SensitivePattern(
        type=SensitiveType.EMAIL,
        pattern=r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
        name="Email Address",
        description="邮箱地址",
        examples=["user@example.com"],
        severity="low"
    ),
    # 电话号码
    SensitivePattern(
        type=SensitiveType.PHONE,
        pattern=r'\b1[3-9]\d{9}\b',
        name="Phone Number",
        description="中国手机号码",
        examples=["13812345678"],
        severity="medium"
    ),
    # 社会保险号（中国）
    SensitivePattern(
        type=SensitiveType.SSN,
        pattern=r'\b[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[0-9Xx]\b',
        name="Chinese SSN",
        description="中国身份证号",
        examples=["110101199003074518"],
        severity="high"
    ),
]


PATTERN_REGISTRY: Dict[SensitiveType, SensitivePattern] = {
    pattern.type: pattern for pattern in SENSITIVE_PATTERNS
}


def get_patterns_by_severity(severity: str) -> List[SensitivePattern]:
    """
    根据严重程度获取模式列表

    Args:
        severity: 严重程度 (high/medium/low/critical)

    Returns:
        匹配严重程度的模式列表
    """
    return [p for p in SENSITIVE_PATTERNS if p.severity == severity]


def get_pattern_by_type(pattern_type: SensitiveType) -> Optional[SensitivePattern]:
    """
    根据类型获取模式

    Args:
        pattern_type: 敏感信息类型

    Returns:
        对应的模式，如果不存在返回 None
    """
    return PATTERN_REGISTRY.get(pattern_type)


def compile_all_patterns() -> Dict[SensitiveType, re.Pattern]:
    """
    编译所有模式为正则表达式对象

    Returns:
        类型到正则表达式的映射
    """
    return {
        pattern.type: pattern.to_regex()
        for pattern in SENSITIVE_PATTERNS
    }

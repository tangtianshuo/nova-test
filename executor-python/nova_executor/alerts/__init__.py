"""
告警模块
==========

告警规则和通知
"""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """告警级别"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertType(str, Enum):
    """告警类型"""
    INSTANCE_FAILED = "instance_failed"
    HIL_TIMEOUT = "hil_timeout"
    HIGH_FAILURE_RATE = "high_failure_rate"
    SLOW_EXECUTION = "slow_execution"
    API_ERROR = "api_error"


@dataclass
class Alert:
    """告警"""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    instance_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class AlertRule:
    """告警规则"""

    def __init__(
        self,
        name: str,
        alert_type: AlertType,
        condition: callable,
        severity: AlertSeverity = AlertSeverity.MEDIUM,
    ):
        self.name = name
        self.alert_type = alert_type
        self.condition = condition
        self.severity = severity

    def evaluate(self, context: Dict[str, Any]) -> Optional[Alert]:
        """评估规则"""
        if self.condition(context):
            return Alert(
                alert_id=f"alert-{datetime.utcnow().timestamp()}",
                alert_type=self.alert_type,
                severity=self.severity,
                message=f"Alert triggered: {self.name}",
                instance_id=context.get("instance_id"),
                metadata=context,
            )
        return None


class AlertManager:
    """告警管理器"""

    def __init__(self):
        self.rules: List[AlertRule] = []
        self.alerts: List[Alert] = []
        self._init_default_rules()

    def _init_default_rules(self):
        """初始化默认规则"""
        # 实例失败告警
        self.add_rule(AlertRule(
            name="实例失败",
            alert_type=AlertType.INSTANCE_FAILED,
            severity=AlertSeverity.HIGH,
            condition=lambda ctx: ctx.get("status") == "FAILED",
        ))

        # HIL 超时告警
        self.add_rule(AlertRule(
            name="HIL 超时",
            alert_type=AlertType.HIL_TIMEOUT,
            severity=AlertSeverity.MEDIUM,
            condition=lambda ctx: ctx.get("hil_waiting_time", 0) > 300,  # 5 分钟
        ))

        # 高失败率告警
        self.add_rule(AlertRule(
            name="高失败率",
            alert_type=AlertType.HIGH_FAILURE_RATE,
            severity=AlertSeverity.HIGH,
            condition=lambda ctx: ctx.get("failure_rate", 0) > 0.5,
        ))

    def add_rule(self, rule: AlertRule):
        """添加规则"""
        self.rules.append(rule)
        logger.info(f"[AlertManager] 添加规则: {rule.name}")

    def evaluate_all(self, context: Dict[str, Any]) -> List[Alert]:
        """评估所有规则"""
        triggered = []
        for rule in self.rules:
            alert = rule.evaluate(context)
            if alert:
                triggered.append(alert)
                self.alerts.append(alert)
        return triggered

    def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        limit: int = 100,
    ) -> List[Alert]:
        """获取告警"""
        if severity:
            return [a for a in self.alerts[-limit:] if a.severity == severity]
        return self.alerts[-limit:]

    def clear(self):
        """清除告警"""
        self.alerts.clear()


# 全局告警管理器
alert_manager = AlertManager()

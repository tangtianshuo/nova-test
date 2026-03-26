"""
追踪器
========

OpenTelemetry 追踪实现

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求
"""

import logging
import uuid
from typing import Optional, Dict, Any
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

# 追踪上下文变量
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
span_id_var: ContextVar[Optional[str]] = ContextVar("span_id", default=None)


class SpanKind(str, Enum):
    """Span 类型"""
    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanStatus(str, Enum):
    """Span 状态"""
    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


@dataclass
class Span:
    """
    追踪 Span

    代表一个操作单元
    """
    name: str
    trace_id: str
    span_id: str
    kind: SpanKind = SpanKind.INTERNAL
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status: SpanStatus = SpanStatus.UNSET
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: list = field(default_factory=list)
    links: list = field(default_factory=list)
    parent_span_id: Optional[str] = None

    def set_attribute(self, key: str, value: Any):
        """设置属性"""
        self.attributes[key] = value

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """添加事件"""
        self.events.append({
            "name": name,
            "timestamp": datetime.utcnow().isoformat(),
            "attributes": attributes or {},
        })

    def set_status(self, status: SpanStatus, description: str = ""):
        """设置状态"""
        self.status = status

    def end(self):
        """结束 Span"""
        self.end_time = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "name": self.name,
            "kind": self.kind.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status.value,
            "attributes": self.attributes,
            "events": self.events,
            "links": self.links,
            "parent_span_id": self.parent_span_id,
        }


class Tracer:
    """
    追踪器

    实现 OpenTelemetry 追踪接口
    """

    def __init__(self, service_name: str = "nova-executor"):
        self.service_name = service_name
        self._spans: list[Span] = []

    def generate_trace_id(self) -> str:
        """生成 Trace ID"""
        return uuid.uuid4().hex[:32]

    def generate_span_id(self) -> str:
        """生成 Span ID"""
        return uuid.uuid4().hex[:16]

    def start_span(
        self,
        name: str,
        parent_context: Optional[Dict[str, str]] = None,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Span:
        """
        开始 Span

        Args:
            name: Span 名称
            parent_context: 父上下文
            kind: Span 类型
            attributes: 属性

        Returns:
            Span 实例
        """
        trace_id = parent_context.get("trace_id") if parent_context else None
        if not trace_id:
            trace_id = self.generate_trace_id()

        span_id = self.generate_span_id()
        parent_span_id = parent_context.get("span_id") if parent_context else None

        span = Span(
            name=name,
            trace_id=trace_id,
            span_id=span_id,
            kind=kind,
            parent_span_id=parent_span_id,
        )

        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, v)

        # 设置上下文变量
        trace_id_var.set(trace_id)
        span_id_var.set(span_id)

        self._spans.append(span)
        logger.debug(f"[Tracer] 开始 Span: {name}, trace_id={trace_id}")

        return span

    def end_span(self, span: Span):
        """结束 Span"""
        span.end()
        logger.debug(f"[Tracer] 结束 Span: {span.name}, trace_id={span.trace_id}")

    def get_current_context(self) -> Dict[str, str]:
        """获取当前上下文"""
        return {
            "trace_id": trace_id_var.get(),
            "span_id": span_id_var.get(),
        }

    def with_context(self, context: Dict[str, str]):
        """创建上下文管理器"""
        class ContextManager:
            def __enter__(self):
                self.prev_trace = trace_id_var.set(context.get("trace_id"))
                self.prev_span = span_id_var.set(context.get("span_id"))
                return context

            def __exit__(self, *args):
                trace_id_var.reset(self.prev_trace)
                span_id_var.reset(self.prev_span)

        return ContextManager()


# 全局追踪器实例
_tracer: Optional[Tracer] = None


def get_tracer(service_name: str = "nova-executor") -> Tracer:
    """获取追踪器实例"""
    global _tracer
    if _tracer is None:
        _tracer = Tracer(service_name)
    return _tracer

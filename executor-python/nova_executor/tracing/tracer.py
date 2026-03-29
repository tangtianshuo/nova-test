"""
追踪器
========

OpenTelemetry 追踪实现

严格遵循 docs/design/02_概要设计文档_v1.0.md 的技术栈要求
"""

import logging
import uuid
from typing import Optional, Dict, Any, Callable
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from contextlib import contextmanager

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.trace import SpanKind, Status, StatusCode
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None
    SpanKind = None

logger = logging.getLogger(__name__)


class SpanKindEnum(str, Enum):
    """Span 类型"""
    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanStatusEnum(str, Enum):
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
    kind: SpanKindEnum = SpanKindEnum.INTERNAL
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status: SpanStatusEnum = SpanStatusEnum.UNSET
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: list = field(default_factory=list)
    links: list = field(default_factory=list)
    parent_span_id: Optional[str] = None
    _otel_span: Optional[Any] = None

    def set_attribute(self, key: str, value: Any):
        """设置属性"""
        self.attributes[key] = value
        if self._otel_span:
            self._otel_span.set_attribute(key, value)

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """添加事件"""
        event_data = {
            "name": name,
            "timestamp": datetime.utcnow().isoformat(),
            "attributes": attributes or {},
        }
        self.events.append(event_data)
        if self._otel_span:
            self._otel_span.add_event(name, attributes)

    def set_status(self, status: SpanStatusEnum, description: str = ""):
        """设置状态"""
        self.status = status
        if self._otel_span:
            otel_status = Status(StatusCode.OK if status == SpanStatusEnum.OK else StatusCode.ERROR)
            self._otel_span.set_status(otel_status, description)

    def record_exception(self, exception: Exception):
        """记录异常"""
        self.add_event("exception", {
            "type": type(exception).__name__,
            "message": str(exception),
        })

    def end(self):
        """结束 Span"""
        self.end_time = datetime.utcnow()
        if self._otel_span:
            self._otel_span.end()

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
        self._otel_tracer = None

        if OTEL_AVAILABLE:
            provider = TracerProvider()
            processor = BatchSpanProcessor(ConsoleSpanExporter())
            provider.add_span_processor(processor)
            trace.set_tracer_provider(provider)
            self._otel_tracer = trace.get_tracer(service_name)

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
        kind: SpanKindEnum = SpanKindEnum.INTERNAL,
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

        if self._otel_tracer:
            otel_kind = SpanKind.INTERNAL
            if kind == SpanKindEnum.SERVER:
                otel_kind = SpanKind.SERVER
            elif kind == SpanKindEnum.CLIENT:
                otel_kind = SpanKind.CLIENT

            otel_span = self._otel_tracer.start_span(name, kind=otel_kind)
            span._otel_span = otel_span

        self._spans.append(span)
        logger.debug(f"[Tracer] 开始 Span: {name}, trace_id={trace_id}")

        return span

    def end_span(self, span: Span):
        """结束 Span"""
        span.end()
        logger.debug(f"[Tracer] 结束 Span: {span.name}, trace_id={span.trace_id}")

    def get_current_context(self) -> Dict[str, str]:
        """获取当前上下文"""
        if self._otel_tracer:
            current_span = trace.get_current_span()
            if current_span:
                ctx = current_span.get_span_context()
                if ctx:
                    return {
                        "trace_id": format(ctx.trace_id, "032x"),
                        "span_id": format(ctx.span_id, "016x"),
                    }
        return {
            "trace_id": None,
            "span_id": None,
        }

    def with_context(self, context: Dict[str, str]):
        """创建上下文管理器"""
        class ContextManager:
            def __enter__(self):
                return context

            def __exit__(self, *args):
                pass

        return ContextManager()

    @contextmanager
    def span(
        self,
        name: str,
        parent_context: Optional[Dict[str, str]] = None,
        kind: SpanKindEnum = SpanKindEnum.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """
        上下文管理器创建 Span

        Args:
            name: Span 名称
            parent_context: 父上下文
            kind: Span 类型
            attributes: 属性

        Yields:
            Span 实例
        """
        span = self.start_span(name, parent_context, kind, attributes)
        try:
            yield span
            span.set_status(SpanStatusEnum.OK)
        except Exception as e:
            span.set_status(SpanStatusEnum.ERROR, str(e))
            span.record_exception(e)
            raise
        finally:
            self.end_span(span)

    def record_exception(self, span: Span, exception: Exception):
        """记录异常"""
        span.add_event("exception", {
            "type": type(exception).__name__,
            "message": str(exception),
        })

    def record_exception_in_span(self, exception: Exception):
        """记录异常到当前 Span"""
        pass


_tracer: Optional[Tracer] = None


def get_tracer(service_name: str = "nova-executor") -> Tracer:
    """获取追踪器实例"""
    global _tracer
    if _tracer is None:
        _tracer = Tracer(service_name)
    return _tracer


def inject_trace_context(carrier: Dict[str, str]) -> Dict[str, str]:
    """
    注入追踪上下文到 carrier

    Args:
        carrier: 携带上下文的字典

    Returns:
        包含上下文的 carrier
    """
    if OTEL_AVAILABLE:
        propagator = TraceContextTextMapPropagator()
        propagator.inject(carrier)
    return carrier


def extract_trace_context(carrier: Dict[str, str]) -> Optional[Dict[str, str]]:
    """
    从 carrier 提取追踪上下文

    Args:
        carrier: 携带上下文的字典

    Returns:
        追踪上下文
    """
    if OTEL_AVAILABLE:
        propagator = TraceContextTextMapPropagator()
        ctx = propagator.extract(carrier)
        if ctx:
            span = trace.get_span(ctx)
            if span:
                ctx = span.get_span_context()
                return {
                    "trace_id": format(ctx.trace_id, "032x"),
                    "span_id": format(ctx.span_id, "016x"),
                }
    return None

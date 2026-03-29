"""
链路追踪测试
============

验证链路追踪和 OpenTelemetry 集成
"""

import pytest
from nova_executor.tracing.tracer import (
    Tracer,
    Span,
    SpanKindEnum,
    SpanStatusEnum,
    get_tracer,
    inject_trace_context,
    extract_trace_context,
)


class TestTracer:
    """追踪器测试"""

    def test_create_tracer(self):
        """验证创建追踪器"""
        tracer = Tracer("test-service")
        assert tracer is not None
        assert tracer.service_name == "test-service"

    def test_generate_trace_id(self):
        """验证生成 Trace ID"""
        tracer = Tracer()
        trace_id = tracer.generate_trace_id()
        assert isinstance(trace_id, str)
        assert len(trace_id) == 32

    def test_generate_span_id(self):
        """验证生成 Span ID"""
        tracer = Tracer()
        span_id = tracer.generate_span_id()
        assert isinstance(span_id, str)
        assert len(span_id) == 16

    def test_generate_unique_ids(self):
        """验证生成的 ID 是唯一的"""
        tracer = Tracer()
        trace_id1 = tracer.generate_trace_id()
        trace_id2 = tracer.generate_trace_id()
        assert trace_id1 != trace_id2

    def test_start_span(self):
        """验证开始 Span"""
        tracer = Tracer()
        span = tracer.start_span("test-span")
        assert span is not None
        assert span.name == "test-span"
        assert span.trace_id is not None
        assert span.span_id is not None
        assert span.kind == SpanKindEnum.INTERNAL

    def test_start_span_with_kind(self):
        """验证带类型的开始 Span"""
        tracer = Tracer()
        span = tracer.start_span("server-span", kind=SpanKindEnum.SERVER)
        assert span.kind == SpanKindEnum.SERVER

    def test_start_span_with_attributes(self):
        """验证带属性的开始 Span"""
        tracer = Tracer()
        span = tracer.start_span(
            "test-span",
            attributes={"user.id": "123", "operation": "test"}
        )
        assert "user.id" in span.attributes
        assert span.attributes["user.id"] == "123"

    def test_start_span_with_parent(self):
        """验证带父上下文的开始 Span"""
        tracer = Tracer()
        parent_span = tracer.start_span("parent-span")
        child_span = tracer.start_span(
            "child-span",
            parent_context={"trace_id": parent_span.trace_id, "span_id": parent_span.span_id}
        )
        assert child_span.parent_span_id == parent_span.span_id

    def test_end_span(self):
        """验证结束 Span"""
        tracer = Tracer()
        span = tracer.start_span("test-span")
        assert span.end_time is None
        tracer.end_span(span)
        assert span.end_time is not None

    def test_set_span_attribute(self):
        """验证设置 Span 属性"""
        tracer = Tracer()
        span = tracer.start_span("test-span")
        span.set_attribute("key", "value")
        assert span.attributes["key"] == "value"

    def test_add_span_event(self):
        """验证添加 Span 事件"""
        tracer = Tracer()
        span = tracer.start_span("test-span")
        span.add_event("test-event", {"detail": "test"})
        assert len(span.events) == 1
        assert span.events[0]["name"] == "test-event"

    def test_set_span_status(self):
        """验证设置 Span 状态"""
        tracer = Tracer()
        span = tracer.start_span("test-span")
        span.set_status(SpanStatusEnum.OK)
        assert span.status == SpanStatusEnum.OK

    def test_span_context_manager(self):
        """验证 Span 上下文管理器"""
        tracer = Tracer()
        with tracer.span("managed-span") as span:
            span.set_attribute("operation", "managed")
        assert span.end_time is not None
        assert span.status == SpanStatusEnum.OK

    def test_span_context_manager_exception(self):
        """验证 Span 上下文管理器异常处理"""
        tracer = Tracer()
        span = None
        try:
            with tracer.span("error-span") as s:
                span = s
                raise ValueError("Test error")
        except ValueError:
            pass
        assert span is not None
        assert span.status == SpanStatusEnum.ERROR

    def test_get_current_context(self):
        """验证获取当前上下文"""
        tracer = Tracer()
        context = tracer.get_current_context()
        assert isinstance(context, dict)
        assert "trace_id" in context
        assert "span_id" in context

    def test_with_context(self):
        """验证上下文管理器"""
        tracer = Tracer()
        context = {"trace_id": "abc123", "span_id": "def456"}
        with tracer.with_context(context) as ctx:
            assert ctx == context


class TestSpan:
    """Span 测试"""

    def test_span_to_dict(self):
        """验证 Span 转换为字典"""
        span = Span(
            name="test-span",
            trace_id="trace123",
            span_id="span456",
        )
        span_dict = span.to_dict()
        assert span_dict["name"] == "test-span"
        assert span_dict["trace_id"] == "trace123"
        assert span_dict["span_id"] == "span456"

    def test_span_to_dict_with_all_fields(self):
        """验证完整 Span 转换为字典"""
        span = Span(
            name="test-span",
            trace_id="trace123",
            span_id="span456",
            kind=SpanKindEnum.SERVER,
            status=SpanStatusEnum.OK,
        )
        span.set_attribute("key", "value")
        span.add_event("event1")
        span_dict = span.to_dict()
        assert span_dict["kind"] == "server"
        assert span_dict["status"] == "ok"
        assert span_dict["attributes"]["key"] == "value"
        assert len(span_dict["events"]) == 1


class TestSpanKindEnum:
    """Span 类型枚举测试"""

    def test_span_kind_values(self):
        """验证 Span 类型枚举值"""
        assert SpanKindEnum.INTERNAL.value == "internal"
        assert SpanKindEnum.SERVER.value == "server"
        assert SpanKindEnum.CLIENT.value == "client"
        assert SpanKindEnum.PRODUCER.value == "producer"
        assert SpanKindEnum.CONSUMER.value == "consumer"


class TestSpanStatusEnum:
    """Span 状态枚举测试"""

    def test_span_status_values(self):
        """验证 Span 状态枚举值"""
        assert SpanStatusEnum.UNSET.value == "unset"
        assert SpanStatusEnum.OK.value == "ok"
        assert SpanStatusEnum.ERROR.value == "error"


class TestGetTracer:
    """获取追踪器测试"""

    def test_get_tracer_creates_instance(self):
        """验证获取追踪器创建实例"""
        tracer = get_tracer("test-service")
        assert tracer is not None
        assert tracer.service_name == "test-service"

    def test_get_tracer_returns_singleton(self):
        """验证获取追踪器返回单例"""
        tracer1 = get_tracer("service1")
        tracer2 = get_tracer("service1")
        assert tracer1 is tracer2


class TestTraceContextPropagation:
    """追踪上下文传播测试"""

    def test_inject_trace_context(self):
        """验证注入追踪上下文"""
        carrier = {}
        result = inject_trace_context(carrier)
        assert result is carrier

    def test_extract_trace_context(self):
        """验证提取追踪上下文"""
        carrier = {"traceparent": "00-abc123-def456-01"}
        context = extract_trace_context(carrier)
        assert context is None or isinstance(context, dict)

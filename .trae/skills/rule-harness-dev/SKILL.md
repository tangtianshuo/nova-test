---
name: "rule-harness-dev"
description: "提供Harness Engineering导向的代码开发规则与质量闸门。做新功能/改Schema/接入模型/改执行流程/发版前调用。"
---

# Rule · Harness Engineering（开发阶段）

## 何时调用

- 进入“代码实现阶段”：开始写后端/前端/Worker/推流/存储逻辑
- 修改任何 Schema/API/DB/MQ/WS 协议
- 调整 Agent 工作流（LangGraph 节点、HIL、重试、验证策略）
- 引入或变更模型推理（Fara-7B/vLLM/TGI/Prompt/JSON约束）
- 发版、合并、上线前需要质量闸门

## Harness Engineering 核心思想（本项目版）

- 先做“可验证的护栏（Harness）”，再做实现：让系统在变更中保持可控
- 把不确定性显性化并可回放：模型输出、置信度、候选框、HIL 决策
- 所有关键接口必须可模拟：推理服务、浏览器沙箱、对象存储、队列/推流

## 必须建立的 Harness（P0）

### 1) Schema Harness

- 每个跨模块对象必须有 Schema：Task/Instance/Step/Action/Event/Ticket/Report
- 每个 Schema 必须带版本字段：`schema_version`
- 对所有输入/输出做结构校验：
  - Vision 输出 ActionSchema（解析失败视为系统事件）
  - Verifier 输出 VerifySchema
  - WS 推送 EventSchema

### 2) API Contract Harness

- 为核心 API 建立契约测试（request/response/error-code）
- 必测路径：
  - `POST /tasks`
  - `POST /tasks/{task_id}/instances`
  - `GET /instances/{instance_id}/state`
  - `POST /instances/{instance_id}/resume`

### 3) Worker/StateMachine Harness

- 状态机每个节点必须可单独测试：init/explore/check_hil/execute/verify
- 必须有“最大步数/终止条件/异常循环”保护测试
- 失败模式必须可重复：固定随机种子或固定 fixture

### 4) HIL Harness

- HIL 触发条件必须可配置并可测试（低置信度/高危/解析失败/超时）
- HIL 决策融合必须可测试：approve/reject/modify
- 高危默认二次确认 + 审计记录必测

### 5) Storage Harness

- 对象存储必须使用受控访问（预签名/网关代理）
- 截图/录屏生命周期可测试（保留期/销毁）

### 6) Multi-tenant Harness

- 所有数据访问必须绑定 tenant 上下文
- 必须有跨租户访问的负向测试

## 推荐 Harness（P1）

- Regression Harness：用固定页面/截图集回放模型输出，监控退化
- Performance Harness：单步延迟、并发实例数、推流稳定性
- Security Harness：敏感字段泄漏扫描（日志/报错/导出）

## 代码开发闸门（DoD）

- Schema：新增/修改字段有版本策略与兼容说明
- Test：新增功能必须包含对应 Harness 测试（最少一个）
- Security：不输出 token/密码/API key；截图/URL 访问受控
- Observability：实例级 trace_id/instance_id 可追溯
- UI：全屏无滚动条；长内容分页/折叠/截断+复制


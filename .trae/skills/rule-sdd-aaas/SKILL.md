---
name: "rule-sdd-aaas"
description: "提供SaaS+AaaS+SDD的统一工程规则与检查清单。用户要求需求/设计/接口/Schema一致性、多租户安全、HIL流程或无滚动全屏UI时调用。"
---

# Rule · SDD + AaaS + SaaS

## 何时调用

- 用户要求：按文档/规范实现功能、补齐设计、对齐接口与Schema、拆任务
- 需要做：多租户隔离、鉴权/RBAC、审计、安全合规、对象存储、队列/推流
- 涉及 Agent 执行闭环：Observe-Think-Act-Verify、HIL 挂起/恢复
- 涉及前端：全屏适配、禁止滚动条、使用分页/折叠/抽屉

## 项目不变量（必须满足）

### SDD（Schema Driven Development）

- 任何跨模块交互必须先有 Schema：`Task`/`Instance`/`Step`/`Action`/`Event`/`Ticket`/`Report`
- Schema 必须带 `schema_version` 或等价版本字段
- Schema 变更：
  - 字段新增优先可选且向后兼容
  - 破坏性变更必须提升主版本并同步更新文档

### SaaS 多租户

- 所有业务表必须显式具备 `tenant_id` 或等价隔离字段
- 所有查询必须绑定租户上下文（token->tenant），禁止跨租户访问
- 任何对象存储 URL 必须鉴权（预签名或网关代理）

### AaaS 执行闭环

- `Observe`：截图采集与上下文构造（objective/history/constraints）
- `Think`：模型输出必须为可解析 JSON（ActionSchema）；解析失败需重试或进入 HIL
- `Act`：执行器必须返回执行结果与新截图
- `Verify`：至少产生 `isSuccess/isDefect/canRetry` 的结构化结论

### Human-in-the-Loop（HIL）

- 触发条件必须可配置（敏感操作、低置信度、异常循环、超时等）
- HIL 工单必须包含：原因、风险等级、planned_action、现场截图、候选框/坐标
- 恢复执行必须支持：approve/reject/modify（修改坐标/输入内容/替代动作）
- 高危动作默认二次确认，且必须落审计（操作者/时间/原因）

### 安全与隐私

- 不允许把账号/密码/API Key 放入模型上下文
- 截图/录屏属于高敏数据：加密、保留期、按租户隔离
- 日志不得打印敏感信息与 token

### UI 全屏无滚动条

- 页面必须适配 `100vh`，禁止出现浏览器滚动条
- 面板内容禁止滚动条，信息超量使用分页/折叠/抽屉/切换视图
- JSON/长文本：截断预览 + 复制全文

## 交付检查清单（提交前）

- 文档：需求/接口/DB/详细设计与实际实现一致
- API：参数校验与错误码一致（至少 `400/401/403/404/409/429/500`）
- 数据：关键操作落审计；对象存储访问受控
- 执行：能跑通最小闭环（Task->Instance->Step->HIL->Report）
- 前端：全屏无滚动条；列表/日志/时间线分页可用


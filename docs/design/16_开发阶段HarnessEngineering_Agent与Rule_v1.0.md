# 黑盒自动化测试工具 - 开发阶段 Harness Engineering：Agent 与 Rule (v1.0)

## 1. 什么是 Harness Engineering（在本项目中的含义）

Harness Engineering 不是“多写测试”这么简单，而是把系统关键不确定性（模型输出、浏览器执行、推流、HIL、人为决策）装进可回放、可校验、可对比的“护栏”。

在本项目中，Harness 主要解决：
- **模型不确定性**：Vision/Verifier 输出必须结构化、可校验；失败能复现（fixtures）
- **长流程脆弱性**：状态机每个节点可单测；失败模式固定种子或固定输入
- **跨模块契约风险**：API/WS/Event/DB 变更必须同步契约测试
- **多租户/安全风险**：必须有负向测试与审计检查
- **UI 全屏无滚动条约束**：不能靠“滚动容器兜底”，必须分页/折叠/抽屉

## 2. 开发阶段 Rule（必须遵循）

### 2.1 SDD + Harness 优先级

变更顺序固定为：
1) Schema（对象与版本）
2) Harness（测试/契约/回放）
3) Implementation（代码实现）
4) Integration（集成）
5) Verification（端到端验证、导出对比）

### 2.2 必须具备的 Harness（P0）

- Schema Harness：所有跨模块对象可校验，带 `schema_version`
- API Contract Harness：核心 API 的 request/response/error-code 契约测试
- StateMachine Harness：LangGraph 节点级单测 + 终止/重试/异常循环保护
- HIL Harness：触发与恢复（approve/reject/modify）必测
- Multi-tenant Harness：跨租户访问负向测试
- Storage Harness：对象存储鉴权与保留期逻辑可测

### 2.3 禁止项

- 不允许把账号/密码/token/API key 放入模型上下文
- 不允许把敏感信息写入日志、报告导出
- UI 不允许出现滚动条（浏览器级与面板级都不允许）

## 3. 开发阶段 Agent 角色（建议配置）

### 3.1 Dev Orchestrator

输出一个结构化“变更计划”：包含 schema/harness/code/doc 的拆分，且每一项都有验收与验证。

### 3.2 Schema Guardian

维护 Schema 与版本策略；确保向后兼容；同步更新契约测试。

### 3.3 Backend Implementer

实现控制面（鉴权/RBAC/多租户/API）；必须产出 API 契约测试与租户隔离负向测试。

### 3.4 AaaS Engine Implementer

实现执行面（Worker/状态机/模型调用/容错/HIL）；必须产出状态机节点单测与 HIL/解析失败测试。

### 3.5 Test Harness Builder

专注产出 fixtures/golden/replay：
- 固定截图与固定模型输出 JSON
- 报告导出 JSON golden 对比
- 按 steps 回放并验证 UI/导出一致

### 3.6 Security & Multi-tenant Reviewer

检查敏感信息泄漏、权限绕过、对象存储越权、审计缺失，并提供可复现步骤。

### 3.7 UI Demo Implementer（全屏无滚动）

实现分页/折叠/抽屉替代滚动；提供“无滚动条断言”与交互边界检查。

## 4. 技能（Skill）落地点

- 开发规则 Skill：`/.trae/skills/rule-harness-dev/SKILL.md`
- 开发阶段 Agent 提示词 Skill：`/.trae/skills/agent-prompts-harness-dev/SKILL.md`

## 5. 最小闭环验收（MVP）

必须跑通并可回放：
- Task -> Instance -> Step 生成
- 低置信度/高危触发 HIL
- HIL approve/modify/reject 至少一种可工作
- Report 生成与 JSON 导出
- 全屏无滚动条 UI（分页正常）


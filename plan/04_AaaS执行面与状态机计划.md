# Plan 04：AaaS 执行面与状态机计划

## 目标

- 实现 Worker + LangGraph 状态机（init/explore/check_hil/execute/verify）
- 对接 Magentic-UI/Playwright（执行器）与 Fara-7B（视觉推理）
- 让关键失败模式可复现、可回放（Harness）

## 依赖关系

本计划依赖以下前置计划：

| 依赖项 | 说明 | 关键依赖内容 |
|--------|------|-------------|
| EP-01 (Schema) | Schema 定义计划 | Instance、Task、Step 等核心类型定义 |
| EP-02 (数据库) | 数据库计划 | Step 表结构、任务状态持久化接口 |
| EP-03 (Instance/Task 基础) | Instance/Task 基础计划 | 队列消费机制、任务生命周期管理 |

**依赖检查点：**
- [ ] EP-01 Schema 中 Instance/Task/Step 类型已定义
- [ ] EP-02 数据库迁移已执行，Step 表可写入
- [ ] EP-03 任务队列已可用，Worker 可消费任务

## 范围

### 执行面能力（P0）

- Worker 从队列消费 instance
- 运行状态机循环：Observe-Think-Act-Verify
- Step 落库：截图引用、动作、验证结论
- 终止条件：max_steps / end

## Harness（先做）

### H1：StateMachine Node Harness（P0）

每个节点必须可单测，测试用例如下：

#### init 节点测试用例

- **`should_init_node_generate_screenshot`**
  - 输入：有效的 Instance 上下文
  - Mock：Playwright 客户端返回模拟截图
  - 预期：生成初始截图，状态初始化为 `initialized`，截图引用正确存储

#### explore 节点测试用例

- **`should_explore_node_produce_planned_action`**
  - 输入：当前页面截图 + 任务目标描述
  - Mock：Vision 客户端返回结构化的 planned_action
  - 预期：产出有效的 `planned_action`，包含 `action_type`、`selector`、`params` 等字段

#### check_hil 节点测试用例

- **`should_check_hil_node_enter_paused_state`**
  - 输入：低置信度的 planned_action（confidence < 阈值）
  - 预期：状态转换为 `paused_hil`，生成 HIL 请求记录

#### execute 节点测试用例

- **`should_execute_node_handle_success_branch`**
  - 输入：有效的 planned_action
  - Mock：Executor 客户端返回执行成功
  - 预期：状态转换为 `executed`，Step 记录执行结果

- **`should_execute_node_handle_failure_branch`**
  - 输入：有效的 planned_action
  - Mock：Executor 客户端返回执行失败（如元素未找到）
  - 预期：状态转换为 `failed` 或触发重试逻辑

#### verify 节点测试用例

- **`should_verify_node_detect_defect`**
  - 输入：执行后的页面截图 + 预期结果
  - Mock：Verifier 返回检测结果（如页面错误、数据异常）
  - 预期：标记为 `defect_detected`，记录缺陷详情

- **`should_verify_node_confirm_success`**
  - 输入：执行后的页面截图 + 预期结果
  - Mock：Verifier 返回验证通过
  - 预期：状态转换为 `verified`，任务可进入下一轮或终止

### H2：Replay Harness（P0）

给定一组固定的 steps fixtures，能够复现以下场景：

#### 测试用例

- **`should_replay_successful_execution`**
  - Fixture：完整的成功执行步骤序列（init → explore → execute → verify → end）
  - 预期：按序回放所有步骤，最终状态为 `completed`

- **`should_replay_low_confidence_hil_trigger`**
  - Fixture：包含低置信度 planned_action 的步骤
  - 预期：在 check_hil 节点触发 HIL，状态转换为 `paused_hil`

- **`should_replay_parse_failure_hil_trigger`**
  - Fixture：包含模型输出解析失败的步骤
  - 预期：解析错误被捕获，触发 HIL，状态转换为 `paused_hil`

- **`should_replay_defect_failure`**
  - Fixture：verify 节点检测到缺陷的步骤
  - 预期：标记缺陷，状态转换为 `defect_detected`，任务终止

### H3：Model Output Robustness Harness（P1）

用"坏 JSON/缺字段/类型错"的模型输出夹具验证系统健壮性：

#### 测试用例

- **`should_handle_malformed_json_output`**
  - 输入：畸形的 JSON 字符串（如缺少引号、括号不匹配）
  - 预期：解析错误被捕获，尝试修复或进入 HIL，不导致系统崩溃

- **`should_handle_missing_required_field`**
  - 输入：JSON 结构正确但缺少必需字段（如缺少 `action_type`）
  - 预期：校验失败被检测，进入 HIL 等待人工干预

- **`should_handle_type_mismatch`**
  - 输入：字段类型错误（如 `confidence` 为字符串而非数字）
  - 预期：类型转换尝试失败后进入 HIL，或自动类型修复

## TDD 步骤

1) 先写节点单测（全部先失败）
2) 实现最小状态结构与路由（关键路由加中文注释：为什么会进入 HIL/终止）
3) 用 mock 的 Vision/Executor/Verifier 跑通 replay
4) 再接入真实适配器（通过接口隔离）
5) 重构：把策略（HIL 阈值/重试）抽成可替换组件（OCP）

## 代码目录结构映射

```
src/executor/
├── worker/
│   ├── worker.service.ts        # 队列消费与任务分发
│   └── sandbox.manager.ts       # 沙箱环境管理
├── state_machine/
│   ├── graph.ts                 # LangGraph 图定义
│   ├── nodes/
│   │   ├── init.node.ts
│   │   ├── explore.node.ts
│   │   ├── check_hil.node.ts
│   │   ├── execute.node.ts
│   │   └── verify.node.ts
│   └── routing.ts               # 节点路由逻辑（需中文注释）
├── adapters/
│   ├── vision.adapter.ts        # Fara-7B 视觉推理适配器
│   ├── executor.adapter.ts      # Playwright 执行适配器
│   └── verifier.adapter.ts      # 验证器适配器
└── clients/
    ├── fara7b.client.ts          # Fara-7B API 客户端
    └── playwright.client.ts      # Playwright 客户端
```

## 中文注释规范

以下关键模块必须添加中文注释，说明业务逻辑和决策依据：

### 状态机路由逻辑 (routing.ts)

```typescript
/**
 * 状态机节点路由逻辑
 * 
 * 根据当前状态决定下一个执行节点：
 * - initialized → explore：初始化完成，开始探索
 * - explored → check_hil：探索完成，检查是否需要人工介入
 * - check_hil → execute/paused_hil：根据置信度决定执行或暂停
 * - executed → verify：执行完成，进入验证
 * - verified → explore/end：验证通过后继续或终止
 */
```

### HIL 分支处理 (check_hil.node.ts)

```typescript
/**
 * HIL（Human-in-the-Loop）分支处理
 * 
 * 触发 HIL 的条件：
 * 1. 置信度低于阈值（confidence < HIL_THRESHOLD）
 * 2. 模型输出解析失败且无法自动修复
 * 3. 遇到未知页面元素或异常状态
 * 
 * HIL 状态：
 * - paused_hil：等待人工干预
 * - resumed：人工干预完成，继续执行
 * - cancelled：人工取消任务
 */
```

### 终止条件判断 (graph.ts)

```typescript
/**
 * 任务终止条件判断
 * 
 * 终止条件（满足任一即终止）：
 * 1. 达到最大步数限制（current_step >= max_steps）
 * 2. 验证成功且无需继续（verify_result === 'success' && should_end）
 * 3. 检测到缺陷（defect_detected === true）
 * 4. 不可恢复的错误（error && !recoverable）
 * 5. 人工取消（status === 'cancelled'）
 */
```

## 设计原则（SOLID）

- `VisionClient`/`ExecutorClient`/`VerifierClient` 必须是接口（ISP/DIP）
- 状态机只依赖接口，不依赖具体 SDK（DIP）
- HIL 策略、重试策略、终止策略独立（SRP/OCP）

## 交付物

- Worker 服务
- 状态机模块
- 适配器接口 + mock 实现
- Harness：节点单测 + 回放

## 验收标准

- 节点单测与回放 harness 全绿
- 任意解析失败不会导致崩溃，而是进入 HIL 或可重试


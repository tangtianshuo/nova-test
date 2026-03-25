# Plan 05：推流与 HIL 计划

## 依赖关系

- **前置依赖**：EP-04 (AaaS 执行面)
  - 依赖 EP-04 的 Instance 运行时状态管理
  - 依赖 EP-04 的 Action 执行器接口
  - 依赖 EP-04 的实例生命周期（pause/resume/terminate）

## 目标

- 落地 WebSocket 推流：截图/思维链/HIL 请求
- 落地 HIL 工单：创建、锁定、处理、恢复执行
- 推流与 HIL 全链路可测试（Harness）

## 范围

### 推流（P0）

- `SCREENSHOT_UPDATE`
- `AGENT_THOUGHT`
- `HIL_REQUEST`
- （建议扩展）`ACTION_PROPOSAL`（用于前端画 bbox/候选框）

### HIL（P0）

- 触发条件：高危/低置信度/解析失败/异常循环/超时
- 工单字段：reason/risk/planned_action/screenshot/overlay
- 处理动作：approve/reject/modify

## Harness（先做）

### H1：EventSchema Harness（P0）

- 推流事件必须符合 EventSchema；不合规必须被拒绝并记录（不崩溃）

#### 测试用例

- `should_accept_valid_screenshot_update_event` - 验证合法的截图更新事件被接受
- `should_accept_valid_agent_thought_event` - 验证合法的 Agent 思维链事件被接受
- `should_accept_valid_hil_request_event` - 验证合法的 HIL 请求事件被接受
- `should_reject_invalid_event_type` - 验证非法事件类型被拒绝并记录错误日志
- `should_reject_missing_instance_id` - 验证缺失 instance_id 的事件被拒绝

### H2：WebSocket Contract Harness（P0）

- 目标：WS 鉴权、订阅、事件顺序与断线重连策略可验证

#### 测试用例

- `should_require_auth_for_websocket_connection` - 验证未授权连接被拒绝
- `should_handle_subscription_correctly` - 验证订阅/取消订阅流程正常
- `should_maintain_event_order` - 验证事件按发送顺序到达
- `should_support_reconnection` - 验证断线后可重连并恢复正常通信
- `should_deliver_last_frame_on_reconnect` - 验证重连后能获取最后一帧状态

### H3：HIL Flow Harness（P0）

- 用例：
  - 低置信度触发工单 -> approve -> 继续执行
  - 高危触发工单 -> modify -> 按修改动作执行
  - reject -> 实例终止并生成报告

#### 测试用例

- `should_approve_continue_execution` - 验证 approve 决策后实例恢复正常执行
- `should_modify_action_and_execute` - 验证 modify 决策后按修改的动作执行
- `should_reject_terminate_instance` - 验证 reject 决策后实例终止并生成报告

## TDD 步骤

1) 先写 HIL flow 的端到端测试（使用 mock Vision/Executor）
2) 写 WS 推流契约测试（事件 schema + 订阅鉴权）
3) 实现事件发布与工单落库
4) 实现 resume API 的决策融合与恢复执行

## 设计原则（SOLID）

- 推流发布器与业务逻辑分离（SRP）
- HIL 工单处理采用策略/命令模式，新增决策类型不改旧代码（OCP）

## 交付物

- WebSocket 服务
- HIL 工单模块 + resume 实现
- Harness：Event/WS/HIL flow

## 验收标准

- HIL flow harness 全绿
- WS 推流可重连且不丢失关键状态（至少最后一帧+最新 action）

## 代码目录结构映射

```
src/streaming/
├── websocket/
│   ├── gateway.ts               # WS 网关服务
│   ├── handlers/
│   │   ├── screenshot.handler.ts
│   │   ├── thought.handler.ts
│   │   └── hil.handler.ts
│   └── middleware/
│       └── auth.ws.middleware.ts
└── hil/
    ├── ticket.service.ts         # 工单创建与管理
    ├── processor.service.ts      # 工单处理（需中文注释）
    └── lock.manager.ts           # HIL 锁管理
```

## 中文注释规范

以下模块需要添加详细的中文注释：

### HIL 决策融合逻辑

```typescript
// processor.service.ts 中需要中文注释的关键逻辑：
// - 决策类型判断与路由（approve/modify/reject）
// - modify 场景下的动作合并策略
// - 决策结果与原计划动作的融合规则
// - 执行恢复时的上下文重建
```

### 锁竞争处理

```typescript
// lock.manager.ts 中需要中文注释的关键逻辑：
// - 工单锁定机制（防止多人同时处理同一工单）
// - 锁超时与自动释放策略
// - 锁获取失败时的重试/降级逻辑
// - 死锁检测与恢复机制
```


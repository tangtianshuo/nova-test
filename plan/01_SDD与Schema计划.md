# Plan 01：SDD 与 Schema 计划

## 依赖关系

此计划是所有后续计划的基础，**无前置依赖**。

---

## 目标

- 把 `docs/design` 中核心对象固化为可演进的 Schema（带版本）
- 让所有跨模块交互都可以被"Schema Harness"校验
- 建立统一的 Schema 校验机制，为后续计划提供数据契约保障

---

## 范围（需要实现的 Schema）

| Schema 名称 | 用途说明 |
|------------|---------|
| `TaskSchema` | 任务定义结构 |
| `InstanceSchema` | 实例运行时结构 |
| `StepSchema` | 步骤执行结构 |
| `ActionSchema` | Vision 输出/Executor 输入 |
| `EventSchema` | WS 推流事件 |
| `HilTicketSchema` | HIL 人工干预工单 |
| `ReportSchema` | 报告输出结构 |

---

## Harness（先做）

### H1：Schema Harness（P0）

**产出**：Schema 校验器 + 样例 fixtures

#### 测试用例列表

| 用例编号 | 用例名称 | 类型 | 说明 |
|---------|---------|------|------|
| H1-01 | `should_accept_valid_task_schema` | 正向 | 验证合法的 TaskSchema |
| H1-02 | `should_accept_valid_instance_schema` | 正向 | 验证合法的 InstanceSchema |
| H1-03 | `should_accept_valid_step_schema` | 正向 | 验证合法的 StepSchema |
| H1-04 | `should_reject_missing_required_field` | 负向 | 拒绝缺少必填字段的数据 |
| H1-05 | `should_reject_invalid_version` | 负向 | 拒绝不支持的版本号 |
| H1-06 | `should_reject_type_mismatch` | 负向 | 拒绝类型不匹配的数据 |
| H1-07 | `should_reject_extra_fields_when_strict` | 负向 | 严格模式下拒绝额外字段 |

#### 正向测试补充

- 每个 Schema 至少 3 个合法样例（放置于 `tests/schema_harness/fixtures/valid/`）

#### 负向测试补充

- 缺少必填、类型错误、版本不支持、额外字段（放置于 `tests/schema_harness/fixtures/invalid/`）

---

## TDD 步骤

1. 为每个 Schema 编写 `should_accept_valid_*` 测试用例
2. 编写 `should_reject_invalid_*` 测试用例
3. 实现最小校验器（解析 + 验证）
4. 重构：抽象通用校验入口（单一职责，便于替换校验库）

---

## 设计原则（SOLID）

| 原则 | 应用说明 |
|------|---------|
| **SRP（单一职责）** | 校验器与业务逻辑分离，校验器只负责数据格式校验 |
| **OCP（开闭原则）** | Schema 版本策略独立模块，新增版本无需修改现有代码 |
| **DIP（依赖倒置）** | 业务模块只依赖"Schema 校验接口"而非具体实现 |

---

## 代码目录结构映射

```
src/schemas/
├── task.schema.ts          # TaskSchema 定义
├── instance.schema.ts      # InstanceSchema 定义
├── step.schema.ts          # StepSchema 定义
├── action.schema.ts        # ActionSchema 定义
├── event.schema.ts         # EventSchema 定义
├── hil_ticket.schema.ts    # HilTicketSchema 定义
├── report.schema.ts        # ReportSchema 定义
└── validators/             # 校验器实现
    ├── schema.validator.ts
    └── version.strategy.ts

tests/schema_harness/
├── fixtures/               # 测试数据
│   ├── valid/              # 合法样例
│   └── invalid/            # 非法样例
└── schema.validator.spec.ts
```

---

## 中文注释规范

Schema 校验器关键逻辑需要添加中文注释，包括但不限于：

- 每个 Schema 文件顶部的模块用途说明
- 校验器核心函数的参数、返回值说明
- 版本策略的兼容性规则说明
- 错误码/错误信息的语义解释
- 复杂校验逻辑的业务含义注释

**示例**：

```typescript
/**
 * Schema 校验器入口
 * 职责：对输入数据进行 Schema 格式校验，返回校验结果
 * @param data - 待校验的原始数据
 * @param schemaType - 目标 Schema 类型
 * @returns 校验结果，包含是否通过及错误信息
 */
export function validateSchema(data: unknown, schemaType: SchemaType): ValidationResult {
  // ...
}
```

---

## 交付物

| 交付物 | 路径/说明 |
|-------|---------|
| Schema 定义文件 | `src/schemas/*.schema.ts` |
| 校验器实现 | `src/schemas/validators/` |
| Harness 测试 | `tests/schema_harness/`（含 fixtures + 单测） |
| 文档 | Schema 版本策略与兼容规则 |

---

## 验收标准

- [ ] 任意跨模块 JSON 进入系统前可被校验器校验
- [ ] 解析失败或版本不支持有明确错误码/错误信息
- [ ] 所有 H1 测试用例通过
- [ ] 校验器关键逻辑包含中文注释
- [ ] 代码目录结构符合上述映射规范

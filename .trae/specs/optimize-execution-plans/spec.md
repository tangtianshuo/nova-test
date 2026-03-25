# 优化执行计划 Spec

## Why

现有 `plan/` 目录中的执行计划已经建立了良好的 Harness Engineering 框架，但需要进一步优化以确保：
1. 计划之间的依赖关系更加清晰
2. 每个计划的具体验收标准更加细化
3. 与 `docs/design/` 中的设计文档保持一致性
4. 实际可执行的任务分解更加明确

## What Changes

- 优化现有 9 个执行计划的内容结构与完整性
- 增强计划间的依赖关系说明
- 添加更详细的 TDD 测试用例规范
- 补充代码实现的具体目录结构规划
- 增加中文注释规范说明

## Impact

- Affected specs: 所有执行计划 (01-09)
- Affected code: `plan/*.md` 文件

## ADDED Requirements

### Requirement: 计划结构标准化

每个执行计划必须包含以下标准化结构：
- **目标**：清晰的目标陈述
- **范围**：P0/P1 优先级划分
- **Harness**：测试护栏定义（带 P0/P1 标记）
- **TDD 步骤**：详细的测试驱动开发步骤
- **设计原则**：SOLID + 迪米特法则应用说明
- **交付物**：具体文件/模块列表
- **验收标准**：可检验的完成条件
- **依赖关系**：前置计划与并行可能

#### Scenario: 计划结构完整
- **WHEN** 审查任一执行计划
- **THEN** 计划包含所有标准化结构元素

### Requirement: 依赖关系可视化

执行计划之间必须有明确的依赖关系说明：
- EP-01 (SDD与Schema) 是所有计划的基础
- EP-02 (数据库) 依赖 EP-01
- EP-03 (控制面API) 依赖 EP-01, EP-02
- EP-04 (AaaS执行面) 依赖 EP-01, EP-02, EP-03
- EP-05 (推流与HIL) 依赖 EP-04
- EP-06 (报告与导出) 依赖 EP-02, EP-04, EP-05
- EP-07 (UI控制台) 依赖 EP-03, EP-05, EP-06
- EP-08 (安全合规) 贯穿全局
- EP-09 (可观测性) 依赖所有计划

#### Scenario: 依赖关系正确
- **WHEN** 开始实施某个计划
- **THEN** 所有前置依赖计划已完成

### Requirement: 代码目录结构规划

必须为每个计划定义具体的代码目录结构：

```
src/
├── schemas/           # EP-01: Schema 定义
├── db/                # EP-02: 数据库层
│   ├── migrations/
│   ├── repositories/
│   └── models/
├── api/               # EP-03: 控制面 API
│   ├── controllers/
│   ├── services/
│   ├── middleware/
│   └── dto/
├── executor/          # EP-04: AaaS 执行面
│   ├── worker/
│   ├── state_machine/
│   ├── adapters/
│   └── clients/
├── streaming/         # EP-05: 推流与 HIL
│   ├── websocket/
│   └── hil/
├── report/            # EP-06: 报告与导出
│   ├── generator/
│   └── exporter/
├── ui/                # EP-07: 前端控制台
│   ├── components/
│   ├── pages/
│   └── hooks/
├── security/          # EP-08: 安全模块
│   ├── sanitizer/
│   └── audit/
└── observability/     # EP-09: 可观测性
    ├── logging/
    └── metrics/
```

#### Scenario: 目录结构一致
- **WHEN** 实施某个计划
- **THEN** 代码放置在预定义的目录结构中

### Requirement: 中文注释规范

关键代码必须包含中文注释：
- 状态机路由逻辑（为什么进入 HIL/终止）
- 安全边界检查（权限与租户隔离）
- HIL 分支处理（决策融合逻辑）
- 错误恢复策略（重试/降级）
- 并发控制（锁/队列）

#### Scenario: 关键代码有中文注释
- **WHEN** 审查状态机/安全/HIL 相关代码
- **THEN** 存在中文注释说明意图与风险

### Requirement: TDD 测试用例细化

每个 Harness 必须包含具体的测试用例定义：

**Schema Harness 示例**：
- `should_accept_valid_task_schema`
- `should_reject_missing_required_field`
- `should_reject_invalid_version`
- `should_reject_type_mismatch`

**Multi-tenant Harness 示例**：
- `should_isolate_tenant_data`
- `should_reject_cross_tenant_access`
- `should_enforce_tenant_quota`

#### Scenario: 测试用例可执行
- **WHEN** 运行某个 Harness 测试套件
- **THEN** 所有定义的测试用例可执行并有明确断言

## MODIFIED Requirements

### Requirement: Sprint 建议优化

原 Sprint 建议调整为更细粒度的迭代：

**迭代 0 (Week 1)**: 基础设施
- EP-01 全部完成
- EP-02 FE-02-01 (核心表与索引)

**迭代 1 (Week 2-3)**: 控制面核心
- EP-03 全部完成
- EP-02 FE-02-02, FE-02-03 (存储与队列)

**迭代 2 (Week 4-5)**: 执行面闭环
- EP-04 FE-04-01, FE-04-02
- EP-05 FE-05-01 (WebSocket 推流)

**迭代 3 (Week 6-7)**: HIL 与报告
- EP-05 FE-05-02, FE-05-03
- EP-06 全部

**迭代 4 (Week 8-9)**: UI 与安全
- EP-07 全部
- EP-08 全部

**迭代 5 (Week 10)**: 可观测性与发布
- EP-09 全部
- 集成测试与回归

## REMOVED Requirements

无移除的需求。本 Spec 为优化现有计划，不删除任何内容。

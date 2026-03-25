# Plan 03：控制面 API 与鉴权计划

## 目标

- 落地 `docs/design/06_接口设计文档_v1.0.md` 的核心 REST API
- 提供 JWT 鉴权、RBAC、租户上下文注入
- 建立 API Contract Harness（契约测试）

## 依赖关系

本计划依赖以下前置计划：

| 依赖项 | 说明 |
|--------|------|
| EP-01 (Schema) | 提供 Task/Instance 等 JSON Schema 定义，用于 DTO 校验 |
| EP-02 (数据库 Repository) | 提供数据访问层接口，服务层通过 Repository 操作持久化数据 |

依赖约束：
- DTO 定义需引用 EP-01 的 Schema
- Service 层注入 Repository 接口（DIP 原则），实现由 EP-02 提供

## 范围

### 核心 API（P0）

- `POST /tasks`
- `POST /tasks/{task_id}/instances`
- `GET /instances/{instance_id}/state`
- `POST /instances/{instance_id}/resume`

### 安全（P0）

- JWT 认证
- RBAC（至少四角色）
- tenant_id 绑定：token -> tenant 上下文

## Harness（先做）

### H1：API Contract Harness（P0）

- 目标：请求/响应/错误码与文档一致
- 覆盖：
  - `ERR_400` 参数校验
  - `ERR_401` token 无效
  - `ERR_403` 权限不足
  - `ERR_404` 资源不存在
  - `ERR_409` 状态冲突（非 paused_hil resume）
  - `ERR_429` 并发额度不足

#### H1 测试用例明细

| 用例名 | 场景描述 | 预期结果 |
|--------|----------|----------|
| `should_return_201_on_create_task` | 使用合法 token 和有效请求体创建任务 | HTTP 201，返回 task_id |
| `should_return_400_on_invalid_input` | 请求体缺少必填字段或类型错误 | HTTP 400，返回 ERR_400 错误详情 |
| `should_return_401_on_missing_token` | 请求未携带 Authorization header | HTTP 401，返回 ERR_401 |
| `should_return_403_on_insufficient_permission` | token 有效但角色无操作权限（如 viewer 调用 POST） | HTTP 403，返回 ERR_403 |
| `should_return_404_on_nonexistent_resource` | 访问不存在的 task_id 或 instance_id | HTTP 404，返回 ERR_404 |
| `should_return_409_on_state_conflict` | 对非 paused_hil 状态的实例调用 resume | HTTP 409，返回 ERR_409 |
| `should_return_429_on_quota_exceeded` | 租户并发实例数超过配额限制 | HTTP 429，返回 ERR_429 |

### H2：Multi-tenant Negative Harness（P0）

- 目标：跨租户访问必须失败
- 用例：用租户A token 访问租户B 的 task/instance

#### H2 测试用例明细

| 用例名 | 场景描述 | 预期结果 |
|--------|----------|----------|
| `should_reject_cross_tenant_task_access` | 租户A token 尝试访问租户B 的 task | HTTP 403/404，拒绝访问 |
| `should_reject_cross_tenant_instance_access` | 租户A token 尝试访问租户B 的 instance | HTTP 403/404，拒绝访问 |
| `should_enforce_tenant_quota` | 租户创建资源时检查配额限制 | 超额返回 HTTP 429 |
| `should_isolate_tenant_data` | 列表查询仅返回当前租户数据 | 响应不包含其他租户数据 |

## TDD 步骤

1) 先写契约测试（按 OpenAPI/文档样例）
2) 实现路由骨架与 DTO/Schema 校验
3) 实现鉴权/RBAC 中间件（关键逻辑加中文注释：权限与租户隔离）
4) 实现业务处理（依赖 Repository 接口）
5) 补充负向与边界测试

## 设计原则（SOLID）

- Controller 只做输入校验与调用应用服务（SRP）
- 应用服务依赖 Repository 接口（DIP）
- RBAC/tenant 作为独立策略组件（OCP）

## 交付物

- API 服务（控制面）
- 契约测试套件
- 租户隔离负向测试

## 验收标准

- 契约测试全绿
- 任意跨租户访问均失败
- 错误码与文档一致

## 代码目录结构映射

```
src/api/
├── controllers/
│   ├── task.controller.ts
│   ├── instance.controller.ts
│   └── auth.controller.ts
├── services/
│   ├── task.service.ts
│   ├── instance.service.ts
│   └── auth.service.ts
├── middleware/
│   ├── auth.middleware.ts
│   ├── rbac.middleware.ts
│   └── tenant.middleware.ts
├── dto/
│   ├── create-task.dto.ts
│   └── instance-state.dto.ts
└── guards/
    └── roles.guard.ts
```

### 目录职责说明

| 目录/文件 | 职责 |
|-----------|------|
| `controllers/` | 处理 HTTP 请求，负责输入校验与响应格式化 |
| `services/` | 业务逻辑层，依赖 Repository 接口实现领域操作 |
| `middleware/` | 横切关注点：认证、授权、租户上下文注入 |
| `dto/` | 数据传输对象，引用 EP-01 Schema 定义 |
| `guards/` | 路由级角色守卫，配合 RBAC 中间件使用 |


# Nova Test AaaS 黑盒自动化测试平台

> 基于 FastAPI + LangGraph + Playwright 的智能自动化测试系统

## 项目概述

Nova Test 是一个企业级黑盒自动化测试平台，通过 LangGraph 状态机驱动的 AI Agent 实现智能化的 Web 应用测试。系统支持 Human-in-the-Loop (HIL) 人机协作，可以在 AI 执行过程中引入人工审核，确保测试的准确性和安全性。

### 核心特性

- **🎯 智能测试执行**: 基于 LangGraph 状态机的 AI 测试 Agent
- **👁️ Vision 模型集成**: 支持 Fara-7B 等视觉语言模型进行页面分析
- **🤝 HIL 人机协作**: 关键决策点支持人工审核和干预
- **📊 实时推流**: WebSocket 实时推送执行状态和截图
- **🔒 多租户隔离**: 完整的 RBAC 权限控制和租户隔离
- **📈 可观测性**: Prometheus 指标、健康检查、日志追踪

## 技术架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端 (React + Vite)                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │任务管理 │ │实例监控 │ │HIL面板  │ │报告查看 │ │实时控制台│  │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘  │
└───────┼───────────┼───────────┼───────────┼───────────┼───────┘
        │           │           │           │           │
        └───────────┴───────────┴───────────┴───────────┘
                                │
                    ┌───────────┴───────────┐
                    │   REST API (Express)  │
                    │  ┌─────────────────┐  │
                    │  │  任务路由       │  │
                    │  │  实例路由       │  │
                    │  │  认证中间件     │  │
                    │  └────────┬────────┘  │
                    └────────────┼────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐      ┌─────────────────┐      ┌───────────────┐
│ PostgreSQL    │      │  Python 执行引擎 │      │    Redis      │
│  (数据存储)   │      │  FastAPI+LangGraph│      │  (消息队列)   │
└───────────────┘      └────────┬────────┘      └───────────────┘
                               │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│  Playwright   │      │ Vision 模型   │      │  MinIO (S3)   │
│  (浏览器沙箱)  │      │ (Fara-7B)    │      │  (截图存储)   │
└───────────────┘      └───────────────┘      └───────────────┘
```

## 项目结构

```
nova-test/
├── executor-python/              # Python 执行引擎 (FastAPI + LangGraph)
│   ├── nova_executor/            # 核心模块
│   │   ├── config.py             # 配置管理
│   │   ├── types.py              # 类型定义
│   │   ├── graph.py              # LangGraph 状态机定义
│   │   ├── sandbox.py            # Playwright 浏览器沙箱
│   │   ├── queue.py              # Redis 任务队列
│   │   ├── adapters/             # 模型适配器
│   │   │   ├── vision.py         # Vision 模型适配器
│   │   │   ├── verifier.py       # 验证器适配器
│   │   │   └── executor.py       # 执行器适配器
│   │   ├── nodes/                # 状态机节点
│   │   │   ├── init.py           # 初始化节点
│   │   │   ├── explore.py        # 页面探索节点
│   │   │   ├── check_hil.py      # HIL 检查节点
│   │   │   ├── execute.py        # 执行动作节点
│   │   │   └── verify.py         # 结果验证节点
│   │   ├── streaming/            # WebSocket 推流
│   │   ├── hil/                  # HIL 人机协作
│   │   ├── report/               # 报告生成
│   │   ├── metrics/              # Prometheus 指标
│   │   └── health/               # 健康检查
│   ├── tests/                    # Python 测试套件
│   ├── Dockerfile                # 容器镜像
│   └── pyproject.toml            # Python 项目配置
│
├── src/                          # TypeScript 前端
│   ├── api/                      # REST API
│   │   ├── routes/               # API 路由
│   │   │   ├── task.routes.ts     # 任务管理
│   │   │   ├── instance.routes.ts # 实例管理
│   │   │   └── auth.routes.ts     # 认证授权
│   │   ├── auth/                 # JWT 认证模块
│   │   ├── middleware/           # 中间件 (租户提取)
│   │   └── index.ts              # API 入口
│   │
│   ├── db/                       # 数据库层
│   │   ├── repositories/         # 数据仓库
│   │   │   ├── task.repository.ts
│   │   │   ├── instance.repository.ts
│   │   │   ├── step.repository.ts
│   │   │   └── hil_ticket.repository.ts
│   │   └── prisma.ts             # Prisma 客户端
│   │
│   ├── executor/                 # 执行引擎客户端
│   │   ├── state_machine/        # 状态机定义
│   │   ├── adapters/             # 模型适配器
│   │   ├── worker/               # Worker 服务
│   │   └── types.ts              # 类型定义
│   │
│   ├── queue/                    # 消息队列
│   │   ├── redis.client.ts
│   │   └── task.queue.ts
│   │
│   ├── storage/                  # 对象存储
│   │   └── s3.client.ts
│   │
│   ├── components/               # React 组件
│   │   ├── hil/                  # HIL 面板
│   │   ├── instance/             # 实例组件
│   │   │   ├── ActionCard.tsx
│   │   │   ├── LiveConsole.tsx
│   │   │   ├── LogPanel.tsx
│   │   │   ├── MetricsSummary.tsx
│   │   │   ├── ScreenshotViewer.tsx
│   │   │   └── Timeline.tsx
│   │   ├── report/               # 报告组件
│   │   ├── task/                 # 任务组件
│   │   └── layout/               # 布局组件
│   │
│   ├── stores/                   # 状态管理 (Zustand)
│   │   └── appStore.ts
│   │
│   ├── schemas/                  # Zod 验证模式
│   │   ├── task.schema.ts
│   │   ├── instance.schema.ts
│   │   └── ...
│   │
│   ├── pages/                    # 页面
│   │   ├── Home.tsx
│   │   └── TasksPage.tsx
│   │
│   ├── App.tsx                   # 应用入口
│   └── main.tsx                  # 渲染入口
│
├── prisma/                       # Prisma Schema
│   └── schema.prisma
│
├── tests/                        # TypeScript 测试
│   ├── api/                      # API 测试
│   ├── auth_harness/             # 认证测试
│   ├── db_harness/              # 数据库测试
│   ├── executor/                 # 执行器测试
│   └── schema_harness/           # Schema 测试
│
├── docs/                         # 设计文档
│   ├── design/                   # 架构设计
│   └── 测试用例/                  # 测试用例
│
├── scripts/                      # 部署脚本
│   └── deploy.sh
│
├── docker-compose.yml             # Docker Compose
├── Dockerfile                     # 前端 Dockerfile
├── package.json                   # 前端依赖
├── tsconfig.json                  # TypeScript 配置
└── vite.config.ts                 # Vite 配置
```

## 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| **执行引擎** | Python 3.11 + FastAPI | >=3.11, >=0.115 |
| **状态机** | LangGraph | >=0.2.0 |
| **浏览器自动化** | Playwright | >=1.48 |
| **前端框架** | React + TypeScript | 18.x, 5.x |
| **构建工具** | Vite | 6.x |
| **数据库** | PostgreSQL | 15 |
| **缓存/队列** | Redis | 7 |
| **对象存储** | MinIO (S3) | Latest |
| **ORM** | Prisma | 5.x |
| **样式** | Tailwind CSS | 3.x |
| **状态管理** | Zustand | 5.x |
| **API 验证** | Zod | 4.x |

## 快速开始

### 前置要求

- Node.js >= 18
- Python >= 3.11
- Docker 和 Docker Compose
- PostgreSQL 15+ (或使用 Docker)

### 1. 克隆项目

```bash
git clone <repository-url>
cd nova-test
```

### 2. 启动基础设施

```bash
# 启动数据库、Redis、MinIO
docker-compose up -d postgres redis minio

# 检查服务状态
docker-compose ps
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置以下内容：
# DATABASE_URL=postgresql://nova:password@localhost:5432/nova_test
# REDIS_URL=redis://localhost:6379
# JWT_SECRET=your-secret-key
```

### 4. 初始化数据库

```bash
# 生成 Prisma Client
npx prisma generate

# 运行数据库迁移
npx prisma migrate dev

# 或直接推送 schema
npx prisma db push
```

### 5. 安装依赖

```bash
# 安装前端依赖
npm install

# 安装 Python 依赖
cd executor-python
pip install -e .
cd ..
```

### 6. 启动服务

```bash
# 开发模式启动前端
npm run dev

# 启动 Python 执行引擎
cd executor-python
uvicorn nova_executor.app:app --reload --port 8002

# 或使用 Docker 启动所有服务
docker-compose up -d
```

### 7. 访问应用

| 服务 | 地址 |
|------|------|
| 前端 UI | http://localhost:3000 |
| Python API | http://localhost:8002 |
| Swagger 文档 | http://localhost:8002/docs |
| MinIO Console | http://localhost:9001 |

## 核心概念

### 1. 任务 (Task)

任务是测试的基本单位，包含测试目标和约束条件：

```typescript
interface TestTask {
  id: string;
  name: string;                    // 任务名称
  targetUrl: string;               // 目标网站 URL
  naturalObjective: string;        // 自然语言测试目标
  constraints: {
    maxSteps: number;             // 最大步数限制
    forbiddenDomains: string[];     // 禁止访问的域名
    timeoutSeconds?: number;        // 超时时间
    retryCount?: number;           // 重试次数
  };
  status: 'ACTIVE' | 'PAUSED' | 'ARCHIVED';
}
```

### 2. 实例 (Instance)

实例是任务的一次执行记录：

```typescript
interface AgentInstance {
  id: string;
  taskId: string;                  // 关联的任务 ID
  status: InstanceStatus;
  stepCount: number;              // 当前步数
  hilCount: number;               // HIL 介入次数
  defectCount: number;             // 检测到的缺陷数
  startedAt?: Date;
  completedAt?: Date;
}
```

### 3. 状态机节点

```
┌─────────┐
│  init   │ 初始化浏览器、导航到目标页面
└────┬────┘
     │
     ▼
┌─────────┐
│ explore │ 页面分析、生成动作计划
└────┬────┘
     │
     ▼
┌───────────┐
│ check_hil │ 检查是否需要人工介入
└─────┬─────┘
      │
      ├──── 高风险 ──▶ HIL 等待 ──▶ resume ──┐
      │                                      │
      ▼                                      ▼
┌───────────┐                           ┌─────────┐
│  execute  │ 执行动作                   │  verify │ 验证结果
└─────┬─────┘                           └────┬────┘
      │                                      │
      └────────────── ◀ ────────────────────┘
                      
           ┌─────────┐
           │   end   │ 正常结束
           └─────────┘
```

### 4. HIL 人机协作

Human-in-the-Loop 机制允许在关键决策点引入人工审核：

- **触发条件**: 置信度低于阈值、动作无效、解析失败
- **审核操作**: 批准执行、拒绝、修改动作参数
- **超时处理**: 可配置超时时间，超时后自动拒绝

## API 参考

### 认证

```bash
# 获取 Token
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "password123"
}

# 响应
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "user_xxx",
    "email": "user@example.com",
    "role": "ADMIN"
  }
}
```

### 任务管理

```bash
# 创建任务
POST /api/tasks
Headers: { "x-tenant-id": "tenant_xxx" }
{
  "name": "电商购买流程测试",
  "target_url": "https://shop.example.com",
  "natural_objective": "搜索商品并加入购物车",
  "constraints": {
    "max_steps": 20,
    "forbidden_domains": ["payment.com"]
  }
}

# 获取任务列表
GET /api/tasks?status=ACTIVE&page=1&limit=20

# 获取任务详情
GET /api/tasks/:id

# 更新任务
PATCH /api/tasks/:id
{
  "name": "新名称",
  "status": "PAUSED"
}
```

### 实例管理

```bash
# 创建实例
POST /api/instances
{ "taskId": "task_xxx" }

# 获取实例列表
GET /api/instances?taskId=task_xxx&status=RUNNING

# 获取实例详情
GET /api/instances/:id

# 更新实例状态
PATCH /api/instances/:id/status
{ "status": "TERMINATED" }
```

## 开发指南

### 代码规范

```bash
# 运行 ESLint
npm run lint

# 运行 TypeScript 检查
npm run check

# 运行测试
npm test

# 运行测试 (监听模式)
npm run test:watch
```

### 添加新功能

1. 在 `prisma/schema.prisma` 中定义数据模型
2. 在 `src/db/repositories/` 中创建数据仓库
3. 在 `src/api/routes/` 中添加 API 路由
4. 在 `src/components/` 中创建 UI 组件
5. 添加相应的测试用例

### 状态机扩展

1. 在 `executor-python/nova_executor/nodes/` 中创建新节点
2. 在 `graph.py` 中注册节点
3. 在 `routing.py` 中定义路由规则

## 部署

### Docker Compose (开发/测试)

```bash
# 构建并启动所有服务
docker-compose up -d --build

# 查看日志
docker-compose logs -f executor

# 停止服务
docker-compose down
```

### 生产环境部署

详见 [DEPLOY.md](./DEPLOY.md)

## 测试

```bash
# 运行所有测试
npm test

# 运行特定测试文件
npm test -- tests/api/task.routes.spec.ts

# 生成覆盖率报告
npm run test:coverage
```

## License

MIT

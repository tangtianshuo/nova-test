# Nova Test AaaS Executor - Python FastAPI + LangGraph

基于 FastAPI 和 LangGraph 实现的 AaaS 执行引擎，严格遵循 [docs/design/02_概要设计文档_v1.0.md](file:///d:/Projects/Tauri/nova-test/docs/design/02_概要设计文档_v1.0.md) 的技术栈要求。

## 技术栈

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| **API 框架** | FastAPI (Python) | 高性能 Agent 触发接口 |
| **状态机** | LangGraph | 状态机流转编排 |
| **视觉推理** | Fara-7B (RPC) | 页面分析和动作规划 |
| **浏览器控制** | Playwright | 沙盒内无头浏览器控制 |

## 项目结构

```
executor-python/
├── nova_executor/
│   ├── __init__.py
│   ├── config.py          # 配置管理
│   ├── types.py          # 类型定义
│   ├── graph.py          # LangGraph 状态机
│   ├── sandbox.py         # Playwright 沙箱管理
│   ├── queue.py          # Redis 队列消费者
│   ├── app.py            # FastAPI 应用
│   ├── adapters/         # 适配器
│   │   ├── vision.py     # Vision 适配器 (Fara-7B)
│   │   ├── executor.py    # Executor 适配器 (Playwright)
│   │   ├── verifier.py    # Verifier 适配器
│   │   └── hil_ticket.py # HIL 工单适配器
│   └── nodes/             # 状态机节点
│       ├── init_node.py
│       ├── explore_node.py
│       ├── check_hil_node.py
│       ├── execute_node.py
│       └── verify_node.py
├── tests/                # 测试套件
├── pyproject.toml        # 项目配置
└── .env.example          # 环境变量示例
```

## 快速开始

### 1. 安装依赖

```bash
cd executor-python
pip install -e .
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件
```

### 3. 启动服务

```bash
# 开发模式
uvicorn nova_executor.app:app --reload --port 8002

# 生产模式
uvicorn nova_executor.app:app --host 0.0.0.0 --port 8002
```

### 4. 运行测试

```bash
pytest tests/ -v
```

## API 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/api/v1/tasks/start` | 启动任务 |
| GET | `/api/v1/tasks/{id}/status` | 获取任务状态 |
| POST | `/api/v1/tasks/{id}/resume` | 恢复任务 |
| POST | `/api/v1/tasks/{id}/terminate` | 终止任务 |
| POST | `/api/v1/hil/decide` | HIL 决策 |
| WS | `/ws/stream/{id}` | WebSocket 流 |

## 状态机流程

```
start -> init -> explore -> check_hil -> execute -> verify -> end
                ^                                      |
                +--------------------------------------+
```

## 节点说明

| 节点 | 功能 |
|------|------|
| **init** | 初始化浏览器，生成初始截图 |
| **explore** | 调用 Vision 模型分析页面，生成动作计划 |
| **check_hil** | 评估置信度，决定是否触发 HIL |
| **execute** | 使用 Playwright 执行动作 |
| **verify** | 验证执行结果，检测缺陷 |

## HIL 触发条件

- 置信度低于阈值 (默认 0.7)
- 无动作计划 (解析失败)
- 动作无效 (缺少 selector 等)
- 执行失败

## 严格遵循设计文档

本实现严格遵循 [docs/design/02_概要设计文档_v1.0.md](file:///d:/Projects/Tauri/nova-test/docs/design/02_概要设计文档_v1.0.md) 的要求：

1. ✅ 使用 **FastAPI (Python)** 作为 Agent 触发接口
2. ✅ 使用 **LangGraph** 维护状态机流转
3. ✅ 使用 **Fara-7B** 作为视觉推理大脑
4. ✅ 使用 **Playwright** 提供沙盒内浏览器控制
5. ✅ 实现 LangGraph **Checkpoint** 状态持久化
6. ✅ 实现 **HIL (Human-in-the-Loop)** 人机协作机制

## License

MIT

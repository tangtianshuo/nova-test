# Nova Test 快速启动指南

本文档帮助你在 10 分钟内启动并运行 Nova Test 平台。

## 快速开始（5 分钟）

### 方式一：Docker Compose（推荐）

最快速的方式，使用 Docker Compose 启动所有服务：

```bash
# 1. 克隆项目
git clone <repository-url>
cd nova-test

# 2. 启动所有服务
docker-compose up -d

# 3. 等待服务启动（约 2 分钟）
docker-compose logs -f --tail=50
```

### 方式二：本地开发

如果需要修改代码：

```bash
# 1. 启动基础设施（数据库、Redis、MinIO）
docker-compose up -d postgres redis minio

# 2. 终端 1: 启动前端
npm install
npm run dev

# 3. 终端 2: 启动执行引擎
cd executor-python
pip install -e .
uvicorn nova_executor.app:app --reload --port 8002
```

## 验证安装

打开浏览器访问以下地址：

| 服务 | 地址 | 验证 |
|------|------|------|
| 前端 UI | http://localhost:3000 | 页面正常加载 |
| Python API | http://localhost:8002 | 返回 JSON |
| 健康检查 | http://localhost:8002/health | `{"status":"ok"}` |

## 创建你的第一个测试任务

### 1. 登录系统

默认管理员账号（需要先创建）：

```bash
# 创建管理员用户
docker-compose exec postgres psql -U nova -d nova_test -c \
  "INSERT INTO users (id, tenant_id, email, password_hash, role) VALUES ('admin_001', 'tenant_001', 'admin@example.com', '\$2a\$10\$...', 'ADMIN');"
```

### 2. 创建任务

在 Web UI 中：

1. 点击侧边栏「任务」
2. 点击「新建任务」
3. 填写以下信息：

```
任务名称: 示例电商搜索测试
目标 URL: https://example.com
测试目标: 在搜索框输入 "iPhone"，点击搜索按钮

约束（可选）:
  最大步数: 10
  禁止域名: payment.com, stripe.com
```

4. 点击「创建」

### 3. 启动执行

1. 在任务列表中找到刚创建的任务
2. 点击任务卡片
3. 点击「创建实例」
4. 点击「开始执行」

### 4. 观察执行

- **截图区域**：显示 AI 正在操作的页面
- **动作卡片**：显示当前执行的动作类型和目标
- **日志面板**：实时显示执行日志
- **时间线**：显示已完成的步骤

### 5. 处理 HIL（如有）

当 AI 请求人工审核时：

1. 查看 HIL 面板中的截图和建议动作
2. 选择操作：
   - ✅ **批准**：同意 AI 的建议
   - ❌ **拒绝**：跳过此步骤
   - ✏️ **修改**：修改动作参数后执行

## 常见操作示例

### 通过 API 创建任务

```bash
# 获取 Token
curl -X POST http://localhost:8002/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}'

# 创建任务
curl -X POST http://localhost:8002/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -d '{
    "name": "API 创建的任务",
    "target_url": "https://example.com",
    "natural_objective": "搜索商品并查看详情",
    "constraints": {
      "max_steps": 15,
      "forbidden_domains": ["payment.com"]
    }
  }'
```

### 启动任务执行

```bash
# 创建实例并启动
curl -X POST http://localhost:8002/api/v1/tasks/<task_id>/start \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

### 查看 HIL 工单

```bash
# 列出待处理的 HIL 工单
curl http://localhost:8002/api/v1/hil/tickets \
  -H "Authorization: Bearer <YOUR_TOKEN>"

# 提交决策
curl -X POST http://localhost:8002/api/v1/hil/decide \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -d '{
    "ticket_id": "hil_xxx",
    "decision": "APPROVED",
    "feedback": "动作看起来正确"
  }'
```

## 项目命令参考

### 前端 (Node.js)

```bash
# 开发
npm run dev              # 启动开发服务器
npm run build            # 生产构建
npm run lint             # ESLint 检查
npm run check            # TypeScript 类型检查
npm test                 # 运行测试
npm run test:coverage    # 测试覆盖率

# 格式化
npx prettier --write src/
npx eslint --fix src/
```

### 后端 (Python)

```bash
# 进入目录
cd executor-python

# 安装依赖
pip install -e .

# 开发
uvicorn nova_executor.app:app --reload --port 8002

# 测试
pytest tests/ -v
pytest tests/ -v --cov=nova_executor
```

### 数据库

```bash
# Prisma 操作
npx prisma generate      # 生成 Client
npx prisma migrate dev   # 开发迁移
npx prisma db push       # 推送 Schema
npx prisma studio        # 打开 Studio

# Docker 数据库操作
docker-compose exec postgres psql -U nova -d nova_test
```

### Docker

```bash
# 启动/停止
docker-compose up -d          # 启动
docker-compose down            # 停止
docker-compose down -v         # 停止并删除数据

# 日志
docker-compose logs -f         # 查看所有日志
docker-compose logs -f executor # 查看特定服务

# 重启
docker-compose restart         # 重启所有
docker-compose restart executor # 重启特定服务
```

## 故障排查

### 服务无法启动

```bash
# 1. 检查 Docker 状态
docker ps

# 2. 查看日志
docker-compose logs

# 3. 清理重建
docker-compose down -v
docker-compose up -d --build
```

### 数据库连接失败

```bash
# 检查数据库是否运行
docker-compose ps postgres

# 测试连接
docker-compose exec postgres psql -U nova -d nova_test -c "SELECT 1;"

# 查看数据库日志
docker-compose logs postgres
```

### 前端无法访问

```bash
# 检查端口占用
lsof -i :3000

# 检查前端日志
docker-compose logs frontend

# 重新构建前端
docker-compose build frontend
docker-compose up -d frontend
```

### 执行引擎报错

```bash
# 查看日志
docker-compose logs executor

# 进入容器调试
docker-compose exec executor bash
```

## 下一步

- 📖 阅读 [完整用户手册](./USER_GUIDE.md)
- 🏗️ 阅读 [部署指南](./DEPLOY.md)
- 📡 查看 [API 参考](./API.md)
- 🧪 查看 [测试用例文档](./docs/测试用例/README.md)

## 获取帮助

- 📧 邮件支持: support@example.com
- 📖 在线文档: https://docs.example.com
- 🐛 问题反馈: https://github.com/example/nova-test/issues

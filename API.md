# Nova Test API 参考文档

本文档详细描述 Nova Test 平台的 REST API 接口。

## 基础信息

| 项目 | 说明 |
|------|------|
| 基础 URL | `http://localhost:8002` (本地开发) |
| 认证方式 | JWT Bearer Token |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |

## 认证

### 登录

用户登录获取访问令牌。

```
POST /api/v1/auth/login
```

**请求体**

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**响应 (200 OK)**

```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "user_abc123",
    "email": "user@example.com",
    "role": "TESTER",
    "tenantId": "tenant_xyz"
  },
  "expiresAt": "2024-01-22T10:00:00Z"
}
```

**错误响应 (401 Unauthorized)**

```json
{
  "success": false,
  "error": {
    "code": "AUTH_INVALID_CREDENTIALS",
    "message": "邮箱或密码错误"
  }
}
```

---

### 注册

用户注册（需要管理员权限）。

```
POST /api/v1/auth/register
```

**请求体**

```json
{
  "email": "newuser@example.com",
  "password": "SecurePassword123",
  "role": "TESTER"
}
```

---

### 获取当前用户

```
GET /api/v1/auth/me
Headers: Authorization: Bearer <token>
```

**响应 (200 OK)**

```json
{
  "success": true,
  "user": {
    "id": "user_abc123",
    "email": "user@example.com",
    "role": "TESTER",
    "tenantId": "tenant_xyz",
    "createdAt": "2024-01-01T00:00:00Z"
  }
}
```

---

## 任务管理

### 创建任务

```
POST /api/v1/tasks
Headers:
  Authorization: Bearer <token>
  Content-Type: application/json
  x-tenant-id: <tenant_id>
```

**请求体**

```json
{
  "name": "电商搜索流程测试",
  "target_url": "https://shop.example.com",
  "natural_objective": "搜索关键词 'iPhone'，点击第一个商品查看详情",
  "constraints": {
    "max_steps": 20,
    "forbidden_domains": ["payment.com", "stripe.com"],
    "timeout_seconds": 45,
    "retry_count": 2
  }
}
```

**字段说明**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 任务名称，1-255 字符 |
| `target_url` | string | ✅ | 目标网站 URL，必须是有效 URL |
| `natural_objective` | string | ✅ | 自然语言测试目标 |
| `constraints.max_steps` | integer | 否 | 最大步数限制 (1-100)，默认 50 |
| `constraints.forbidden_domains` | string[] | 否 | 禁止访问的域名列表 |
| `constraints.timeout_seconds` | integer | 否 | 单步超时时间（秒） |
| `constraints.retry_count` | integer | 否 | 失败重试次数 |

**响应 (201 Created)**

```json
{
  "success": true,
  "data": {
    "task_id": "task_abc123",
    "status": "ACTIVE",
    "created_at": "2024-01-15T14:30:00Z"
  }
}
```

---

### 获取任务列表

```
GET /api/v1/tasks
Headers: Authorization: Bearer <token>
Query Parameters:
  status: ACTIVE | PAUSED | ARCHIVED (可选)
  page: integer (默认 1)
  limit: integer (默认 20, 最大 100)
```

**响应 (200 OK)**

```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "task_id": "task_abc123",
        "name": "电商搜索流程测试",
        "target_url": "https://shop.example.com",
        "natural_objective": "搜索关键词 'iPhone'",
        "status": "ACTIVE",
        "created_at": "2024-01-15T14:30:00Z",
        "updated_at": "2024-01-15T14:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 45,
      "total_pages": 3
    }
  }
}
```

---

### 获取任务详情

```
GET /api/v1/tasks/{task_id}
Headers: Authorization: Bearer <token>
```

**响应 (200 OK)**

```json
{
  "success": true,
  "data": {
    "task_id": "task_abc123",
    "tenant_id": "tenant_xyz",
    "name": "电商搜索流程测试",
    "target_url": "https://shop.example.com",
    "natural_objective": "搜索关键词 'iPhone'，点击第一个商品查看详情",
    "constraints": {
      "max_steps": 20,
      "forbidden_domains": ["payment.com", "stripe.com"],
      "timeout_seconds": 45,
      "retry_count": 2
    },
    "status": "ACTIVE",
    "created_at": "2024-01-15T14:30:00Z",
    "updated_at": "2024-01-15T14:30:00Z"
  }
}
```

---

### 更新任务

```
PATCH /api/v1/tasks/{task_id}
Headers:
  Authorization: Bearer <token>
  Content-Type: application/json
```

**请求体**

```json
{
  "name": "更新后的任务名称",
  "target_url": "https://new-url.example.com",
  "constraints": {
    "max_steps": 25
  },
  "status": "PAUSED"
}
```

**响应 (200 OK)**

```json
{
  "success": true,
  "data": {
    "task_id": "task_abc123",
    "updated_at": "2024-01-15T15:00:00Z"
  }
}
```

---

### 删除任务

```
DELETE /api/v1/tasks/{task_id}
Headers: Authorization: Bearer <token>
```

**响应 (200 OK)**

```json
{
  "success": true,
  "message": "任务已删除"
}
```

---

## 实例管理

### 创建实例

创建任务的执行实例。

```
POST /api/v1/instances
Headers:
  Authorization: Bearer <token>
  Content-Type: application/json
```

**请求体**

```json
{
  "task_id": "task_abc123"
}
```

**响应 (201 Created)**

```json
{
  "success": true,
  "data": {
    "instance_id": "ins_xyz789",
    "task_id": "task_abc123",
    "status": "PENDING",
    "created_at": "2024-01-15T14:35:00Z"
  }
}
```

---

### 获取实例列表

```
GET /api/v1/instances
Headers: Authorization: Bearer <token>
Query Parameters:
  task_id: string (可选，筛选特定任务)
  status: PENDING | RUNNING | WAITING_HIL | COMPLETED | FAILED | TERMINATED (可选)
  page: integer (默认 1)
  limit: integer (默认 20)
```

**响应 (200 OK)**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "instance_id": "ins_xyz789",
        "task_id": "task_abc123",
        "status": "RUNNING",
        "step_count": 5,
        "hil_count": 1,
        "defect_count": 0,
        "created_at": "2024-01-15T14:35:00Z",
        "started_at": "2024-01-15T14:35:05Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 12,
      "total_pages": 1
    }
  }
}
```

---

### 获取实例详情

```
GET /api/v1/instances/{instance_id}
Headers: Authorization: Bearer <token>
```

**响应 (200 OK)**

```json
{
  "success": true,
  "data": {
    "instance_id": "ins_xyz789",
    "task_id": "task_abc123",
    "status": "RUNNING",
    "step_count": 5,
    "hil_count": 1,
    "defect_count": 0,
    "started_at": "2024-01-15T14:35:05Z",
    "steps": [
      {
        "step_number": 1,
        "node_name": "init",
        "screenshot_url": "https://s3.example.com/screenshots/ins_xyz789/step_1.png",
        "executed_at": "2024-01-15T14:35:06Z"
      }
    ]
  }
}
```

---

### 更新实例状态

```
PATCH /api/v1/instances/{instance_id}/status
Headers:
  Authorization: Bearer <token>
  Content-Type: application/json
```

**请求体**

```json
{
  "status": "TERMINATED"
}
```

**响应 (200 OK)**

```json
{
  "success": true,
  "data": {
    "instance_id": "ins_xyz789",
    "status": "TERMINATED",
    "updated_at": "2024-01-15T14:40:00Z"
  }
}
```

---

## HIL 人机协作

### 获取 HIL 工单列表

```
GET /api/v1/hil/tickets
Headers: Authorization: Bearer <token>
Query Parameters:
  status: WAITING | APPROVED | REJECTED | EXPIRED (可选)
  instance_id: string (可选)
```

**响应 (200 OK)**

```json
{
  "success": true,
  "data": {
    "tickets": [
      {
        "ticket_id": "hil_abc456",
        "instance_id": "ins_xyz789",
        "step_no": 5,
        "reason": "置信度 0.65 低于阈值 0.7",
        "risk_level": "MEDIUM",
        "status": "WAITING",
        "planned_action": {
          "action_type": "type",
          "selector": "#search-input",
          "value": "iPhone 15"
        },
        "screenshot_url": "https://s3.example.com/screenshots/hil_abc456.png",
        "created_at": "2024-01-15T14:38:00Z",
        "expires_at": "2024-01-15T14:43:00Z"
      }
    ]
  }
}
```

---

### 提交 HIL 决策

```
POST /api/v1/hil/decide
Headers:
  Authorization: Bearer <token>
  Content-Type: application/json
```

**请求体**

```json
{
  "ticket_id": "hil_abc456",
  "decision": "APPROVED",
  "feedback": "动作看起来正确，执行吧",
  "modified_action": null
}
```

**或修改动作后批准**

```json
{
  "ticket_id": "hil_abc456",
  "decision": "MODIFIED",
  "feedback": "选择器需要调整",
  "modified_action": {
    "action_type": "click",
    "selector": "#search-btn",
    "value": null
  }
}
```

**字段说明**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `ticket_id` | string | ✅ | 工单 ID |
| `decision` | string | ✅ | APPROVED / REJECTED / MODIFIED |
| `feedback` | string | 否 | 用户反馈意见 |
| `modified_action` | object | 条件必填 | decision=MODIFIED 时必填 |
| `modified_action.action_type` | string | 条件必填 | click / type / navigate / screenshot |
| `modified_action.selector` | string | 条件必填 | CSS 选择器或 URL |
| `modified_action.value` | string | 否 | type 动作的输入值 |

**响应 (200 OK)**

```json
{
  "success": true,
  "data": {
    "ticket_id": "hil_abc456",
    "decision": "APPROVED",
    "decided_at": "2024-01-15T14:39:30Z"
  }
}
```

---

## 报告

### 获取实例报告

```
GET /api/v1/reports/{instance_id}
Headers: Authorization: Bearer <token>
```

**响应 (200 OK)**

```json
{
  "success": true,
  "data": {
    "report_id": "rpt_abc789",
    "instance_id": "ins_xyz789",
    "summary": {
      "total_steps": 18,
      "success_rate": 0.889,
      "total_defects": 1,
      "hil_count": 3,
      "execution_duration_seconds": 154.5
    },
    "steps": [
      {
        "step_number": 1,
        "node_name": "init",
        "action_type": "navigate",
        "thought": "导航到目标页面",
        "screenshot_url": "https://s3.example.com/reports/ins_xyz789/step_1.png",
        "is_success": true,
        "executed_at": "2024-01-15T14:35:06Z"
      }
    ],
    "defects": [
      {
        "step_number": 7,
        "description": "页面显示 '商品已下架'",
        "expected": "应显示商品详情",
        "actual": "商品已下架",
        "screenshot_url": "https://s3.example.com/reports/ins_xyz789/defect_1.png"
      }
    ]
  }
}
```

---

### 导出报告

```
GET /api/v1/reports/{instance_id}/export
Headers: Authorization: Bearer <token>
Query Parameters:
  format: json | html | pdf
```

**响应**

根据 `format` 参数返回对应格式的文件：
- `json`: 返回 JSON 文件
- `html`: 返回 HTML 文件（可交互）
- `pdf`: 返回 PDF 文件

---

## WebSocket 实时推送

### 连接

```
WS /ws/stream?instance_id={instance_id}&token={token}
```

### 消息格式

**执行事件**

```json
{
  "type": "step",
  "data": {
    "step_number": 5,
    "node_name": "execute",
    "action": {
      "type": "click",
      "selector": "#search-btn"
    },
    "screenshot_url": "https://s3.example.com/screenshots/step_5.png",
    "timestamp": "2024-01-15T14:38:30Z"
  }
}
```

**状态更新**

```json
{
  "type": "status",
  "data": {
    "status": "WAITING_HIL",
    "message": "等待 HIL 决策"
  }
}
```

**HIL 通知**

```json
{
  "type": "hil_ticket",
  "data": {
    "ticket_id": "hil_abc456",
    "step_number": 5,
    "risk_level": "MEDIUM",
    "reason": "置信度低于阈值"
  }
}
```

**执行完成**

```json
{
  "type": "completed",
  "data": {
    "status": "COMPLETED",
    "summary": {
      "total_steps": 18,
      "success_rate": 0.889
    }
  }
}
```

---

## 健康检查

### 健康状态

```
GET /health
```

**响应 (200 OK)**

```json
{
  "status": "ok",
  "timestamp": "2024-01-15T14:30:00Z",
  "version": "1.0.0"
}
```

---

### 就绪检查

```
GET /ready
```

**响应 (200 OK)**

```json
{
  "ready": true,
  "checks": {
    "database": "ok",
    "redis": "ok",
    "s3": "ok"
  }
}
```

---

### 指标

```
GET /metrics
```

返回 Prometheus 格式的指标数据。

---

## 错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| `ERR_400` | 400 | 请求参数错误 |
| `ERR_401` | 401 | 未认证或认证失败 |
| `ERR_403` | 403 | 权限不足 |
| `ERR_404` | 404 | 资源不存在 |
| `ERR_409` | 409 | 资源冲突 |
| `ERR_422` | 422 | Schema 验证失败 |
| `ERR_429` | 429 | 请求过于频繁 |
| `ERR_500` | 500 | 服务器内部错误 |
| `ERR_503` | 503 | 服务不可用 |

---

## 速率限制

| 端点类型 | 限制 |
|----------|------|
| 读取操作 (GET) | 100 请求/分钟 |
| 写入操作 (POST/PATCH) | 50 请求/分钟 |
| HIL 决策 | 200 请求/分钟 |

---

## 示例代码

### JavaScript / Node.js

```javascript
const axios = require('axios');

const API_BASE = 'http://localhost:8002/api/v1';

// 登录
async function login(email, password) {
  const response = await axios.post(`${API_BASE}/auth/login`, {
    email,
    password
  });
  return response.data.token;
}

// 创建任务
async function createTask(token, taskData) {
  const response = await axios.post(`${API_BASE}/tasks`, taskData, {
    headers: {
      Authorization: `Bearer ${token}`,
      'x-tenant-id': 'tenant_001'
    }
  });
  return response.data;
}

// 使用
const token = await login('user@example.com', 'password');
const task = await createTask(token, {
  name: '测试任务',
  target_url: 'https://example.com',
  natural_objective: '搜索并点击第一个结果'
});
console.log(task);
```

### Python

```python
import requests

API_BASE = 'http://localhost:8002/api/v1'

# 登录
def login(email, password):
    response = requests.post(
        f'{API_BASE}/auth/login',
        json={'email': email, 'password': password}
    )
    return response.json()['token']

# 创建任务
def create_task(token, task_data):
    response = requests.post(
        f'{API_BASE}/tasks',
        json=task_data,
        headers={'Authorization': f'Bearer {token}'}
    )
    return response.json()

# 使用
token = login('user@example.com', 'password')
task = create_task(token, {
    'name': '测试任务',
    'target_url': 'https://example.com',
    'natural_objective': '搜索并点击第一个结果'
})
print(task)
```

### cURL

```bash
# 登录
TOKEN=$(curl -s -X POST http://localhost:8002/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | jq -r '.token')

# 创建任务
curl -X POST http://localhost:8002/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "测试任务",
    "target_url": "https://example.com",
    "natural_objective": "搜索并点击第一个结果"
  }'
```

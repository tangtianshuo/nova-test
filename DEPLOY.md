# Nova Test 部署指南

本文档详细介绍 Nova Test AaaS 平台的多种部署方式，包括开发环境、测试环境和生产环境。

## 目录

- [环境要求](#环境要求)
- [开发环境部署](#开发环境部署)
- [Docker Compose 部署](#docker-compose-部署)
- [生产环境部署](#生产环境部署)
- [Kubernetes 部署](#kubernetes-部署)
- [配置参考](#配置参考)
- [运维指南](#运维指南)
- [故障排查](#故障排查)

---

## 环境要求

### 硬件要求

| 环境 | CPU | 内存 | 磁盘 | 说明 |
|------|-----|------|------|------|
| 开发/测试 | 2 核 | 4 GB | 20 GB | 可使用 Docker Desktop |
| 小规模生产 | 4 核 | 8 GB | 50 GB | 单节点部署 |
| 中等规模生产 | 8 核 | 16 GB | 100 GB | 多服务集群 |
| 大规模生产 | 16+ 核 | 32+ GB | 200+ GB | 高可用集群 |

### 软件要求

| 软件 | 版本 | 用途 |
|------|------|------|
| Docker | 24.0+ | 容器运行时 |
| Docker Compose | 2.20+ | 容器编排 |
| Node.js | 18+ | 前端构建 |
| Python | 3.11+ | 执行引擎 |
| PostgreSQL | 15+ | 主数据库 |
| Redis | 7+ | 缓存和队列 |

### 网络要求

- 端口 3000: 前端 UI
- 端口 5432: PostgreSQL
- 端口 6379: Redis
- 端口 8002: Python API
- 端口 9000/9001: MinIO

---

## 开发环境部署

### 方式一：本地开发

#### 1. 克隆代码

```bash
git clone <repository-url>
cd nova-test
```

#### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
cat > .env << 'EOF'
# 数据库配置
DATABASE_URL=postgresql://nova:password@localhost:5432/nova_test

# Redis 配置
REDIS_URL=redis://localhost:6379

# JWT 配置
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_EXPIRES_IN=7d

# S3/MinIO 配置
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin123
S3_BUCKET=nova-test
S3_REGION=us-east-1

# Python 执行引擎配置
EXECUTOR_API_URL=http://localhost:8002
EOF
```

#### 3. 启动基础设施

```bash
# 使用 Docker 启动数据库服务
docker run -d \
  --name nova-postgres \
  -e POSTGRES_DB=nova_test \
  -e POSTGRES_USER=nova \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15-alpine

docker run -d \
  --name nova-redis \
  -p 6379:6379 \
  redis:7-alpine

docker run -d \
  --name nova-minio \
  -p 9000:9000 \
  -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin123 \
  -v minio_data:/data \
  minio/minio server /data --console-address ":9001"
```

#### 4. 初始化数据库

```bash
# 安装前端依赖
npm install

# 生成 Prisma Client
npx prisma generate

# 推送数据库 Schema
npx prisma db push

# 创建初始管理员用户（需要手动在数据库中创建）
```

#### 5. 启动服务

```bash
# 终端 1: 启动前端开发服务器
npm run dev

# 终端 2: 启动 Python 执行引擎
cd executor-python
pip install -e .
uvicorn nova_executor.app:app --reload --port 8002 --host 0.0.0.0
```

#### 6. 验证部署

访问以下地址确认服务运行正常：

| 服务 | 地址 | 验证方式 |
|------|------|----------|
| 前端 | http://localhost:3000 | 页面加载 |
| Python API | http://localhost:8002 | JSON 响应 |
| API 健康检查 | http://localhost:8002/health | `{"status":"ok"}` |
| Swagger 文档 | http://localhost:8002/docs | API 文档页面 |
| MinIO Console | http://localhost:9001 | 登录界面 |

---

## Docker Compose 部署

### 开发/测试环境

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务（保留数据）
docker-compose down

# 停止服务（删除数据）
docker-compose down -v
```

### 环境变量文件

创建 `.env.prod` 文件：

```bash
# 生产环境配置
NODE_ENV=production
PORT=3000

# 数据库
DATABASE_URL=postgresql://nova:password@postgres:5432/nova_test

# Redis
REDIS_URL=redis://redis:6379

# JWT (必须修改)
JWT_SECRET=change-this-to-a-very-long-random-string-in-production
JWT_EXPIRES_IN=24h

# S3/MinIO
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin123
S3_BUCKET=nova-test
S3_REGION=us-east-1

# Python 执行引擎
EXECUTOR_API_URL=http://executor:8002
```

### 使用生产配置启动

```bash
docker-compose --env-file .env.prod up -d
```

---

## 生产环境部署

### 架构设计

```
                           ┌─────────────────┐
                           │   Nginx/LB     │
                           │   (HTTPS)      │
                           └────────┬────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           │                        │                        │
           ▼                        ▼                        ▼
    ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
    │   Frontend  │          │   Frontend  │          │   Frontend  │
    │  (Node.js) │          │  (Node.js) │          │  (Node.js) │
    │   :3000     │          │   :3000     │          │   :3000     │
    └──────┬──────┘          └──────┬──────┘          └──────┬──────┘
           │                        │                        │
           └────────────────────────┼────────────────────────┘
                                    │
                           ┌────────┴────────┐
                           │   Nginx / API   │
                           │   Gateway       │
                           └────────┬────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           │                        │                        │
           ▼                        ▼                        ▼
    ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
    │  Executor   │          │  Executor   │          │  Executor   │
    │ (FastAPI)   │          │ (FastAPI)   │          │ (FastAPI)   │
    │   :8002     │          │   :8002     │          │   :8002     │
    └──────┬──────┘          └──────┬──────┘          └──────┬──────┘
           │                        │                        │
           └────────────────────────┼────────────────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           │                        │                        │
           ▼                        ▼                        ▼
    ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
    │ PostgreSQL  │          │    Redis    │          │    MinIO    │
    │  Primary    │          │   Cluster   │          │   Cluster   │
    │   :5432     │          │   :6379     │          │  :9000/9001 │
    └─────────────┘          └─────────────┘          └─────────────┘
```

### 前置准备

#### 1. 服务器准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要工具
sudo apt install -y \
  curl \
  wget \
  git \
  ufw \
  fail2ban \
  nginx \
  certbot \
  python3-certbot-nginx

# 安装 Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 2. 目录结构

```bash
sudo mkdir -p /opt/nova-test
sudo mkdir -p /data/postgres
sudo mkdir -p /data/minio
sudo mkdir -p /var/log/nova-test

sudo chown -R $USER:$USER /opt/nova-test /data /var/log/nova-test
```

#### 3. SSL 证书

```bash
# 使用 Let's Encrypt
sudo certbot --nginx -d api.example.com

# 或手动放置证书
sudo mkdir -p /etc/nginx/ssl
sudo cp your-cert.crt /etc/nginx/ssl/server.crt
sudo cp your-cert.key /etc/nginx/ssl/server.key
```

### 部署步骤

#### 1. 创建生产环境配置文件

```bash
cd /opt/nova-test

cat > .env.production << 'EOF'
# 应用配置
NODE_ENV=production
PORT=3000

# 数据库 (外部 PostgreSQL)
DATABASE_URL=postgresql://nova:PASSWORD@db.example.com:5432/nova_test

# Redis (外部 Redis)
REDIS_URL=redis://redis.example.com:6379

# JWT (必须使用强密钥)
JWT_SECRET=GENERATE_A_64_CHARACTER_RANDOM_STRING_HERE
JWT_EXPIRES_IN=24h

# S3/MinIO (外部或自托管)
S3_ENDPOINT=https://s3.example.com
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
S3_BUCKET=nova-test
S3_REGION=us-east-1

# Python 执行引擎
EXECUTOR_API_URL=http://localhost:8002
EOF

chmod 600 .env.production
```

#### 2. 配置 Nginx

```bash
sudo cat > /etc/nginx/sites-available/nova-test << 'EOF'
upstream frontend {
    server 127.0.0.1:3000;
}

upstream api {
    server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name nova.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name nova.example.com;

    ssl_certificate /etc/letsencrypt/live/nova.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/nova.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # Gzip 配置
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    # 前端静态文件
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # API 代理
    location /api {
        proxy_pass http://api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket 支持
    location /ws {
        proxy_pass http://api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 健康检查
    location /health {
        proxy_pass http://api/health;
        access_log off;
    }

    # 日志
    access_log /var/log/nginx/nova-test.access.log;
    error_log /var/log/nginx/nova-test.error.log;
}
EOF

sudo ln -s /etc/nginx/sites-available/nova-test /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 3. 使用 Docker Compose 启动

```bash
# 创建 docker-compose.prod.yml
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  frontend:
    build:
      context: .
      dockerfile: Dockerfile
    restart: always
    ports:
      - "127.0.0.1:3000:3000"
    environment:
      - NODE_ENV=production
      - API_BASE_URL=http://localhost:8002
    depends_on:
      - executor
    networks:
      - nova-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3

  executor:
    build:
      context: ./executor-python
      dockerfile: Dockerfile
    restart: always
    ports:
      - "127.0.0.1:8002:8002"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - S3_ENDPOINT=${S3_ENDPOINT}
      - S3_ACCESS_KEY=${S3_ACCESS_KEY}
      - S3_SECRET_KEY=${S3_SECRET_KEY}
      - S3_BUCKET=${S3_BUCKET}
      - S3_REGION=${S3_REGION}
      - JWT_SECRET=${JWT_SECRET}
    volumes:
      - /var/log/nova-test:/app/logs
    networks:
      - nova-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  nova-network:
    driver: bridge
EOF

# 启动服务
docker-compose -f docker-compose.prod.yml up -d --build

# 查看状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

---

## Kubernetes 部署

### Helm Chart 结构

```
nova-test/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── deployment-frontend.yaml
│   ├── deployment-executor.yaml
│   ├── service-frontend.yaml
│   ├── service-executor.yaml
│   ├── ingress.yaml
│   └── horizontalpodautoscaler.yaml
```

### 部署命令

```bash
# 添加 Helm 仓库
helm repo add nova-test https://charts.example.com

# 安装
helm install nova-test nova-test/nova-test \
  --namespace nova-test \
  --create-namespace \
  --values values.prod.yaml

# 升级
helm upgrade nova-test nova-test/nova-test \
  --namespace nova-test \
  --values values.prod.yaml

# 查看状态
helm status nova-test -n nova-test

# 删除
helm uninstall nova-test -n nova-test
```

---

## 配置参考

### 环境变量详解

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `DATABASE_URL` | 是 | - | PostgreSQL 连接字符串 |
| `REDIS_URL` | 是 | - | Redis 连接字符串 |
| `JWT_SECRET` | 是 | - | JWT 签名密钥 (至少 32 字符) |
| `JWT_EXPIRES_IN` | 否 | `7d` | Token 过期时间 |
| `S3_ENDPOINT` | 否 | - | S3/MinIO 端点 |
| `S3_ACCESS_KEY` | 否 | - | S3 访问密钥 |
| `S3_SECRET_KEY` | 否 | - | S3 密钥 |
| `S3_BUCKET` | 否 | `nova-test` | 存储桶名称 |
| `S3_REGION` | 否 | `us-east-1` | 区域 |

### Prisma 配置

```bash
# 生产环境使用连接池
DATABASE_URL="postgresql://user:pass@host:5432/db?schema=public&connection_limit=10&pool_timeout=20"
```

### Redis 配置

```bash
# 生产环境建议使用集群模式
REDIS_URL="redis://redis-cluster.example.com:6379"
```

---

## 运维指南

### 日常维护

```bash
# 查看服务状态
docker-compose ps

# 查看资源使用
docker stats

# 查看日志
docker-compose logs -f --tail=100

# 清理未使用的资源
docker system prune -f

# 备份数据库
docker exec nova-postgres pg_dump -U nova nova_test > backup_$(date +%Y%m%d).sql

# 恢复数据库
cat backup.sql | docker exec -i nova-postgres psql -U nova nova_test
```

### 监控

```bash
# 查看健康状态
curl http://localhost:8002/health

# 查看指标
curl http://localhost:8002/metrics

# 查看前端构建
curl http://localhost:3000/api/health
```

### 更新升级

```bash
# 拉取最新代码
git pull origin main

# 重新构建
docker-compose build --no-cache

# 重启服务
docker-compose up -d

# 运行迁移
npx prisma migrate deploy
```

---

## 故障排查

### 常见问题

#### 1. 数据库连接失败

```bash
# 检查 PostgreSQL 日志
docker-compose logs postgres | grep ERROR

# 测试连接
docker exec -it nova-postgres psql -U nova -d nova_test -c "SELECT 1"
```

#### 2. Redis 连接失败

```bash
# 检查 Redis 日志
docker-compose logs redis | grep ERROR

# 测试连接
docker exec -it nova-redis redis-cli ping
```

#### 3. 前端构建失败

```bash
# 清理缓存
rm -rf node_modules package-lock.json
npm install

# 重新构建
npm run build
```

#### 4. 执行引擎启动失败

```bash
# 查看详细日志
cd executor-python
python -c "from nova_executor import app; print('OK')"

# 检查依赖
pip install -e . --force-reinstall
```

### 日志位置

| 服务 | 日志位置 |
|------|----------|
| Nginx | `/var/log/nginx/` |
| Frontend | `docker-compose logs frontend` |
| Executor | `docker-compose logs executor` |
| PostgreSQL | `docker-compose logs postgres` |
| Redis | `docker-compose logs redis` |

---

## 安全建议

1. **定期更新依赖**
   ```bash
   npm audit fix
   pip-audit
   ```

2. **使用强密码和密钥**
   - JWT_SECRET 使用 64+ 字符随机字符串
   - 数据库密码定期轮换

3. **配置防火墙**
   ```bash
   sudo ufw allow 22/tcp    # SSH
   sudo ufw allow 80/tcp    # HTTP
   sudo ufw allow 443/tcp   # HTTPS
   sudo ufw enable
   ```

4. **启用 Fail2Ban**
   ```bash
   sudo systemctl enable fail2ban
   sudo systemctl start fail2ban
   ```

5. **定期备份**
   ```bash
   # 每天凌晨 3 点备份
   0 3 * * * /opt/nova-test/scripts/backup.sh
   ```

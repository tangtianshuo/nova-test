/**
 * 任务 API 契约测试
 * 职责：验证任务 API 的请求/响应契约
 * @version 1.0.0
 */

import { describe, it, expect, beforeAll, afterAll, vi } from 'vitest';
import request from 'supertest';
import app from '../../src/api';

const TENANT_ID = 'test-tenant-001';

vi.mock('../../src/db/prisma', () => ({
  default: {
    testTask: {
      create: vi.fn(async (data: { data: { tenantId: string; name: string; targetUrl: string; naturalObjective: string; constraints: unknown } }) => ({
        id: `task-${Date.now()}`,
        tenantId: data.data.tenantId,
        name: data.data.name,
        targetUrl: data.data.targetUrl,
        naturalObjective: data.data.naturalObjective,
        constraints: data.data.constraints,
        status: 'ACTIVE',
        createdAt: new Date(),
        updatedAt: new Date(),
      })),
      findFirst: vi.fn(async () => null),
      findMany: vi.fn(async () => []),
      update: vi.fn(async () => null),
      delete: vi.fn(async () => {}),
      count: vi.fn(async () => 0),
    },
  },
}));

describe('Task API Contract Tests', () => {
  describe('POST /api/tasks - 创建任务', () => {
    it('应使用有效数据成功创建任务', async () => {
      const validPayload = {
        tenant_id: TENANT_ID,
        name: '电商核心购买流程测试',
        target_url: 'https://shop.example.com',
        natural_objective: '搜索MacBook，加入购物车并结算，不进行最终付款',
        constraints: {
          max_steps: 50,
          forbidden_domains: ['stripe.com', 'alipay.com'],
        },
      };

      const response = await request(app)
        .post('/api/tasks')
        .set('x-tenant-id', TENANT_ID)
        .send(validPayload);

      expect(response.status).toBe(201);
      expect(response.body).toHaveProperty('status', 'success');
      expect(response.body.data).toHaveProperty('task_id');
      expect(response.body.data).toHaveProperty('status', 'ACTIVE');
      expect(response.body.data).toHaveProperty('created_at');
    });

    it('应拒绝缺少必填字段的请求', async () => {
      const invalidPayload = {
        name: '测试任务',
      };

      const response = await request(app)
        .post('/api/tasks')
        .set('x-tenant-id', TENANT_ID)
        .send(invalidPayload);

      expect(response.status).toBe(400);
      expect(response.body).toHaveProperty('status', 'error');
      expect(response.body.error).toHaveProperty('code', 'ERR_400');
      expect(response.body.error.message).toContain('参数不符合 Schema 规范');
    });

    it('应拒绝无效的 URL 格式', async () => {
      const invalidPayload = {
        tenant_id: TENANT_ID,
        name: '测试任务',
        target_url: 'not-a-valid-url',
        natural_objective: '测试目标',
      };

      const response = await request(app)
        .post('/api/tasks')
        .set('x-tenant-id', TENANT_ID)
        .send(invalidPayload);

      expect(response.status).toBe(400);
      expect(response.body).toHaveProperty('status', 'error');
      expect(response.body.error).toHaveProperty('code', 'ERR_400');
    });

    it('应拒绝缺少 x-tenant-id 请求头', async () => {
      const validPayload = {
        tenant_id: TENANT_ID,
        name: '测试任务',
        target_url: 'https://example.com',
        natural_objective: '测试目标',
      };

      const response = await request(app)
        .post('/api/tasks')
        .send(validPayload);

      expect(response.status).toBe(401);
      expect(response.body).toHaveProperty('status', 'error');
      expect(response.body.error).toHaveProperty('code', 'ERR_401');
    });

    it('应使用默认约束值创建任务', async () => {
      const payloadWithoutConstraints = {
        tenant_id: TENANT_ID,
        name: '简单测试任务',
        target_url: 'https://example.com',
        natural_objective: '简单目标',
      };

      const response = await request(app)
        .post('/api/tasks')
        .set('x-tenant-id', TENANT_ID)
        .send(payloadWithoutConstraints);

      expect(response.status).toBe(201);
      expect(response.body).toHaveProperty('status', 'success');
    });
  });

  describe('GET /api/tasks - 获取任务列表', () => {
    it('应成功返回任务列表', async () => {
      const response = await request(app)
        .get('/api/tasks')
        .set('x-tenant-id', TENANT_ID);

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('status', 'success');
      expect(response.body.data).toHaveProperty('tasks');
      expect(response.body.data).toHaveProperty('pagination');
      expect(response.body.data.pagination).toHaveProperty('page');
      expect(response.body.data.pagination).toHaveProperty('limit');
      expect(response.body.data.pagination).toHaveProperty('total');
      expect(response.body.data.pagination).toHaveProperty('total_pages');
    });

    it('应支持分页参数', async () => {
      const response = await request(app)
        .get('/api/tasks?page=2&limit=10')
        .set('x-tenant-id', TENANT_ID);

      expect(response.status).toBe(200);
      expect(response.body.data.pagination.page).toBe(2);
      expect(response.body.data.pagination.limit).toBe(10);
    });

    it('应支持状态筛选', async () => {
      const response = await request(app)
        .get('/api/tasks?status=ACTIVE')
        .set('x-tenant-id', TENANT_ID);

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('status', 'success');
    });

    it('应拒绝无效的状态值', async () => {
      const response = await request(app)
        .get('/api/tasks?status=INVALID_STATUS')
        .set('x-tenant-id', TENANT_ID);

      expect(response.status).toBe(400);
      expect(response.body).toHaveProperty('status', 'error');
      expect(response.body.error).toHaveProperty('code', 'ERR_400');
    });

    it('应拒绝缺少 x-tenant-id 请求头', async () => {
      const response = await request(app)
        .get('/api/tasks');

      expect(response.status).toBe(401);
      expect(response.body).toHaveProperty('status', 'error');
      expect(response.body.error).toHaveProperty('code', 'ERR_401');
    });
  });

  describe('GET /api/tasks/:id - 获取单个任务', () => {
    it('应成功返回任务详情', async () => {
      const mockPrisma = await import('../../src/db/prisma');
      vi.mocked(mockPrisma.default.testTask.findFirst).mockResolvedValueOnce({
        id: 'task-123',
        tenantId: TENANT_ID,
        name: '测试任务',
        targetUrl: 'https://example.com',
        naturalObjective: '测试目标',
        constraints: { max_steps: 50, forbidden_domains: [] },
        status: 'ACTIVE',
        createdAt: new Date(),
        updatedAt: new Date(),
      });

      const response = await request(app)
        .get('/api/tasks/task-123')
        .set('x-tenant-id', TENANT_ID);

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('status', 'success');
      expect(response.body.data).toHaveProperty('task_id', 'task-123');
      expect(response.body.data).toHaveProperty('name', '测试任务');
      expect(response.body.data).toHaveProperty('target_url');
      expect(response.body.data).toHaveProperty('natural_objective');
      expect(response.body.data).toHaveProperty('status');
      expect(response.body.data).toHaveProperty('created_at');
      expect(response.body.data).toHaveProperty('updated_at');
    });

    it('应返回 404 当任务不存在', async () => {
      const mockPrisma = await import('../../src/db/prisma');
      vi.mocked(mockPrisma.default.testTask.findFirst).mockResolvedValueOnce(null);

      const response = await request(app)
        .get('/api/tasks/non-existent-id')
        .set('x-tenant-id', TENANT_ID);

      expect(response.status).toBe(404);
      expect(response.body).toHaveProperty('status', 'error');
      expect(response.body.error).toHaveProperty('code', 'ERR_404');
      expect(response.body.error.message).toContain('找不到对应的 Task');
    });

    it('应拒绝缺少 x-tenant-id 请求头', async () => {
      const response = await request(app)
        .get('/api/tasks/task-123');

      expect(response.status).toBe(401);
      expect(response.body).toHaveProperty('status', 'error');
      expect(response.body.error).toHaveProperty('code', 'ERR_401');
    });
  });

  describe('PATCH /api/tasks/:id - 更新任务', () => {
    it('应成功更新任务名称', async () => {
      const mockPrisma = await import('../../src/db/prisma');
      vi.mocked(mockPrisma.default.testTask.findFirst).mockResolvedValueOnce({
        id: 'task-123',
        tenantId: TENANT_ID,
        name: '旧名称',
        targetUrl: 'https://example.com',
        naturalObjective: '测试目标',
        constraints: { max_steps: 50, forbidden_domains: [] },
        status: 'ACTIVE',
        createdAt: new Date(),
        updatedAt: new Date(),
      });
      vi.mocked(mockPrisma.default.testTask.update).mockResolvedValueOnce({
        id: 'task-123',
        tenantId: TENANT_ID,
        name: '新名称',
        targetUrl: 'https://example.com',
        naturalObjective: '测试目标',
        constraints: { max_steps: 50, forbidden_domains: [] },
        status: 'ACTIVE',
        createdAt: new Date(),
        updatedAt: new Date(),
      });

      const response = await request(app)
        .patch('/api/tasks/task-123')
        .set('x-tenant-id', TENANT_ID)
        .send({ name: '新名称' });

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('status', 'success');
      expect(response.body.data).toHaveProperty('name', '新名称');
    });

    it('应成功更新任务状态', async () => {
      const mockPrisma = await import('../../src/db/prisma');
      vi.mocked(mockPrisma.default.testTask.findFirst).mockResolvedValueOnce({
        id: 'task-123',
        tenantId: TENANT_ID,
        name: '测试任务',
        targetUrl: 'https://example.com',
        naturalObjective: '测试目标',
        constraints: { max_steps: 50, forbidden_domains: [] },
        status: 'ACTIVE',
        createdAt: new Date(),
        updatedAt: new Date(),
      });
      vi.mocked(mockPrisma.default.testTask.update).mockResolvedValueOnce({
        id: 'task-123',
        tenantId: TENANT_ID,
        name: '测试任务',
        targetUrl: 'https://example.com',
        naturalObjective: '测试目标',
        constraints: { max_steps: 50, forbidden_domains: [] },
        status: 'PAUSED',
        createdAt: new Date(),
        updatedAt: new Date(),
      });

      const response = await request(app)
        .patch('/api/tasks/task-123')
        .set('x-tenant-id', TENANT_ID)
        .send({ status: 'PAUSED' });

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('status', 'success');
      expect(response.body.data).toHaveProperty('status', 'PAUSED');
    });

    it('应成功更新约束条件', async () => {
      const mockPrisma = await import('../../src/db/prisma');
      vi.mocked(mockPrisma.default.testTask.findFirst).mockResolvedValueOnce({
        id: 'task-123',
        tenantId: TENANT_ID,
        name: '测试任务',
        targetUrl: 'https://example.com',
        naturalObjective: '测试目标',
        constraints: { max_steps: 50, forbidden_domains: [] },
        status: 'ACTIVE',
        createdAt: new Date(),
        updatedAt: new Date(),
      });
      vi.mocked(mockPrisma.default.testTask.update).mockResolvedValueOnce({
        id: 'task-123',
        tenantId: TENANT_ID,
        name: '测试任务',
        targetUrl: 'https://example.com',
        naturalObjective: '测试目标',
        constraints: { max_steps: 100, forbidden_domains: ['stripe.com'] },
        status: 'ACTIVE',
        createdAt: new Date(),
        updatedAt: new Date(),
      });

      const response = await request(app)
        .patch('/api/tasks/task-123')
        .set('x-tenant-id', TENANT_ID)
        .send({
          constraints: {
            max_steps: 100,
            forbidden_domains: ['stripe.com'],
          },
        });

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('status', 'success');
    });

    it('应拒绝无效的 URL 格式', async () => {
      const response = await request(app)
        .patch('/api/tasks/task-123')
        .set('x-tenant-id', TENANT_ID)
        .send({ target_url: 'invalid-url' });

      expect(response.status).toBe(400);
      expect(response.body).toHaveProperty('status', 'error');
      expect(response.body.error).toHaveProperty('code', 'ERR_400');
    });

    it('应拒绝无效的状态值', async () => {
      const response = await request(app)
        .patch('/api/tasks/task-123')
        .set('x-tenant-id', TENANT_ID)
        .send({ status: 'INVALID_STATUS' });

      expect(response.status).toBe(400);
      expect(response.body).toHaveProperty('status', 'error');
      expect(response.body.error).toHaveProperty('code', 'ERR_400');
    });

    it('应返回 404 当任务不存在', async () => {
      const mockPrisma = await import('../../src/db/prisma');
      vi.mocked(mockPrisma.default.testTask.findFirst).mockResolvedValueOnce(null);

      const response = await request(app)
        .patch('/api/tasks/non-existent-id')
        .set('x-tenant-id', TENANT_ID)
        .send({ name: '新名称' });

      expect(response.status).toBe(404);
      expect(response.body).toHaveProperty('status', 'error');
      expect(response.body.error).toHaveProperty('code', 'ERR_404');
    });

    it('应拒绝缺少 x-tenant-id 请求头', async () => {
      const response = await request(app)
        .patch('/api/tasks/task-123')
        .send({ name: '新名称' });

      expect(response.status).toBe(401);
      expect(response.body).toHaveProperty('status', 'error');
      expect(response.body.error).toHaveProperty('code', 'ERR_401');
    });
  });
});

describe('API 响应格式契约测试', () => {
  it('成功响应应包含 status: success 和 data 字段', async () => {
    const mockPrisma = await import('../../src/db/prisma');
    vi.mocked(mockPrisma.default.testTask.findMany).mockResolvedValueOnce([]);
    vi.mocked(mockPrisma.default.testTask.count).mockResolvedValueOnce(0);

    const response = await request(app)
      .get('/api/tasks')
      .set('x-tenant-id', TENANT_ID);

    expect(response.body).toMatchObject({
      status: 'success',
      data: expect.any(Object),
    });
  });

  it('错误响应应包含 status: error 和 error 字段', async () => {
    const response = await request(app)
      .get('/api/tasks')
      .set('x-tenant-id', '');

    expect(response.body).toMatchObject({
      status: 'error',
      error: expect.objectContaining({
        code: expect.any(String),
        message: expect.any(String),
      }),
    });
  });
});

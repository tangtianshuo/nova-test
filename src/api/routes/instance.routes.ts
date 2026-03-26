/**
 * 实例 API 路由
 * 提供实例的创建、查询、更新等接口
 */
import { Router, Response } from 'express';
import { z } from 'zod';
import { TenantRequest, getTenantId } from '../middleware';
import { instanceRepository } from '../../db/repositories';

const router = Router();

export const CreateInstanceSchema = z.object({
  taskId: z.string().uuid('无效的任务 ID'),
});

export const UpdateInstanceStatusSchema = z.object({
  status: z.enum(['PENDING', 'RUNNING', 'WAITING_HIL', 'COMPLETED', 'FAILED', 'TERMINATED']),
});

export const ListInstanceSchema = z.object({
  taskId: z.string().uuid().optional(),
  status: z.enum(['PENDING', 'RUNNING', 'WAITING_HIL', 'COMPLETED', 'FAILED', 'TERMINATED']).optional(),
  page: z.coerce.number().int().positive().default(1),
  pageSize: z.coerce.number().int().min(1).max(100).default(20),
});

/**
 * POST /api/instances
 * 创建新实例
 */
router.post('/', async (req: TenantRequest, res: Response) => {
  try {
    const tenantId = getTenantId(req);
    if (!tenantId) {
      res.status(401).json({ error: '租户上下文缺失' });
      return;
    }

    const validation = CreateInstanceSchema.safeParse(req.body);
    if (!validation.success) {
      res.status(400).json({
        error: '请求参数无效',
        details: validation.error.flatten(),
      });
      return;
    }

    const { taskId } = validation.data;

    const instance = await instanceRepository.create({
      tenantId,
      taskId,
      status: 'PENDING',
    });

    res.status(201).json({
      success: true,
      data: instance,
    });
  } catch (error) {
    console.error('[Instance API] 创建实例失败:', error);
    res.status(500).json({ error: '创建实例失败' });
  }
});

/**
 * GET /api/instances
 * 获取实例列表
 */
router.get('/', async (req: TenantRequest, res: Response) => {
  try {
    const tenantId = getTenantId(req);
    if (!tenantId) {
      res.status(401).json({ error: '租户上下文缺失' });
      return;
    }

    const validation = ListInstanceSchema.safeParse(req.query);
    if (!validation.success) {
      res.status(400).json({
        error: '查询参数无效',
        details: validation.error.flatten(),
      });
      return;
    }

    const { taskId, status, page, pageSize } = validation.data;

    const [items, total] = await Promise.all([
      instanceRepository.findMany({
        tenantId,
        taskId,
        status,
        skip: (page - 1) * pageSize,
        take: pageSize,
        orderBy: { createdAt: 'desc' },
      }),
      instanceRepository.count({ tenantId, taskId, status }),
    ]);

    res.json({
      success: true,
      data: {
        items,
        pagination: {
          page,
          pageSize,
          total,
          totalPages: Math.ceil(total / pageSize),
        },
      },
    });
  } catch (error) {
    console.error('[Instance API] 查询实例列表失败:', error);
    res.status(500).json({ error: '查询实例列表失败' });
  }
});

/**
 * GET /api/instances/:id
 * 获取单个实例详情
 */
router.get('/:id', async (req: TenantRequest, res: Response) => {
  try {
    const tenantId = getTenantId(req);
    if (!tenantId) {
      res.status(401).json({ error: '租户上下文缺失' });
      return;
    }

    const id = req.params.id as string;

    const instance = await instanceRepository.findById(id);
    if (!instance) {
      res.status(404).json({ error: '实例不存在' });
      return;
    }

    res.json({
      success: true,
      data: instance,
    });
  } catch (error) {
    console.error('[Instance API] 查询实例详情失败:', error);
    res.status(500).json({ error: '查询实例详情失败' });
  }
});

/**
 * PATCH /api/instances/:id/status
 * 更新实例状态
 */
router.patch('/:id/status', async (req: TenantRequest, res: Response) => {
  try {
    const tenantId = getTenantId(req);
    if (!tenantId) {
      res.status(401).json({ error: '租户上下文缺失' });
      return;
    }

    const id = req.params.id as string;

    const validation = UpdateInstanceStatusSchema.safeParse(req.body);
    if (!validation.success) {
      res.status(400).json({
        error: '请求参数无效',
        details: validation.error.flatten(),
      });
      return;
    }

    const { status } = validation.data;

    const instance = await instanceRepository.findById(id);
    if (!instance) {
      res.status(404).json({ error: '实例不存在' });
      return;
    }
    void instance;

    const updated = await instanceRepository.updateStatus(id, status);

    res.json({
      success: true,
      data: updated,
    });
  } catch (error) {
    console.error('[Instance API] 更新实例状态失败:', error);
    res.status(500).json({ error: '更新实例状态失败' });
  }
});

/**
 * DELETE /api/instances/:id
 * 终止实例
 */
router.delete('/:id', async (req: TenantRequest, res: Response) => {
  try {
    const tenantId = getTenantId(req);
    if (!tenantId) {
      res.status(401).json({ error: '租户上下文缺失' });
      return;
    }

    const id = req.params.id as string;

    const instance = await instanceRepository.findById(id);
    if (!instance) {
      res.status(404).json({ error: '实例不存在' });
      return;
    }
    void instance;

    await instanceRepository.updateStatus(id, 'TERMINATED');

    res.json({
      success: true,
      message: '实例已终止',
    });
  } catch (error) {
    console.error('[Instance API] 终止实例失败:', error);
    res.status(500).json({ error: '终止实例失败' });
  }
});

export default router;

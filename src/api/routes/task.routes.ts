/**
 * 任务 API 路由
 * 职责：实现任务的 CRUD 操作接口
 * @version 1.0.0
 */

import { Router, type Request, type Response, type NextFunction } from 'express';
import { z } from 'zod';
import {
  taskRepository,
  type CreateTaskInput,
  type UpdateTaskInput,
} from '../../db/repositories/task.repository';

const router = Router();

const CreateTaskSchema = z.object({
  tenant_id: z.string().min(1, 'tenant_id 不能为空'),
  name: z.string().min(1, '任务名称不能为空').max(255, '任务名称最多255个字符'),
  target_url: z.string().url('target_url 必须是有效的 URL'),
  natural_objective: z.string().min(1, 'natural_objective 不能为空'),
  constraints: z
    .object({
      max_steps: z.number().int().min(1).max(100).optional().default(50),
      forbidden_domains: z.array(z.string()).optional().default([]),
      timeout_seconds: z.number().int().positive().optional(),
      retry_count: z.number().int().min(0).optional(),
    })
    .optional(),
});

const UpdateTaskSchema = z.object({
  name: z.string().min(1, '任务名称不能为空').max(255, '任务名称最多255个字符').optional(),
  target_url: z.string().url('target_url 必须是有效的 URL').optional(),
  natural_objective: z.string().min(1, 'natural_objective 不能为空').optional(),
  constraints: z
    .object({
      max_steps: z.number().int().min(1).max(100).optional(),
      forbidden_domains: z.array(z.string()).optional(),
      timeout_seconds: z.number().int().positive().optional(),
      retry_count: z.number().int().min(0).optional(),
    })
    .optional(),
  status: z.enum(['ACTIVE', 'PAUSED', 'ARCHIVED']).optional(),
});

const TaskQuerySchema = z.object({
  status: z.enum(['ACTIVE', 'PAUSED', 'ARCHIVED']).optional(),
  page: z.coerce.number().int().min(1).optional().default(1),
  limit: z.coerce.number().int().min(1).max(100).optional().default(20),
});

interface ApiResponse<T> {
  status: 'success' | 'error';
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: unknown;
  };
}

interface CreateTaskResponse {
  task_id: string;
  status: string;
  created_at: string;
}

interface TaskDetailResponse {
  task_id: string;
  tenant_id: string;
  name: string;
  target_url: string;
  natural_objective: string;
  constraints: {
    max_steps: number;
    forbidden_domains: string[];
    timeout_seconds?: number;
    retry_count?: number;
  } | null;
  status: string;
  created_at: string;
  updated_at: string;
}

interface TaskListResponse {
  tasks: TaskDetailResponse[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
  };
}

function sendSuccess<T>(res: Response, data: T, statusCode = 200): void {
  const response: ApiResponse<T> = { status: 'success', data };
  res.status(statusCode).json(response);
}

function sendError(
  res: Response,
  code: string,
  message: string,
  statusCode = 400,
  details?: unknown
): void {
  const response: ApiResponse<never> = {
    status: 'error',
    error: { code, message, details },
  };
  res.status(statusCode).json(response);
}

function getTenantId(req: Request): string {
  const tenantId = req.headers['x-tenant-id'] as string;
  if (!tenantId) {
    throw new Error('缺少 x-tenant-id 请求头');
  }
  return tenantId;
}

function mapTaskToResponse(task: {
  id: string;
  tenantId: string;
  name: string;
  targetUrl: string;
  naturalObjective: string;
  constraints: unknown;
  status: string;
  createdAt: Date;
  updatedAt: Date;
}): TaskDetailResponse {
  return {
    task_id: task.id,
    tenant_id: task.tenantId,
    name: task.name,
    target_url: task.targetUrl,
    natural_objective: task.naturalObjective,
    constraints: task.constraints as TaskDetailResponse['constraints'],
    status: task.status,
    created_at: task.createdAt.toISOString(),
    updated_at: task.updatedAt.toISOString(),
  };
}

/**
 * POST /api/tasks
 * 创建新任务
 */
router.post('/', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const tenantId = getTenantId(req);

    const validationResult = CreateTaskSchema.safeParse(req.body);
    if (!validationResult.success) {
      sendError(res, 'ERR_400', '参数不符合 Schema 规范', 400, validationResult.error.issues);
      return;
    }

    const input = validationResult.data;

    const createInput: CreateTaskInput = {
      tenantId,
      name: input.name,
      targetUrl: input.target_url,
      naturalObjective: input.natural_objective,
      constraints: input.constraints ? JSON.parse(JSON.stringify(input.constraints)) : null,
    };

    const task = await taskRepository.create(createInput);

    const response: CreateTaskResponse = {
      task_id: task.id,
      status: task.status,
      created_at: task.createdAt.toISOString(),
    };

    sendSuccess(res, response, 201);
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/tasks
 * 获取任务列表
 */
router.get('/', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const tenantId = getTenantId(req);

    const queryValidation = TaskQuerySchema.safeParse(req.query);
    if (!queryValidation.success) {
      sendError(res, 'ERR_400', '查询参数不符合规范', 400, queryValidation.error.issues);
      return;
    }

    const { status, page, limit } = queryValidation.data;
    const skip = (page - 1) * limit;

    const [tasks, total] = await Promise.all([
      taskRepository.findMany({
        tenantId,
        status,
        skip,
        take: limit,
      }),
      taskRepository.count({ tenantId, status }),
    ]);

    const totalPages = Math.ceil(total / limit);

    const response: TaskListResponse = {
      tasks: tasks.map(mapTaskToResponse),
      pagination: {
        page,
        limit,
        total,
        total_pages: totalPages,
      },
    };

    sendSuccess(res, response);
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/tasks/:id
 * 获取单个任务详情
 */
router.get('/:id', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const tenantId = getTenantId(req);
    const id = req.params.id as string;

    if (!id) {
      sendError(res, 'ERR_400', '缺少任务 ID', 400);
      return;
    }

    const task = await taskRepository.findById(id, tenantId);

    if (!task) {
      sendError(res, 'ERR_404', '找不到对应的 Task', 404);
      return;
    }

    sendSuccess(res, mapTaskToResponse(task));
  } catch (error) {
    next(error);
  }
});

/**
 * PATCH /api/tasks/:id
 * 更新任务信息
 */
router.patch('/:id', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const tenantId = getTenantId(req);
    const id = req.params.id as string;

    if (!id) {
      sendError(res, 'ERR_400', '缺少任务 ID', 400);
      return;
    }

    const validationResult = UpdateTaskSchema.safeParse(req.body);
    if (!validationResult.success) {
      sendError(res, 'ERR_400', '参数不符合 Schema 规范', 400, validationResult.error.issues);
      return;
    }

    const input = validationResult.data;

    const updateInput: UpdateTaskInput = {};

    if (input.name !== undefined) updateInput.name = input.name;
    if (input.target_url !== undefined) updateInput.targetUrl = input.target_url;
    if (input.natural_objective !== undefined)
      updateInput.naturalObjective = input.natural_objective;
    if (input.constraints !== undefined)
      updateInput.constraints = JSON.parse(JSON.stringify(input.constraints));
    if (input.status !== undefined) updateInput.status = input.status;

    const updatedTask = await taskRepository.update(id, tenantId, updateInput);

    if (!updatedTask) {
      sendError(res, 'ERR_404', '找不到对应的 Task', 404);
      return;
    }

    sendSuccess(res, mapTaskToResponse(updatedTask));
  } catch (error) {
    next(error);
  }
});

/**
 * 错误处理中间件
 */
router.use((err: Error, _req: Request, res: Response, _next: NextFunction) => {
  void _next;
  console.error('Task API Error:', err);

  if (err.message.includes('x-tenant-id')) {
    sendError(res, 'ERR_401', '缺少认证信息', 401);
    return;
  }

  sendError(res, 'ERR_500', '服务器内部错误', 500);
});

export default router;

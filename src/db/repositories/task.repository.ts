import prisma from '../prisma';
import type { TestTask, Prisma } from '@prisma/client';

export interface CreateTaskInput {
  tenantId: string;
  name: string;
  targetUrl: string;
  naturalObjective: string;
  constraints?: Prisma.JsonValue;
}

export interface UpdateTaskInput {
  name?: string;
  targetUrl?: string;
  naturalObjective?: string;
  constraints?: Prisma.JsonValue;
  status?: string;
}

export interface TaskQueryOptions {
  tenantId: string;
  status?: string;
  skip?: number;
  take?: number;
}

export const taskRepository = {
  async create(data: CreateTaskInput): Promise<TestTask> {
    return prisma.testTask.create({
      data: {
        tenantId: data.tenantId,
        name: data.name,
        targetUrl: data.targetUrl,
        naturalObjective: data.naturalObjective,
        constraints: data.constraints,
      },
    });
  },

  async findById(id: string, tenantId: string): Promise<TestTask | null> {
    return prisma.testTask.findFirst({
      where: { id, tenantId },
    });
  },

  async findMany(options: TaskQueryOptions): Promise<TestTask[]> {
    const where: Prisma.TestTaskWhereInput = {
      tenantId: options.tenantId,
    };
    if (options.status) {
      where.status = options.status;
    }
    return prisma.testTask.findMany({
      where,
      skip: options.skip,
      take: options.take,
      orderBy: { updatedAt: 'desc' },
    });
  },

  async update(id: string, tenantId: string, data: UpdateTaskInput): Promise<TestTask | null> {
    const existing = await this.findById(id, tenantId);
    if (!existing) return null;
    return prisma.testTask.update({
      where: { id },
      data,
    });
  },

  async delete(id: string, tenantId: string): Promise<boolean> {
    const existing = await this.findById(id, tenantId);
    if (!existing) return false;
    await prisma.agentInstance.deleteMany({ where: { taskId: id } });
    await prisma.testTask.delete({ where: { id } });
    return true;
  },

  async count(options: TaskQueryOptions): Promise<number> {
    const where: Prisma.TestTaskWhereInput = { tenantId: options.tenantId };
    if (options.status) where.status = options.status;
    return prisma.testTask.count({ where });
  },
};

import prisma from '../prisma';
import type { AgentInstance, Prisma } from '@prisma/client';

export interface CreateInstanceInput {
  tenantId: string;
  taskId: string;
  status?: string;
}

export interface UpdateInstanceInput {
  status?: string;
  langgraphState?: Prisma.JsonValue;
  startedAt?: Date | null;
  completedAt?: Date | null;
  stepCount?: number;
  hilCount?: number;
  defectCount?: number;
  errorMessage?: string | null;
}

export interface InstanceQueryOptions {
  tenantId?: string;
  taskId?: string;
  status?: string;
  skip?: number;
  take?: number;
  orderBy?: { createdAt?: 'asc' | 'desc' };
}

export const instanceRepository = {
  async create(data: CreateInstanceInput): Promise<AgentInstance> {
    return prisma.agentInstance.create({
      data: {
        tenantId: data.tenantId,
        taskId: data.taskId,
        status: data.status || 'PENDING',
      },
    });
  },

  async findById(id: string): Promise<AgentInstance | null> {
    return prisma.agentInstance.findUnique({
      where: { id },
      include: { steps: { orderBy: { stepNumber: 'asc' } } },
    });
  },

  async findMany(options: InstanceQueryOptions): Promise<AgentInstance[]> {
    const where: Prisma.AgentInstanceWhereInput = {};
    if (options.tenantId) where.tenantId = options.tenantId;
    if (options.taskId) where.taskId = options.taskId;
    if (options.status) where.status = options.status;
    return prisma.agentInstance.findMany({
      where,
      skip: options.skip,
      take: options.take,
      orderBy: options.orderBy || { createdAt: 'desc' },
    });
  },

  async count(options: Omit<InstanceQueryOptions, 'skip' | 'take' | 'orderBy'>): Promise<number> {
    const where: Prisma.AgentInstanceWhereInput = {};
    if (options.tenantId) where.tenantId = options.tenantId;
    if (options.taskId) where.taskId = options.taskId;
    if (options.status) where.status = options.status;
    return prisma.agentInstance.count({ where });
  },

  async update(id: string, data: UpdateInstanceInput): Promise<AgentInstance | null> {
    return prisma.agentInstance.update({
      where: { id },
      data,
    });
  },

  async updateStatus(id: string, status: string): Promise<AgentInstance | null> {
    const updateData: UpdateInstanceInput = { status };
    if (status === 'RUNNING' && !(await this.findById(id))?.startedAt) {
      updateData.startedAt = new Date();
    }
    if (status === 'COMPLETED' || status === 'FAILED') {
      updateData.completedAt = new Date();
    }
    return this.update(id, updateData);
  },

  async incrementStepCount(id: string): Promise<AgentInstance | null> {
    return prisma.agentInstance.update({
      where: { id },
      data: { stepCount: { increment: 1 } },
    });
  },

  async incrementHilCount(id: string): Promise<void> {
    await prisma.agentInstance.update({
      where: { id },
      data: { hilCount: { increment: 1 } },
    });
  },

  async incrementDefectCount(id: string): Promise<void> {
    await prisma.agentInstance.update({
      where: { id },
      data: { defectCount: { increment: 1 } },
    });
  },
};

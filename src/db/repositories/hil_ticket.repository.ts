import prisma from '../prisma';
import type { HilTicket, WorkerCheckpoint, Prisma } from '@prisma/client';

export interface CreateHilTicketInput {
  tenantId: string;
  instanceId: string;
  stepNo: number;
  reason: string;
  riskLevel?: string;
  plannedAction?: Prisma.JsonValue;
  screenshotUrl?: string;
  overlay?: Prisma.JsonValue;
  expiresAt?: Date;
}

export interface UpdateHilTicketInput {
  status?: string;
  decision?: string;
  modifiedAction?: Prisma.JsonValue;
  decidedBy?: string;
  decidedAt?: Date;
}

export interface CreateWorkerCheckpointInput {
  instanceId: string;
  ticketId?: string;
  currentNode: string;
  stepCount: number;
  executionState: Prisma.JsonValue;
  plannedAction?: Prisma.JsonValue;
  screenshotData?: string;
  workerId?: string;
  interruptedReason?: string;
  hilTriggered?: boolean;
  lastError?: string;
  retryCount?: number;
  metadata?: Prisma.JsonValue;
}

export interface UpdateWorkerCheckpointInput {
  status?: string;
  currentNode?: string;
  stepCount?: number;
  executionState?: Prisma.JsonValue;
  plannedAction?: Prisma.JsonValue;
  screenshotData?: string;
  workerId?: string;
  interruptedReason?: string;
  hilTriggered?: boolean;
  lastError?: string;
  retryCount?: number;
  version?: number;
  metadata?: Prisma.JsonValue;
}

export const hilTicketRepository = {
  async create(data: CreateHilTicketInput): Promise<HilTicket> {
    return prisma.hilTicket.create({
      data: {
        tenantId: data.tenantId,
        instanceId: data.instanceId,
        stepNo: data.stepNo,
        reason: data.reason,
        riskLevel: data.riskLevel ?? 'MEDIUM',
        plannedAction: data.plannedAction,
        screenshotUrl: data.screenshotUrl,
        overlay: data.overlay ?? {},
        expiresAt: data.expiresAt,
      },
    });
  },

  async findById(id: string): Promise<HilTicket | null> {
    return prisma.hilTicket.findUnique({ where: { id } });
  },

  async findByInstanceId(instanceId: string): Promise<HilTicket | null> {
    return prisma.hilTicket.findUnique({ where: { instanceId } });
  },

  async findWaiting(): Promise<HilTicket[]> {
    return prisma.hilTicket.findMany({
      where: { status: 'WAITING' },
      orderBy: { createdAt: 'asc' },
    });
  },

  async update(id: string, data: UpdateHilTicketInput): Promise<HilTicket | null> {
    return prisma.hilTicket.update({
      where: { id },
      data,
    });
  },

  async resolve(
    id: string,
    decision: string,
    decidedBy: string,
    modifiedAction?: Prisma.JsonValue
  ): Promise<HilTicket | null> {
    const statusMap: Record<string, string> = {
      approve: 'APPROVED',
      reject: 'REJECTED',
      modify: 'MODIFIED',
    };
    return this.update(id, {
      status: statusMap[decision] ?? decision,
      decision,
      decidedBy,
      decidedAt: new Date(),
      modifiedAction,
    });
  },

  async countByStatus(status: string): Promise<number> {
    return prisma.hilTicket.count({ where: { status } });
  },
};

export const workerCheckpointRepository = {
  async create(data: CreateWorkerCheckpointInput): Promise<WorkerCheckpoint> {
    return prisma.workerCheckpoint.create({
      data: {
        instanceId: data.instanceId,
        ticketId: data.ticketId,
        currentNode: data.currentNode,
        stepCount: data.stepCount,
        executionState: data.executionState,
        plannedAction: data.plannedAction,
        screenshotData: data.screenshotData,
        workerId: data.workerId,
        interruptedReason: data.interruptedReason,
        hilTriggered: data.hilTriggered ?? false,
        lastError: data.lastError,
        retryCount: data.retryCount ?? 0,
        metadata: data.metadata ?? {},
      },
    });
  },

  async findByInstanceId(instanceId: string): Promise<WorkerCheckpoint | null> {
    return prisma.workerCheckpoint.findFirst({
      where: { instanceId },
      orderBy: { version: 'desc' },
    });
  },

  async findPendingCheckpoints(limit: number = 100): Promise<WorkerCheckpoint[]> {
    return prisma.workerCheckpoint.findMany({
      where: { status: 'INTERRUPTED' },
      orderBy: { interruptedAt: 'asc' },
      take: limit,
    });
  },

  async update(
    id: string,
    data: UpdateWorkerCheckpointInput
  ): Promise<WorkerCheckpoint | null> {
    return prisma.workerCheckpoint.update({
      where: { id },
      data,
    });
  },

  async markAsRecovered(id: string): Promise<WorkerCheckpoint | null> {
    return prisma.workerCheckpoint.update({
      where: { id },
      data: {
        status: 'RECOVERED',
        updatedAt: new Date(),
      },
    });
  },

  async markAsFailed(id: string, error: string): Promise<WorkerCheckpoint | null> {
    return prisma.workerCheckpoint.update({
      where: { id },
      data: {
        status: 'FAILED',
        lastError: error,
        updatedAt: new Date(),
      },
    });
  },

  async updateWithOptimisticLock(
    id: string,
    data: UpdateWorkerCheckpointInput,
    expectedVersion: number
  ): Promise<WorkerCheckpoint | null> {
    return prisma.workerCheckpoint.updateMany({
      where: {
        id,
        version: expectedVersion,
      },
      data: {
        ...data,
        version: expectedVersion + 1,
        updatedAt: new Date(),
      },
    }).then(async (result) => {
      if (result.count === 0) {
        return null;
      }
      return prisma.workerCheckpoint.findUnique({ where: { id } });
    });
  },

  async cleanupOldCheckpoints(daysOld: number = 7): Promise<number> {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - daysOld);

    const result = await prisma.workerCheckpoint.deleteMany({
      where: {
        status: { in: ['RECOVERED', 'FAILED'] },
        updatedAt: { lt: cutoffDate },
      },
    });

    return result.count;
  },
};

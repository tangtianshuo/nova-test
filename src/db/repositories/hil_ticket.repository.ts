import prisma from '../prisma';
import type { HilTicket, Prisma } from '@prisma/client';

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

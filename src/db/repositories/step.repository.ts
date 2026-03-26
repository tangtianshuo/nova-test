import prisma from '../prisma';
import type { TestStep, Prisma } from '@prisma/client';

export interface CreateStepInput {
  instanceId: string;
  stepNumber: number;
  nodeName: string;
  screenshotUrl?: string;
  thought?: string;
  actionType?: string;
  actionTarget?: Prisma.JsonValue;
  actionParams?: Prisma.JsonValue;
  confidence?: number;
  expectedResult?: string;
  isSuccess?: boolean;
  isDefect?: boolean;
  verificationMsg?: string;
  durationMs?: number;
}

export const stepRepository = {
  async create(data: CreateStepInput): Promise<TestStep> {
    return prisma.testStep.create({
      data: {
        instanceId: data.instanceId,
        stepNumber: data.stepNumber,
        nodeName: data.nodeName,
        screenshotUrl: data.screenshotUrl,
        thought: data.thought,
        actionType: data.actionType,
        actionTarget: data.actionTarget,
        actionParams: data.actionParams,
        confidence: data.confidence,
        expectedResult: data.expectedResult,
        isSuccess: data.isSuccess,
        isDefect: data.isDefect,
        verificationMsg: data.verificationMsg,
        durationMs: data.durationMs ?? 0,
      },
    });
  },

  async findById(id: string): Promise<TestStep | null> {
    return prisma.testStep.findUnique({ where: { id } });
  },

  async findByInstance(instanceId: string): Promise<TestStep[]> {
    return prisma.testStep.findMany({
      where: { instanceId },
      orderBy: { stepNumber: 'asc' },
    });
  },

  async findByInstanceAndNumber(instanceId: string, stepNumber: number): Promise<TestStep | null> {
    return prisma.testStep.findFirst({
      where: { instanceId, stepNumber },
    });
  },

  async updateVerification(
    id: string,
    data: { isSuccess: boolean; isDefect: boolean; verificationMsg: string }
  ): Promise<TestStep | null> {
    return prisma.testStep.update({
      where: { id },
      data: {
        isSuccess: data.isSuccess,
        isDefect: data.isDefect,
        verificationMsg: data.verificationMsg,
      },
    });
  },

  async countByInstance(instanceId: string): Promise<number> {
    return prisma.testStep.count({ where: { instanceId } });
  },
};

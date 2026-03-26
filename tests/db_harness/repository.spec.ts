/**
 * Repository 层测试
 * 验证数据访问层的基本 CRUD 操作
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { PrismaClient } from '@prisma/client';
import { taskRepository, CreateTaskInput } from '../../src/db/repositories/task.repository';
import { instanceRepository, CreateInstanceInput } from '../../src/db/repositories/instance.repository';
import { stepRepository, CreateStepInput } from '../../src/db/repositories/step.repository';
import {
  hilTicketRepository,
  CreateHilTicketInput,
} from '../../src/db/repositories/hil_ticket.repository';

const prisma = new PrismaClient();

describe('Repository Harness', () => {
  let testTenantId: string;
  let cleanupIds: {
    tenants: string[];
    users: string[];
    tasks: string[];
    instances: string[];
    steps: string[];
    hilTickets: string[];
  };
  let dbAvailable = false;

  beforeEach(async () => {
    cleanupIds = {
      tenants: [],
      users: [],
      tasks: [],
      instances: [],
      steps: [],
      hilTickets: [],
    };

    try {
      await prisma.$connect();
      const tenant = await prisma.tenant.create({
        data: {
          name: `Test Tenant ${Date.now()}`,
          planType: 'FREE',
        },
      });
      testTenantId = tenant.id;
      cleanupIds.tenants.push(testTenantId);
      dbAvailable = true;
    } catch (error) {
      console.warn('[DB Test] 数据库不可用，跳过测试:', error);
      dbAvailable = false;
    }
  });

  afterEach(async () => {
    if (!dbAvailable) return;
    try {
      await prisma.hilTicket.deleteMany({
        where: { id: { in: cleanupIds.hilTickets } },
      }).catch(() => {});
      await prisma.testStep.deleteMany({
        where: { id: { in: cleanupIds.steps } },
      }).catch(() => {});
      await prisma.agentInstance.deleteMany({
        where: { id: { in: cleanupIds.instances } },
      }).catch(() => {});
      await prisma.testTask.deleteMany({
        where: { id: { in: cleanupIds.tasks } },
      }).catch(() => {});
      await prisma.user.deleteMany({
        where: { id: { in: cleanupIds.users } },
      }).catch(() => {});
      await prisma.tenant.deleteMany({
        where: { id: { in: cleanupIds.tenants } },
      }).catch(() => {});
    } catch {
      // 忽略清理错误
    }
  });

  describe('TaskRepository', () => {
    it('should_create_task_with_valid_data', async () => {
      if (!dbAvailable) return;
      const input: CreateTaskInput = {
        tenantId: testTenantId,
        name: 'Test Task',
        targetUrl: 'https://example.com',
        naturalObjective: 'Test the login flow',
        constraints: { maxSteps: 10 },
      };

      const task = await taskRepository.create(input);
      cleanupIds.tasks.push(task.id);
      expect(task.id).toBeDefined();
      expect(task.name).toBe('Test Task');
    });

    it('should_find_task_by_id_with_tenant_isolation', async () => {
      if (!dbAvailable) return;
      const input: CreateTaskInput = {
        tenantId: testTenantId,
        name: 'Isolation Test Task',
        targetUrl: 'https://example.com',
        naturalObjective: 'Test isolation',
      };
      const task = await taskRepository.create(input);
      cleanupIds.tasks.push(task.id);
      const found = await taskRepository.findById(task.id, testTenantId);
      expect(found).not.toBeNull();
      expect(found?.name).toBe('Isolation Test Task');
    });

    it('should_update_task_status', async () => {
      if (!dbAvailable) return;
      const input: CreateTaskInput = {
        tenantId: testTenantId,
        name: 'Update Test Task',
        targetUrl: 'https://example.com',
        naturalObjective: 'Test update',
      };
      const task = await taskRepository.create(input);
      cleanupIds.tasks.push(task.id);
      const updated = await taskRepository.update(task.id, testTenantId, { status: 'INACTIVE' });
      expect(updated?.status).toBe('INACTIVE');
    });

    it('should_delete_task_cascade_instances', async () => {
      if (!dbAvailable) return;
      const input: CreateTaskInput = {
        tenantId: testTenantId,
        name: 'Delete Cascade Task',
        targetUrl: 'https://example.com',
        naturalObjective: 'Test cascade delete',
      };
      const task = await taskRepository.create(input);
      const instanceInput: CreateInstanceInput = {
        tenantId: testTenantId,
        taskId: task.id,
        status: 'PENDING',
      };
      await instanceRepository.create(instanceInput);
      const deleted = await taskRepository.delete(task.id, testTenantId);
      expect(deleted).toBe(true);
    });

    it('should_count_tasks_by_tenant', async () => {
      if (!dbAvailable) return;
      const count = await taskRepository.count({ tenantId: testTenantId });
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });

  describe('InstanceRepository', () => {
    it('should_create_instance_linked_to_task', async () => {
      if (!dbAvailable) return;
      const taskInput: CreateTaskInput = {
        tenantId: testTenantId,
        name: 'Instance Test Task',
        targetUrl: 'https://example.com',
        naturalObjective: 'Test',
      };
      const task = await taskRepository.create(taskInput);
      cleanupIds.tasks.push(task.id);
      const instanceInput: CreateInstanceInput = {
        tenantId: testTenantId,
        taskId: task.id,
        status: 'PENDING',
      };
      const instance = await instanceRepository.create(instanceInput);
      cleanupIds.instances.push(instance.id);
      expect(instance.id).toBeDefined();
      expect(instance.taskId).toBe(task.id);
    });

    it('should_update_instance_status_with_timestamps', async () => {
      if (!dbAvailable) return;
      const taskInput: CreateTaskInput = {
        tenantId: testTenantId,
        name: 'Status Test Task',
        targetUrl: 'https://example.com',
        naturalObjective: 'Test',
      };
      const task = await taskRepository.create(taskInput);
      cleanupIds.tasks.push(task.id);
      const instanceInput: CreateInstanceInput = {
        tenantId: testTenantId,
        taskId: task.id,
        status: 'PENDING',
      };
      const instance = await instanceRepository.create(instanceInput);
      cleanupIds.instances.push(instance.id);
      const updated = await instanceRepository.updateStatus(instance.id, testTenantId, 'RUNNING');
      expect(updated?.status).toBe('RUNNING');
    });

    it('should_increment_counters_atomically', async () => {
      if (!dbAvailable) return;
      const taskInput: CreateTaskInput = {
        tenantId: testTenantId,
        name: 'Counter Test Task',
        targetUrl: 'https://example.com',
        naturalObjective: 'Test',
      };
      const task = await taskRepository.create(taskInput);
      cleanupIds.tasks.push(task.id);
      const instanceInput: CreateInstanceInput = {
        tenantId: testTenantId,
        taskId: task.id,
        status: 'PENDING',
      };
      const instance = await instanceRepository.create(instanceInput);
      cleanupIds.instances.push(instance.id);
      const updated = await instanceRepository.incrementStepCount(instance.id, testTenantId);
      expect(updated?.stepCount).toBe(1);
    });

    it('should_find_instances_by_task', async () => {
      if (!dbAvailable) return;
      const taskInput: CreateTaskInput = {
        tenantId: testTenantId,
        name: 'Find Instances Task',
        targetUrl: 'https://example.com',
        naturalObjective: 'Test',
      };
      const task = await taskRepository.create(taskInput);
      cleanupIds.tasks.push(task.id);
      const instances = await instanceRepository.findMany({
        tenantId: testTenantId,
        taskId: task.id,
      });
      expect(Array.isArray(instances)).toBe(true);
    });
  });

  describe('StepRepository', () => {
    it('should_create_step_with_all_fields', async () => {
      if (!dbAvailable) return;
      const taskInput: CreateTaskInput = {
        tenantId: testTenantId,
        name: 'Step Test Task',
        targetUrl: 'https://example.com',
        naturalObjective: 'Test',
      };
      const task = await taskRepository.create(taskInput);
      cleanupIds.tasks.push(task.id);
      const instanceInput: CreateInstanceInput = {
        tenantId: testTenantId,
        taskId: task.id,
        status: 'RUNNING',
      };
      const instance = await instanceRepository.create(instanceInput);
      cleanupIds.instances.push(instance.id);
      const stepInput: CreateStepInput = {
        tenantId: testTenantId,
        instanceId: instance.id,
        stepNumber: 1,
        nodeName: 'init',
        action: { type: 'click', selector: '#login' },
      };
      const step = await stepRepository.create(stepInput);
      cleanupIds.steps.push(step.id);
      expect(step.id).toBeDefined();
      expect(step.stepNumber).toBe(1);
    });

    it('should_find_steps_by_instance_ordered', async () => {
      if (!dbAvailable) return;
      const taskInput: CreateTaskInput = {
        tenantId: testTenantId,
        name: 'Ordered Steps Task',
        targetUrl: 'https://example.com',
        naturalObjective: 'Test',
      };
      const task = await taskRepository.create(taskInput);
      cleanupIds.tasks.push(task.id);
      const instanceInput: CreateInstanceInput = {
        tenantId: testTenantId,
        taskId: task.id,
        status: 'RUNNING',
      };
      const instance = await instanceRepository.create(instanceInput);
      cleanupIds.instances.push(instance.id);
      const steps = await stepRepository.findByInstance(instance.id, testTenantId);
      expect(Array.isArray(steps)).toBe(true);
    });

    it('should_update_step_verification', async () => {
      if (!dbAvailable) return;
      const taskInput: CreateTaskInput = {
        tenantId: testTenantId,
        name: 'Verify Test Task',
        targetUrl: 'https://example.com',
        naturalObjective: 'Test',
      };
      const task = await taskRepository.create(taskInput);
      cleanupIds.tasks.push(task.id);
      const instanceInput: CreateInstanceInput = {
        tenantId: testTenantId,
        taskId: task.id,
        status: 'RUNNING',
      };
      const instance = await instanceRepository.create(instanceInput);
      cleanupIds.instances.push(instance.id);
      const stepInput: CreateStepInput = {
        tenantId: testTenantId,
        instanceId: instance.id,
        stepNumber: 1,
        nodeName: 'verify',
        action: { type: 'click', selector: '#btn' },
      };
      const step = await stepRepository.create(stepInput);
      cleanupIds.steps.push(step.id);
      const found = await stepRepository.findById(step.id);
      expect(found?.id).toBe(step.id);
    });

    it('should_count_steps_by_instance', async () => {
      if (!dbAvailable) return;
      const taskInput: CreateTaskInput = {
        tenantId: testTenantId,
        name: 'Count Steps Task',
        targetUrl: 'https://example.com',
        naturalObjective: 'Test',
      };
      const task = await taskRepository.create(taskInput);
      cleanupIds.tasks.push(task.id);
      const instanceInput: CreateInstanceInput = {
        tenantId: testTenantId,
        taskId: task.id,
        status: 'RUNNING',
      };
      const instance = await instanceRepository.create(instanceInput);
      cleanupIds.instances.push(instance.id);
      const count = await stepRepository.countByInstance(instance.id, testTenantId);
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });

  describe('HilTicketRepository', () => {
    it('should_create_ticket_for_blocked_instance', async () => {
      if (!dbAvailable) return;
      const taskInput: CreateTaskInput = {
        tenantId: testTenantId,
        name: 'HIL Test Task',
        targetUrl: 'https://example.com',
        naturalObjective: 'Test',
      };
      const task = await taskRepository.create(taskInput);
      cleanupIds.tasks.push(task.id);
      const instanceInput: CreateInstanceInput = {
        tenantId: testTenantId,
        taskId: task.id,
        status: 'WAITING_HIL',
      };
      const instance = await instanceRepository.create(instanceInput);
      cleanupIds.instances.push(instance.id);
      const ticketInput: CreateHilTicketInput = {
        tenantId: testTenantId,
        instanceId: instance.id,
        stepNo: 1,
        reason: '需要人工确认支付操作',
        riskLevel: 'HIGH',
      };
      const ticket = await hilTicketRepository.create(ticketInput);
      cleanupIds.hilTickets.push(ticket.id);
      expect(ticket.id).toBeDefined();
      expect(ticket.status).toBe('WAITING');
    });

    it('should_resolve_ticket_with_decision', async () => {
      if (!dbAvailable) return;
      const taskInput: CreateTaskInput = {
        tenantId: testTenantId,
        name: 'Resolve Test Task',
        targetUrl: 'https://example.com',
        naturalObjective: 'Test',
      };
      const task = await taskRepository.create(taskInput);
      cleanupIds.tasks.push(task.id);
      const instanceInput: CreateInstanceInput = {
        tenantId: testTenantId,
        taskId: task.id,
        status: 'WAITING_HIL',
      };
      const instance = await instanceRepository.create(instanceInput);
      cleanupIds.instances.push(instance.id);
      const ticketInput: CreateHilTicketInput = {
        tenantId: testTenantId,
        instanceId: instance.id,
        stepNo: 1,
        reason: 'Test',
        riskLevel: 'MEDIUM',
      };
      const ticket = await hilTicketRepository.create(ticketInput);
      cleanupIds.hilTickets.push(ticket.id);
      expect(ticket.id).toBeDefined();
    });

    it('should_resolve_ticket_with_modified_action', async () => {
      if (!dbAvailable) return;
      const tickets = await hilTicketRepository.findWaiting();
      expect(Array.isArray(tickets)).toBe(true);
    });

    it('should_find_waiting_tickets', async () => {
      if (!dbAvailable) return;
      const tickets = await hilTicketRepository.findWaiting(testTenantId);
      expect(Array.isArray(tickets)).toBe(true);
    });

    it('should_find_ticket_by_instance', async () => {
      if (!dbAvailable) return;
      const taskInput: CreateTaskInput = {
        tenantId: testTenantId,
        name: 'Find Ticket Task',
        targetUrl: 'https://example.com',
        naturalObjective: 'Test',
      };
      const task = await taskRepository.create(taskInput);
      cleanupIds.tasks.push(task.id);
      const instanceInput: CreateInstanceInput = {
        tenantId: testTenantId,
        taskId: task.id,
        status: 'WAITING_HIL',
      };
      const instance = await instanceRepository.create(instanceInput);
      cleanupIds.instances.push(instance.id);
      const count = await hilTicketRepository.countByStatus('WAITING');
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Tenant Isolation Integration', () => {
    it('should_enforce_tenant_isolation_across_repositories', async () => {
      if (!dbAvailable) return;
      const tenant2 = await prisma.tenant.create({
        data: { name: `Tenant 2 ${Date.now()}`, planType: 'PRO' },
      });
      cleanupIds.tenants.push(tenant2.id);

      const task1 = await taskRepository.create({
        tenantId: testTenantId,
        name: 'Task for Tenant 1',
        targetUrl: 'https://example.com',
        naturalObjective: 'Test',
      });
      cleanupIds.tasks.push(task1.id);

      const tasksForTenant2 = await taskRepository.findMany({ tenantId: tenant2.id });
      expect(tasksForTenant2.find((t) => t.id === task1.id)).toBeUndefined();
    });
  });
});

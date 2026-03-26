/**
 * RBAC 权限控制模块
 * 实现基于角色的访问控制
 */
import { Request, Response, NextFunction } from 'express';

export enum Role {
  ADMIN = 'ADMIN',
  OPERATOR = 'OPERATOR',
  VIEWER = 'VIEWER',
  AUDITOR = 'AUDITOR',
}

export enum Permission {
  TASK_CREATE = 'task:create',
  TASK_READ = 'task:read',
  TASK_UPDATE = 'task:update',
  TASK_DELETE = 'task:delete',
  INSTANCE_CREATE = 'instance:create',
  INSTANCE_READ = 'instance:read',
  INSTANCE_UPDATE = 'instance:update',
  INSTANCE_TERMINATE = 'instance:terminate',
  HIL_APPROVE = 'hil:approve',
  HIL_REJECT = 'hil:reject',
  REPORT_VIEW = 'report:view',
  REPORT_EXPORT = 'report:export',
  USER_MANAGE = 'user:manage',
  TENANT_SETTINGS = 'tenant:settings',
}

const ROLE_PERMISSIONS: Record<Role, Permission[]> = {
  [Role.ADMIN]: Object.values(Permission),
  [Role.OPERATOR]: [
    Permission.TASK_CREATE,
    Permission.TASK_READ,
    Permission.TASK_UPDATE,
    Permission.INSTANCE_CREATE,
    Permission.INSTANCE_READ,
    Permission.INSTANCE_UPDATE,
    Permission.INSTANCE_TERMINATE,
    Permission.HIL_APPROVE,
    Permission.HIL_REJECT,
    Permission.REPORT_VIEW,
  ],
  [Role.VIEWER]: [
    Permission.TASK_READ,
    Permission.INSTANCE_READ,
    Permission.REPORT_VIEW,
  ],
  [Role.AUDITOR]: [
    Permission.TASK_READ,
    Permission.INSTANCE_READ,
    Permission.REPORT_VIEW,
    Permission.REPORT_EXPORT,
  ],
};

export function hasPermission(role: Role, permission: Permission): boolean {
  return ROLE_PERMISSIONS[role]?.includes(permission) ?? false;
}

export function hasAnyPermission(role: Role, permissions: Permission[]): boolean {
  return permissions.some((p) => hasPermission(role, p));
}

export function hasAllPermissions(role: Role, permissions: Permission[]): boolean {
  return permissions.every((p) => hasPermission(role, p));
}

export interface AuthenticatedRequest extends Request {
  user: {
    userId: string;
    email: string;
    role: Role;
    tenantId: string;
  };
}

export function requireRole(...roles: Role[]) {
  return (req: AuthenticatedRequest, res: Response, next: NextFunction): void => {
    const user = req.user;

    if (!user) {
      res.status(401).json({ error: '未认证' });
      return;
    }

    if (!roles.includes(user.role)) {
      res.status(403).json({
        error: '权限不足',
        required: roles,
        current: user.role,
      });
      return;
    }

    next();
  };
}

export function requirePermission(...permissions: Permission[]) {
  return (req: AuthenticatedRequest, res: Response, next: NextFunction): void => {
    const user = req.user;

    if (!user) {
      res.status(401).json({ error: '未认证' });
      return;
    }

    const hasRequired = permissions.every((p) =>
      hasPermission(user.role, p)
    );

    if (!hasRequired) {
      res.status(403).json({
        error: '权限不足',
        required: permissions,
        current: user.role,
      });
      return;
    }

    next();
  };
}

export function requirePermissionAny(...permissions: Permission[]) {
  return (req: AuthenticatedRequest, res: Response, next: NextFunction): void => {
    const user = req.user;

    if (!user) {
      res.status(401).json({ error: '未认证' });
      return;
    }

    const hasAny = permissions.some((p) =>
      hasPermission(user.role, p)
    );

    if (!hasAny) {
      res.status(403).json({
        error: '权限不足',
        required: permissions,
        current: user.role,
      });
      return;
    }

    next();
  };
}

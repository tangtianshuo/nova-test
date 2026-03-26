/**
 * 租户上下文中间件
 * 从 JWT 中提取租户 ID 并注入到请求上下文
 */
import { Request, Response, NextFunction } from 'express';
import { AuthenticatedRequest, Role } from '../auth/rbac';

export interface TenantContext {
  tenantId: string;
  userId: string;
  role: Role;
}

export interface TenantRequest extends Request {
  tenant?: TenantContext;
}

export function extractTenant(
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction
): void {
  const user = req.user;

  if (user) {
    (req as TenantRequest).tenant = {
      tenantId: user.tenantId,
      userId: user.userId,
      role: user.role,
    };
  }

  next();
}

export function requireTenant(
  req: TenantRequest,
  res: Response,
  next: NextFunction
): void {
  if (!req.tenant) {
    res.status(401).json({ error: '租户上下文缺失' });
    return;
  }

  if (!req.tenant.tenantId) {
    res.status(400).json({ error: '无效的租户 ID' });
    return;
  }

  next();
}

export function getTenantId(req: TenantRequest): string | undefined {
  return req.tenant?.tenantId;
}

export function getUserId(req: TenantRequest): string | undefined {
  return req.tenant?.userId;
}

/**
 * JWT 认证模块
 * 提供用户认证、令牌生成与验证、密码哈希等功能
 * @version 1.0.0
 */

import jwt, { SignOptions } from 'jsonwebtoken';
import bcrypt from 'bcryptjs';
import type { Request, Response, NextFunction, RequestHandler } from 'express';
import { prisma } from '../../db/prisma';
import type { StringValue } from 'ms';

/**
 * JWT 配置接口
 */
export interface JwtConfig {
  secret: string;
  expiresIn: StringValue | number;
  issuer?: string;
  audience?: string;
}

/**
 * JWT 载荷接口
 */
export interface JwtPayload {
  userId: string;
  tenantId: string;
  email: string;
  role: string;
  iat?: number;
  exp?: number;
  iss?: string;
  aud?: string;
}

/**
 * 登录请求接口
 */
export interface LoginRequest {
  email: string;
  password: string;
}

/**
 * 登录响应接口
 */
export interface LoginResponse {
  success: boolean;
  token?: string;
  user?: {
    id: string;
    email: string;
    role: string;
    tenantId: string;
  };
  error?: string;
}

/**
 * 认证错误响应接口
 */
export interface AuthErrorResponse {
  error: string;
  code: string;
  statusCode: number;
}

/**
 * 获取 JWT 配置
 * @returns JWT 配置对象
 */
export function getJwtConfig(): JwtConfig {
  return {
    secret: process.env.JWT_SECRET || 'default-secret-change-in-production',
    expiresIn: (process.env.JWT_EXPIRES_IN || '24h') as StringValue,
    issuer: process.env.JWT_ISSUER || 'nova-test-api',
    audience: process.env.JWT_AUDIENCE || 'nova-test-users',
  };
}

/**
 * 生成 JWT 令牌
 * @param payload 令牌载荷
 * @returns 生成的 JWT 令牌字符串
 */
export function generateToken(payload: JwtPayload): string {
  const config = getJwtConfig();
  
  const tokenPayload = {
    userId: payload.userId,
    tenantId: payload.tenantId,
    email: payload.email,
    role: payload.role,
  };

  const signOptions: SignOptions = {
    expiresIn: config.expiresIn,
    issuer: config.issuer,
    audience: config.audience,
  };

  return jwt.sign(tokenPayload, config.secret, signOptions);
}

/**
 * 验证 JWT 令牌
 * @param token 要验证的令牌字符串
 * @returns 解码后的令牌载荷
 * @throws 如果令牌无效或已过期
 */
export function verifyToken(token: string): JwtPayload {
  const config = getJwtConfig();
  
  try {
    const decoded = jwt.verify(token, config.secret, {
      issuer: config.issuer,
      audience: config.audience,
    }) as JwtPayload;
    
    return decoded;
  } catch (error) {
    if (error instanceof jwt.TokenExpiredError) {
      throw new Error('令牌已过期');
    } else if (error instanceof jwt.JsonWebTokenError) {
      throw new Error('令牌无效');
    } else if (error instanceof jwt.NotBeforeError) {
      throw new Error('令牌尚未生效');
    }
    throw new Error('令牌验证失败');
  }
}

/**
 * 哈希密码
 * @param password 明文密码
 * @param saltRounds 盐轮次（默认 12）
 * @returns 哈希后的密码
 */
export async function hashPassword(password: string, saltRounds: number = 12): Promise<string> {
  return bcrypt.hash(password, saltRounds);
}

/**
 * 比较密码
 * @param password 明文密码
 * @param hashedPassword 哈希后的密码
 * @returns 密码是否匹配
 */
export async function comparePassword(password: string, hashedPassword: string): Promise<boolean> {
  return bcrypt.compare(password, hashedPassword);
}

/**
 * 认证中间件类型
 */
export type AuthMiddleware = RequestHandler;

/**
 * 扩展 Express Request 接口
 */
declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace Express {
    interface Request {
      user?: JwtPayload;
    }
  }
}

/**
 * 创建认证中间件
 * @param options 可选配置项
 * @returns Express 中间件函数
 */
export function createAuthMiddleware(options?: {
  optional?: boolean;
  requiredRoles?: string[];
}): AuthMiddleware {
  return async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    const authHeader = req.headers.authorization;

    if (!authHeader) {
      if (options?.optional) {
        return next();
      }
      
      const errorResponse: AuthErrorResponse = {
        error: '未提供认证令牌',
        code: 'AUTH_TOKEN_MISSING',
        statusCode: 401,
      };
      res.status(401).json(errorResponse);
      return;
    }

    const parts = authHeader.split(' ');
    if (parts.length !== 2 || parts[0] !== 'Bearer') {
      const errorResponse: AuthErrorResponse = {
        error: '认证头格式无效，应为: Bearer <token>',
        code: 'AUTH_HEADER_INVALID',
        statusCode: 401,
      };
      res.status(401).json(errorResponse);
      return;
    }

    const token = parts[1];

    try {
      const decoded = verifyToken(token);
      
      if (options?.requiredRoles && options.requiredRoles.length > 0) {
        if (!options.requiredRoles.includes(decoded.role)) {
          const errorResponse: AuthErrorResponse = {
            error: '权限不足',
            code: 'AUTH_INSUFFICIENT_PERMISSIONS',
            statusCode: 403,
          };
          res.status(403).json(errorResponse);
          return;
        }
      }

      (req as Express.Request & { user?: JwtPayload }).user = decoded;
      next();
    } catch (error) {
      const errorResponse: AuthErrorResponse = {
        error: error instanceof Error ? error.message : '令牌验证失败',
        code: 'AUTH_TOKEN_INVALID',
        statusCode: 401,
      };
      res.status(401).json(errorResponse);
    }
  };
}

/**
 * 默认认证中间件实例
 */
export const authMiddleware: AuthMiddleware = createAuthMiddleware();

/**
 * 处理登录请求
 * @param req Express 请求对象
 * @param res Express 响应对象
 */
export async function handleLogin(req: Request, res: Response): Promise<void> {
  try {
    const { email, password } = req.body as LoginRequest;

    if (!email || !password) {
      const response: LoginResponse = {
        success: false,
        error: '邮箱和密码为必填项',
      };
      res.status(400).json(response);
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      const response: LoginResponse = {
        success: false,
        error: '邮箱格式无效',
      };
      res.status(400).json(response);
      return;
    }

    const user = await prisma.user.findUnique({
      where: { email },
      include: { tenant: true },
    });

    if (!user) {
      const response: LoginResponse = {
        success: false,
        error: '用户不存在或密码错误',
      };
      res.status(401).json(response);
      return;
    }

    const isPasswordValid = await comparePassword(password, user.passwordHash);

    if (!isPasswordValid) {
      const response: LoginResponse = {
        success: false,
        error: '用户不存在或密码错误',
      };
      res.status(401).json(response);
      return;
    }

    const token = generateToken({
      userId: user.id,
      tenantId: user.tenantId,
      email: user.email,
      role: user.role,
    });

    const response: LoginResponse = {
      success: true,
      token,
      user: {
        id: user.id,
        email: user.email,
        role: user.role,
        tenantId: user.tenantId,
      },
    };

    res.status(200).json(response);
  } catch (error) {
    console.error('登录处理错误:', error);
    const response: LoginResponse = {
      success: false,
      error: '服务器内部错误',
    };
    res.status(500).json(response);
  }
}

/**
 * 获取当前用户信息
 * @param req Express 请求对象
 * @param res Express 响应对象
 */
export function getCurrentUser(req: Request, res: Response): void {
  const user = (req as Express.Request & { user?: JwtPayload }).user;

  if (!user) {
    res.status(401).json({
      error: '未认证',
      code: 'AUTH_NOT_AUTHENTICATED',
    });
    return;
  }

  res.status(200).json({
    success: true,
    user: {
      id: user.userId,
      email: user.email,
      role: user.role,
      tenantId: user.tenantId,
    },
  });
}

/**
 * 登出处理（可选实现，主要用于清除客户端令牌）
 * @param req Express 请求对象
 * @param res Express 响应对象
 */
export function handleLogout(_req: Request, res: Response): void {
  res.status(200).json({
    success: true,
    message: '登出成功',
  });
}

/**
 * 刷新令牌
 * @param req Express 请求对象
 * @param res Express 响应对象
 */
export async function refreshToken(req: Request, res: Response): Promise<void> {
  try {
    const user = (req as Express.Request & { user?: JwtPayload }).user;

    if (!user) {
      res.status(401).json({
        success: false,
        error: '未认证',
      });
      return;
    }

    const newToken = generateToken({
      userId: user.userId,
      tenantId: user.tenantId,
      email: user.email,
      role: user.role,
    });

    res.status(200).json({
      success: true,
      token: newToken,
    });
  } catch (error) {
    console.error('令牌刷新错误:', error);
    res.status(500).json({
      success: false,
      error: '服务器内部错误',
    });
  }
}

export default {
  generateToken,
  verifyToken,
  hashPassword,
  comparePassword,
  createAuthMiddleware,
  authMiddleware,
  handleLogin,
  getCurrentUser,
  handleLogout,
  refreshToken,
  getJwtConfig,
};

/**
 * 认证路由模块
 * 提供认证相关的 API 端点
 * @version 1.0.0
 */

import { Router } from 'express';
import {
  handleLogin,
  getCurrentUser,
  handleLogout,
  refreshToken,
  authMiddleware,
} from '../auth/jwt.module';

const router = Router();

/**
 * POST /api/auth/login
 * 用户登录接口
 */
router.post('/login', handleLogin);

/**
 * GET /api/auth/me
 * 获取当前登录用户信息
 */
router.get('/me', authMiddleware, getCurrentUser);

/**
 * POST /api/auth/logout
 * 用户登出接口
 */
router.post('/logout', authMiddleware, handleLogout);

/**
 * POST /api/auth/refresh
 * 刷新访问令牌
 */
router.post('/refresh', authMiddleware, refreshToken);

export default router;

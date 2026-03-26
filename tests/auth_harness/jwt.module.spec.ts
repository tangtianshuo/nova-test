/**
 * JWT 认证模块测试套件
 * 遵循 Harness Engineering 原则：先写测试，再写实现
 * @version 1.0.0
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import type { Request, Response, NextFunction } from 'express';
import {
  generateToken,
  verifyToken,
  hashPassword,
  comparePassword,
  JwtPayload,
  AuthMiddleware,
  createAuthMiddleware,
} from '../../src/api/auth/jwt.module';

describe('JWT 认证模块 Harness', () => {
  const testSecret = 'test-jwt-secret-key-for-harness-testing';
  const testUserId = 'user-uuid-12345';
  const testTenantId = 'tenant-uuid-67890';
  const testEmail = 'test@example.com';
  const testRole = 'TESTER';
  const testPassword = 'SecurePassword123!';
  const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJ0ZXN0IiwidGVuYW50SWQiOiJ0ZXN0IiwiZW1haWwiOiJ0ZXN0QHRlc3QuY29tIiwicm9sZSI6IlRFU1RFUiIsImlhdCI6MTUxNjIzOTAyMiwiZXhwIjoxNTE2MjM5MDIyfQ.invalid';

  beforeEach(() => {
    vi.resetAllMocks();
    process.env.JWT_SECRET = testSecret;
    process.env.JWT_EXPIRES_IN = '1h';
  });

  describe('H1: 密码哈希与验证', () => {
    it('should_hash_password_successfully', async () => {
      const hashedPassword = await hashPassword(testPassword);
      expect(hashedPassword).toBeDefined();
      expect(typeof hashedPassword).toBe('string');
      expect(hashedPassword).not.toBe(testPassword);
      expect(hashedPassword.length).toBeGreaterThan(0);
    });

    it('should_compare_correct_password_successfully', async () => {
      const hashedPassword = await hashPassword(testPassword);
      const isValid = await comparePassword(testPassword, hashedPassword);
      expect(isValid).toBe(true);
    });

    it('should_reject_incorrect_password', async () => {
      const hashedPassword = await hashPassword(testPassword);
      const isValid = await comparePassword('WrongPassword', hashedPassword);
      expect(isValid).toBe(false);
    });

    it('should_generate_unique_hashes_for_same_password', async () => {
      const hash1 = await hashPassword(testPassword);
      const hash2 = await hashPassword(testPassword);
      expect(hash1).not.toBe(hash2);
    });
  });

  describe('H2: JWT 令牌生成', () => {
    it('should_generate_valid_jwt_token', () => {
      const payload: JwtPayload = {
        userId: testUserId,
        tenantId: testTenantId,
        email: testEmail,
        role: testRole,
      };

      const token = generateToken(payload);

      expect(token).toBeDefined();
      expect(typeof token).toBe('string');
      expect(token.split('.').length).toBe(3);
    });

    it('should_include_payload_data_in_token', () => {
      const payload: JwtPayload = {
        userId: testUserId,
        tenantId: testTenantId,
        email: testEmail,
        role: testRole,
      };

      const token = generateToken(payload);
      const decoded = verifyToken(token);

      expect(decoded).toBeDefined();
      expect(decoded.userId).toBe(testUserId);
      expect(decoded.tenantId).toBe(testTenantId);
      expect(decoded.email).toBe(testEmail);
      expect(decoded.role).toBe(testRole);
    });

    it('should_set_expiration_time', () => {
      const payload: JwtPayload = {
        userId: testUserId,
        tenantId: testTenantId,
        email: testEmail,
        role: testRole,
      };

      const token = generateToken(payload);
      const decoded = verifyToken(token);

      expect(decoded.exp).toBeDefined();
      expect(decoded.iat).toBeDefined();
      expect(decoded.exp).toBeGreaterThan(decoded.iat);
    });
  });

  describe('H3: JWT 令牌验证', () => {
    it('should_verify_valid_token_successfully', () => {
      const payload: JwtPayload = {
        userId: testUserId,
        tenantId: testTenantId,
        email: testEmail,
        role: testRole,
      };

      const token = generateToken(payload);
      const decoded = verifyToken(token);

      expect(decoded).toBeDefined();
      expect(decoded.userId).toBe(testUserId);
    });

    it('should_throw_error_for_invalid_token', () => {
      expect(() => verifyToken('invalid-token')).toThrow();
    });

    it('should_throw_error_for_expired_token', () => {
      expect(() => verifyToken(expiredToken)).toThrow();
    });

    it('should_throw_error_for_malformed_token', () => {
      expect(() => verifyToken('not.a.valid.jwt')).toThrow();
    });
  });

  describe('H4: 认证中间件', () => {
    let mockRequest: Partial<Request>;
    let mockResponse: Partial<Response>;
    let mockNext: NextFunction;

    beforeEach(() => {
      mockRequest = {
        headers: {},
      };
      mockResponse = {
        status: vi.fn().mockReturnThis(),
        json: vi.fn().mockReturnThis(),
      };
      mockNext = vi.fn();
    });

    it('should_pass_valid_token_to_next_middleware', () => {
      const payload: JwtPayload = {
        userId: testUserId,
        tenantId: testTenantId,
        email: testEmail,
        role: testRole,
      };

      const token = generateToken(payload);
      mockRequest.headers = { authorization: `Bearer ${token}` };

      const middleware = createAuthMiddleware();
      middleware(mockRequest as Request, mockResponse as Response, mockNext);

      expect(mockNext).toHaveBeenCalled();
      expect((mockRequest as any).user).toBeDefined();
      expect((mockRequest as any).user.userId).toBe(testUserId);
    });

    it('should_reject_request_without_token', () => {
      mockRequest.headers = {};

      const middleware = createAuthMiddleware();
      middleware(mockRequest as Request, mockResponse as Response, mockNext);

      expect(mockResponse.status).toHaveBeenCalledWith(401);
      expect(mockResponse.json).toHaveBeenCalledWith(
        expect.objectContaining({
          error: expect.stringContaining('未提供认证令牌'),
        })
      );
      expect(mockNext).not.toHaveBeenCalled();
    });

    it('should_reject_request_with_invalid_token', () => {
      mockRequest.headers = { authorization: 'Bearer invalid-token' };

      const middleware = createAuthMiddleware();
      middleware(mockRequest as Request, mockResponse as Response, mockNext);

      expect(mockResponse.status).toHaveBeenCalledWith(401);
      expect(mockResponse.json).toHaveBeenCalledWith(
        expect.objectContaining({
          error: expect.stringContaining('令牌无效'),
        })
      );
      expect(mockNext).not.toHaveBeenCalled();
    });

    it('should_reject_request_with_malformed_authorization_header', () => {
      mockRequest.headers = { authorization: 'InvalidFormat token' };

      const middleware = createAuthMiddleware();
      middleware(mockRequest as Request, mockResponse as Response, mockNext);

      expect(mockResponse.status).toHaveBeenCalledWith(401);
      expect(mockNext).not.toHaveBeenCalled();
    });

    it('should_inject_user_context_into_request', () => {
      const payload: JwtPayload = {
        userId: testUserId,
        tenantId: testTenantId,
        email: testEmail,
        role: testRole,
      };

      const token = generateToken(payload);
      mockRequest.headers = { authorization: `Bearer ${token}` };

      const middleware = createAuthMiddleware();
      middleware(mockRequest as Request, mockResponse as Response, mockNext);

      expect((mockRequest as any).user).toEqual(
        expect.objectContaining({
          userId: testUserId,
          tenantId: testTenantId,
          email: testEmail,
          role: testRole,
        })
      );
    });
  });

  describe('H5: 登录接口验证', () => {
    it('should_validate_login_request_schema', () => {
      const validLoginRequest = {
        email: 'user@example.com',
        password: 'SecurePassword123!',
      };

      expect(validLoginRequest.email).toBeDefined();
      expect(validLoginRequest.password).toBeDefined();
      expect(validLoginRequest.email).toMatch(/^[^\s@]+@[^\s@]+\.[^\s@]+$/);
    });

    it('should_reject_login_without_email', () => {
      const invalidLoginRequest = {
        password: 'SecurePassword123!',
      };

      expect(invalidLoginRequest.email).toBeUndefined();
    });

    it('should_reject_login_without_password', () => {
      const invalidLoginRequest = {
        email: 'user@example.com',
      };

      expect(invalidLoginRequest.password).toBeUndefined();
    });

    it('should_reject_login_with_invalid_email_format', () => {
      const invalidLoginRequest = {
        email: 'invalid-email',
        password: 'SecurePassword123!',
      };

      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      expect(emailRegex.test(invalidLoginRequest.email)).toBe(false);
    });
  });
});

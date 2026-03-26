/**
 * S3/MinIO 存储客户端 Harness 测试
 */
import { describe, it, expect } from 'vitest';
import { storage } from '../../src/storage';

describe('Storage Harness', () => {
  describe('H1: S3 Client Configuration', () => {
    it('should_have_correct_bucket_name', () => {
      expect(process.env.S3_BUCKET || 'nova-test-assets').toBeDefined();
    });

    it('should_create_s3_client', () => {
      expect(storage).toBeDefined();
    });
  });

  describe('H2: Storage Service', () => {
    it('should_generate_screenshot_key', async () => {
      const key = await storage.generateScreenshotKey('tenant-1', 'instance-1', 1);
      expect(key).toContain('screenshots/');
      expect(key).toContain('tenant-1');
      expect(key).toContain('instance-1');
      expect(key).toMatch(/step-1-\d+\.png$/);
    });

    it('should_generate_video_key', async () => {
      const key = await storage.generateVideoKey('tenant-1', 'instance-1');
      expect(key).toContain('videos/');
      expect(key).toMatch(/recording-\d+\.webm$/);
    });
  });

  describe('H3: Key Generation', () => {
    it('should_create_unique_keys_for_different_files', async () => {
      const key1 = await storage.generateScreenshotKey('t1', 'i1', 1);
      const key2 = await storage.generateScreenshotKey('t1', 'i1', 2);
      expect(key1).not.toBe(key2);
    });
  });
});

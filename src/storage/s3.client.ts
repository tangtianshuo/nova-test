/**
 * S3/MinIO 存储客户端
 * 用于存储截图、录屏等测试资产
 */
import {
  S3Client,
  PutObjectCommand,
  GetObjectCommand,
  DeleteObjectCommand,
  ListObjectsV2Command,
  S3ClientConfig,
} from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';

const globalForS3 = globalThis as unknown as {
  s3Client: S3Client | undefined;
};

export function createS3Client(): S3Client {
  const config: S3ClientConfig = {
    region: process.env.S3_REGION || 'us-east-1',
    credentials: {
    accessKeyId: process.env.S3_ACCESS_KEY_ID || '',
    secretAccessKey: process.env.S3_SECRET_ACCESS_KEY || '',
  },
    endpoint: process.env.S3_ENDPOINT || undefined,
    forcePathStyle: !!process.env.S3_FORCE_PATH_STYLE,
  };

  const client = new S3Client(config);

  console.log('[S3] 客户端已初始化');
  return client;
}

export const s3Client = globalForS3.s3Client ?? createS3Client();

if (process.env.NODE_ENV !== 'production') {
  globalForS3.s3Client = s3Client;
}

export const S3_BUCKET = process.env.S3_BUCKET || 'nova-test-assets';

export interface UploadResult {
  key: string;
  url: string;
  etag?: string;
}

export class StorageService {
  private bucket: string;

  constructor(bucket: string = S3_BUCKET) {
    this.bucket = bucket;
  }

  async uploadFile(
    key: string,
    body: Buffer | Uint8Array | string,
    contentType: string = 'application/octet-stream'
  ): Promise<UploadResult> {
    await s3Client.send(
      new PutObjectCommand({
        Bucket: this.bucket,
        Key: key,
        Body: body,
        ContentType: contentType,
      })
    );

    const url = await this.getSignedUrl(key);
    return { key, url };
  }

  async downloadFile(key: string): Promise<Buffer | undefined> {
    const response = await s3Client.send(
      new GetObjectCommand({
        Bucket: this.bucket,
        Key: key,
      })
    );
    if (!response.Body) return undefined;
    const chunks: Uint8Array[] = [];
    for await (const chunk of response.Body as AsyncIterable<Uint8Array>) {
      chunks.push(chunk);
    }
    return Buffer.concat(chunks);
  }

  async deleteFile(key: string): Promise<void> {
    await s3Client.send(
      new DeleteObjectCommand({
        Bucket: this.bucket,
        Key: key,
      })
    );
  }

  async listFiles(prefix: string = ''): Promise<string[]> {
    const response = await s3Client.send(
      new ListObjectsV2Command({
        Bucket: this.bucket,
        Prefix: prefix,
      })
    );
    return (response.Contents || []).map((item) => item.Key || '');
  }

  async getSignedUrl(key: string, expiresIn: number = 3600): Promise<string> {
    const command = new GetObjectCommand({
      Bucket: this.bucket,
      Key: key,
    });

    return getSignedUrl(s3Client, command, {
      expiresIn,
    });
  }

  async generateScreenshotKey(
    tenantId: string,
    instanceId: string,
    stepNumber: number
  ): Promise<string> {
    const timestamp = Date.now();
    return `screenshots/${tenantId}/${instanceId}/step-${stepNumber}-${timestamp}.png`;
  }

  async generateVideoKey(
    tenantId: string,
    instanceId: string
  ): Promise<string> {
    const timestamp = Date.now();
    return `videos/${tenantId}/${instanceId}/recording-${timestamp}.webm`;
  }
}

export const storage = new StorageService();
export default storage;

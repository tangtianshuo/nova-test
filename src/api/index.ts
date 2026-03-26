/**
 * API 入口模块
 * @version 1.0.0
 */

import express from 'express';
import taskRoutes from './routes/task.routes';
import authRoutes from './routes/auth.routes';
import instanceRoutes from './routes/instance.routes';
import { extractTenant } from './middleware';

const app = express();
const _PORT = process.env.PORT || 3000;
void _PORT;

app.use(express.json());

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.use('/api/auth', authRoutes);
app.use('/api/tasks', extractTenant, taskRoutes);
app.use('/api/instances', extractTenant, instanceRoutes);

export default app;

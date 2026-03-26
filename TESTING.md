# 项目整体测试计划

## 测试范围

| 模块 | 测试类型 | 覆盖率 |
|------|----------|--------|
| Python 执行引擎 | 单元测试 + 集成测试 | 85% |
| TypeScript 前端 | 组件测试 + E2E | 70% |
| 数据库 | Schema 测试 | 100% |
| API | Contract 测试 | 90% |
| Docker Compose | 配置验证 | 100% |

## 测试执行

### Python 测试
pytest tests/ -v --cov

### TypeScript 测试
npm test -- --coverage

### Docker 验证
docker-compose config --quiet

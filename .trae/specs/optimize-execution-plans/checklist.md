# Checklist

## Phase 1: 计划结构优化

### EP-01 SDD与Schema计划
- [x] 计划包含标准化结构元素（目标、范围、 Harness、 TDD步骤、设计原则、交付物、验收标准、依赖关系）
- [x] Harness 测试用例列表已细化（至少每个 Schema 3 个正向 + 3 个负向用例）
- [x] 代码目录结构映射已添加
- [x] 中文注释规范说明已补充
### EP-02 数据库与存储计划
- [x] 与 EP-01 的依赖关系已说明
- [x] DB Migration Harness 测试用例已细化
- [x] Storage Access Harness 具体用例已添加
- [x] 数据模型与 Schema 的映射关系已补充
### EP-03 控制面API与鉴权计划
- [x] 与 EP-01, EP-02 的依赖关系已添加
- [x] API Contract Harness 测试用例已细化（含错误码）
- [x] Multi-tenant Negative Harness 具体用例已添加
- [x] RBAC 权限矩阵已补充
### EP-04 AaaS执行面与状态机计划
- [x] 与 EP-01, EP-02, EP-03 的依赖关系已添加
- [x] StateMachine Node Harness 测试用例已细化
- [x] Replay Harness 具体场景已添加
- [x] 模型输出容错 Harness 已细化
### EP-05 推流与HIL计划
- [x] 与 EP-04 的依赖关系已添加
- [x] EventSchema Harness 测试用例已细化
- [x] HIL Flow Harness 完整场景已添加
- [x] WebSocket 契约测试规范已补充
### EP-06 报告与导出计划
- [x] 与 EP-02, EP-04, EP-05 的依赖关系已添加
- [x] Golden File Harness 测试用例已细化
- [x] Security Harness 敏感信息扫描规则已添加
- [x] 导出格式规范已补充
### EP-07 UI控制台计划
- [x] 与 EP-03, EP-05, EP-06 的依赖关系已添加
- [x] No-Scroll Harness 测试用例已细化
- [x] Paging Harness 分页测试规范已添加
- [x] Overlay Harness 标注层测试已补充
### EP-08 安全合规与多租户验证计划
- [x] 安全计划贯穿所有迭代的定位已明确
- [x] Tenant Isolation Harness 测试用例已细化
- [x] Sensitive Leak Harness 扫描规则已添加
- [x] HIL Audit Harness 审计字段规范已补充
### EP-09 可观测性与发布闸门计划
- [x] 与所有计划的依赖关系已添加
- [x] Traceability Harness 测试用例已细化
- [x] 发布闸门 DoD 清单已补充
- [x] Performance Harness 性能指标已添加
## Phase 2: 索引与依赖关系
### 计划索引更新
- [x] 00_INDEX.md 包含所有计划的标准摘要
- [x] 每个计划的优先级 (P0/P1) 已标注
- [x] 迭代建议已更新
### 依赖关系可视化
- [x] Mermaid 依赖关系图已生成
- [x] 关键路径已标注
- [x] 可并行的计划已标注
## Phase 3: 代码目录结构规划
- [x] 后端目录结构已定义 (NestJS/Python)
- [x] 前端目录结构已定义 (Next.js)
- [x] 测试目录结构已定义
- [x] 配置文件规范已定义
## Phase 4: 中文注释规范
- [x] 状态机注释规范已创建
- [x] 安全边界注释规范已创建
- [x] HIL 处理注释规范已创建
- [x] 错误恢复注释规范已创建
## 最终验收
- [x] 所有 9 个执行计划已优化完成
- [x] 计划间依赖关系清晰
- [x] 测试用例可直接执行
- [x] 代码结构有明确规划
- [x] 中文注释规范明确
# Runbook 目录

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目录说明

本目录存放所有运行手册（Runbook），包含门禁（Gate）故障排查与运维操作指南两大类。

## Runbook 分类

| 类别 | 目录 | 说明 |
|------|------|------|
| 门禁 Runbook | `gates/` | CI 门禁失败时的故障排查与处理 |
| 运维操作 Runbook | `operations/` | 发布、部署、回滚、迁移等运维操作流程 |

## 门禁 Runbook 规范

每个门禁 Runbook 必须包含以下章节：

1. **门禁概述**：门禁名称、ID、类型、触发条件
2. **常见失败原因**：按频率排序的失败原因列表
3. **解决方案**：对应每个失败原因的解决步骤
4. **手动执行**：本地手动执行该门禁的方法
5. **升级路径**：无法解决时的联系人与升级流程

## 运维操作 Runbook 规范

每个运维操作 Runbook 必须包含以下章节：

1. **操作概述**：操作名称、ID、类型、适用场景、前置条件
2. **操作步骤**：分阶段详细操作步骤
3. **回滚方案**：回滚触发条件与操作步骤
4. **常见问题与解决方案**：按频率排序的常见问题
5. **相关链接**：关联的规范、脚本、API 文档

## 门禁 Runbook 列表

| Gate ID | 文件 | 说明 |
|---------|------|------|
| G-STATIC-001 | [ruff.md](gates/ruff.md) | Ruff Lint 静态检查 |
| G-STATIC-002 | [mypy.md](gates/mypy.md) | Mypy 类型检查 |
| G-UNIT-001 | [vote-tests.md](gates/vote-tests.md) | vote-service 单元测试 |
| G-UNIT-002 | [world-tests.md](gates/world-tests.md) | world-service 单元测试 |
| G-UNIT-003 | [content-tests.md](gates/content-tests.md) | content-service 单元测试 |
| G-UNIT-004 | [workers-tests.md](gates/workers-tests.md) | workers 单元测试 |
| G-UNIT-005 | [generation-tests.md](gates/generation-tests.md) | generation-service 单元测试 |
| G-UNIT-006 | [review-tests.md](gates/review-tests.md) | review-service 单元测试 |
| G-UNIT-007 | [player-tests.md](gates/player-tests.md) | player-service 单元测试 |
| G-UNIT-008 | [ops-tests.md](gates/ops-tests.md) | ops-service 单元测试 |
| G-UNIT-009 | [gateway-tests.md](gates/gateway-tests.md) | gateway-service 单元测试 |
| G-CONTENT-001 | [world_consistency.md](gates/world_consistency.md) | 世界一致性检查 |
| G-CONTENT-002 | [reward_boundary.md](gates/reward_boundary.md) | 数值平衡检查 |
| G-CONTENT-003 | [content_safety.md](gates/content_safety.md) | 内容安全检查 |
| G-CONTENT-004 | [duplication.md](gates/duplication.md) | 重复度检查 |
| G-E2E-001 | [critical_e2e.md](gates/critical_e2e.md) | 关键路径 E2E 测试 |

## 使用流程

1. CI 门禁失败时，根据失败日志中的 `gate_id` 定位对应 Runbook
2. 按 Runbook 中的"常见失败原因"排查问题
3. 执行"解决方案"中的步骤修复问题
4. 本地执行"手动执行"验证修复
5. 提交代码重新触发 CI

## 运维操作 Runbook 列表

| Operation ID | 文件 | 说明 |
|--------------|------|------|
| OP-RELEASE-001 | [gray-release.md](operations/gray-release.md) | 内容包灰度发布 |
| OP-RELEASE-002 | [full-release.md](operations/full-release.md) | 内容包全量发布 |
| OP-RELEASE-003 | [rollback.md](operations/rollback.md) | 内容包回滚 |
| OP-DEPLOY-001 | [service-deployment.md](operations/service-deployment.md) | 服务部署与更新 |
| OP-DEPLOY-002 | [db-migration.md](operations/db-migration.md) | 数据库迁移 |
| OP-INIT-001 | [seed-content.md](operations/seed-content.md) | 首期内容包初始化 |

## 使用流程

### 门禁故障排查

1. CI 门禁失败时，根据失败日志中的 `gate_id` 定位对应 Runbook
2. 按 Runbook 中的"常见失败原因"排查问题
3. 执行"解决方案"中的步骤修复问题
4. 本地执行"手动执行"验证修复
5. 提交代码重新触发 CI

### 运维操作执行

1. 确定需要执行的操作类型（发布/回滚/部署/迁移/初始化）
2. 找到对应 Runbook，仔细阅读"操作概述"和"前置条件"
3. 按"操作步骤"逐步执行，每步完成后确认预期结果
4. 执行完成后按"验证方法"确认操作成功
5. 如出现问题，按"回滚方案"执行回滚
6. 记录操作结果和关键指标

## 维护规则

- 新增门禁时，必须同步创建对应 Runbook
- 新增运维操作流程时，必须同步创建对应 Runbook
- 定期更新失败原因和解决方案（每季度或出现新失败模式时）
- Runbook 内容应保持简洁，避免冗长描述
- 所有 Runbook 必须包含回滚方案（不可逆操作除外）
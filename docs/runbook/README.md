# Runbook 目录

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目录说明

本目录存放所有门禁（Gate）的运行手册（Runbook），用于指导 CI 门禁失败时的故障排查与处理。

## Runbook 规范

每个门禁 Runbook 必须包含以下章节：

1. **门禁概述**：门禁名称、ID、类型、触发条件
2. **常见失败原因**：按频率排序的失败原因列表
3. **解决方案**：对应每个失败原因的解决步骤
4. **手动执行**：本地手动执行该门禁的方法
5. **升级路径**：无法解决时的联系人与升级流程

## 门禁 Runbook 列表

| Gate ID | 文件 | 说明 |
|---------|------|------|
| G-STATIC-001 | [ruff.md](gates/ruff.md) | Ruff Lint 静态检查 |
| G-STATIC-002 | [mypy.md](gates/mypy.md) | Mypy 类型检查 |
| G-UNIT-001 | [vote-tests.md](gates/vote-tests.md) | vote-service 单元测试 |
| G-UNIT-002 | [world-tests.md](gates/world-tests.md) | world-service 单元测试 |
| G-UNIT-003 | [content-tests.md](gates/content-tests.md) | content-service 单元测试 |
| G-UNIT-004 | [workers-tests.md](gates/workers-tests.md) | workers 单元测试 |
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

## 维护规则

- 新增门禁时，必须同步创建对应 Runbook
- 定期更新失败原因和解决方案（每季度或出现新失败模式时）
- Runbook 内容应保持简洁，避免冗长描述
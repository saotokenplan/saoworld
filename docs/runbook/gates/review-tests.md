# Runbook: Review Service Unit Tests (G-UNIT-006)

> gate_id: G-UNIT-006
> gate_name: Service Unit Tests (review)
> gate_type: unit
> owner: Backend Agent

## 门禁概述

Review Service Unit Tests 是 review-service 的单元测试门禁，验证内容审核记录管理、审核批准/拒绝流程、风险等级评估等核心功能。

**触发条件**：
- 路径：`services/review/**`
- 触发：`on_pr`

**执行命令**：
```bash
cd services/review && pytest
```

**预期耗时**：40 秒

## 常见失败原因

### 1. 数据库连接失败

**现象**：
- `sqlalchemy.exc.OperationalError`
- 测试数据库未启动

**解决方案**：
```bash
cd infra && docker compose -f docker-compose.dev.yml up -d
sleep 10
cd services/review && alembic upgrade head
cd services/review && pytest
```

### 2. 审核状态机校验失败

**现象**：
- 审核记录状态迁移测试失败
- 非法状态转换被允许

**解决方案**：
```bash
cd services/review && pytest -v --tb=short
# 检查文件：services/review/app/domain/models.py
# 确认状态转换逻辑是否正确（pending → approved/rejected/manual_review）
```

### 3. 风险等级评估错误

**现象**：
- 风险等级（low/medium/high/critical）评估测试失败
- 风险判断逻辑不正确

**解决方案**：
```bash
cd services/review && pytest -k "risk" -v
# 检查文件：services/review/app/repositories/review_repo.py
# 确认风险等级评估逻辑是否正确
```

### 4. 审核批准权限校验失败

**现象**：
- 审核批准接口权限检查测试失败
- 无权限用户被允许批准

**解决方案**：
```bash
cd services/review && pytest -k "auth" -v
# 检查文件：services/review/app/core/auth.py
# 确认 review:approve scope 校验是否正确
```

## 手动执行

```bash
cd services/review && pytest
cd services/review && pytest tests/test_review_approve.py -v
cd services/review && pytest tests/test_review_records.py::test_create_review_record -v
cd services/review && pytest --cov=app --cov-report=html
```

## 升级路径

| 级别 | 处理方式 |
|------|----------|
| 数据库问题 | 启动 Docker 数据库或检查连接字符串 |
| 状态机问题 | 检查 models.py 中的状态转换逻辑 |
| 权限问题 | 检查 auth.py 中的 scope 校验逻辑 |
| 无法解决 | 联系 Backend Agent |

## 相关链接

- 规范文档：`docs/30-api/api-overview.md`
- 测试文件：`services/review/tests/`
- 门禁注册表：`docs/40-dev-loop/gate_registry.yaml`
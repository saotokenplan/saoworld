# Runbook: Generation Service Unit Tests (G-UNIT-005)

> gate_id: G-UNIT-005
> gate_name: Service Unit Tests (generation)
> gate_type: unit
> owner: Backend Agent

## 门禁概述

Generation Service Unit Tests 是 generation-service 的单元测试门禁，验证内容生成请求管理、生成对象状态机、审核流程等核心功能。

**触发条件**：
- 路径：`services/generation/**`
- 触发：`on_pr`

**执行命令**：
```bash
cd services/generation && pytest
```

**预期耗时**：55 秒

## 常见失败原因

### 1. 数据库连接失败

**现象**：
- `sqlalchemy.exc.OperationalError`
- 测试数据库未启动

**解决方案**：
```bash
cd infra && docker compose -f docker-compose.dev.yml up -d
sleep 10
cd services/generation && alembic upgrade head
cd services/generation && pytest
```

### 2. 生成请求状态机校验失败

**现象**：
- 生成请求状态迁移测试失败
- 非法状态转换被允许

**解决方案**：
```bash
cd services/generation && pytest -v --tb=short
# 检查文件：services/generation/app/domain/models.py
# 确认状态转换逻辑是否正确（pending → processing → succeeded/failed_retryable/failed_permanent）
```

### 3. 生成对象审核流程错误

**现象**：
- 生成对象审核状态更新测试失败
- 审核结果未正确记录

**解决方案**：
```bash
cd services/generation && pytest -k "review" -v
# 检查文件：services/generation/app/repositories/generation_repo.py
# 确认审核状态更新逻辑是否正确
```

### 4. 事件发布集成失败

**现象**：
- 生成完成事件发布测试失败
- Redis 连接失败

**解决方案**：
```bash
cd infra && docker compose -f docker-compose.dev.yml up -d redis
sleep 5
cd services/generation && pytest -k "event" -v
```

## 手动执行

```bash
cd services/generation && pytest
cd services/generation && pytest tests/test_generation_requests.py -v
cd services/generation && pytest tests/test_generated_objects.py::test_approve_object -v
cd services/generation && pytest --cov=app --cov-report=html
```

## 升级路径

| 级别 | 处理方式 |
|------|----------|
| 数据库问题 | 启动 Docker 数据库或检查连接字符串 |
| 状态机问题 | 检查 models.py 中的状态转换逻辑 |
| 事件发布问题 | 检查 Redis 连接和事件发布器配置 |
| 无法解决 | 联系 Backend Agent |

## 相关链接

- 规范文档：`docs/30-api/api-overview.md`
- 测试文件：`services/generation/tests/`
- 门禁注册表：`docs/40-dev-loop/gate_registry.yaml`
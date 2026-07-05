# Runbook: Ops Service Unit Tests (G-UNIT-008)

> gate_id: G-UNIT-008
> gate_name: Service Unit Tests (ops)
> gate_type: unit
> owner: Backend Agent

## 门禁概述

Ops Service Unit Tests 是 ops-service 的单元测试门禁，验证运营仪表盘、运营操作记录、系统状态查询等核心功能。

**触发条件**：
- 路径：`services/ops/**`
- 触发：`on_pr`

**执行命令**：
```bash
cd services/ops && pytest
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
cd services/ops && alembic upgrade head
cd services/ops && pytest
```

### 2. 仪表盘数据聚合失败

**现象**：
- 运营仪表盘数据查询测试失败
- 聚合指标计算错误

**解决方案**：
```bash
cd services/ops && pytest -k "dashboard" -v
# 检查文件：services/ops/app/repositories/dashboard_repo.py
# 确认数据聚合逻辑是否正确
```

### 3. 运营操作记录缺失

**现象**：
- 运营操作记录测试失败
- 操作未正确记录到 ops_actions 表

**解决方案**：
```bash
cd services/ops && pytest -k "action" -v
# 检查文件：services/ops/app/repositories/ops_action_repo.py
# 确认操作记录逻辑是否正确
```

### 4. 系统状态查询失败

**现象**：
- 系统状态接口测试失败
- 服务健康检查返回错误

**解决方案**：
```bash
cd services/ops && pytest -k "status" -v
# 检查文件：services/ops/app/api/routes.py
# 确认系统状态查询逻辑是否正确
```

## 手动执行

```bash
cd services/ops && pytest
cd services/ops && pytest tests/test_dashboard.py -v
cd services/ops && pytest tests/test_ops_actions.py::test_create_action -v
cd services/ops && pytest --cov=app --cov-report=html
```

## 升级路径

| 级别 | 处理方式 |
|------|----------|
| 数据库问题 | 启动 Docker 数据库或检查连接字符串 |
| 聚合问题 | 检查 dashboard_repo.py 中的数据聚合逻辑 |
| 记录问题 | 检查 ops_action_repo.py 中的操作记录逻辑 |
| 无法解决 | 联系 Backend Agent |

## 相关链接

- 规范文档：`docs/30-api/api-overview.md`
- 测试文件：`services/ops/tests/`
- 门禁注册表：`docs/40-dev-loop/gate_registry.yaml`
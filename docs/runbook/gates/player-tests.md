# Runbook: Player Service Unit Tests (G-UNIT-007)

> gate_id: G-UNIT-007
> gate_name: Service Unit Tests (player)
> gate_type: unit
> owner: Backend Agent

## 门禁概述

Player Service Unit Tests 是 player-service 的单元测试门禁，验证玩家信息管理、任务状态跟踪、区域解锁等核心功能。

**触发条件**：
- 路径：`services/player/**`
- 触发：`on_pr`

**执行命令**：
```bash
cd services/player && pytest
```

**预期耗时**：35 秒

## 常见失败原因

### 1. 数据库连接失败

**现象**：
- `sqlalchemy.exc.OperationalError`
- 测试数据库未启动

**解决方案**：
```bash
cd infra && docker compose -f docker-compose.dev.yml up -d
sleep 10
cd services/player && alembic upgrade head
cd services/player && pytest
```

### 2. 任务状态机校验失败

**现象**：
- 玩家任务状态迁移测试失败
- 非法状态转换被允许

**解决方案**：
```bash
cd services/player && pytest -v --tb=short
# 检查文件：services/player/app/domain/models.py
# 确认状态转换逻辑是否正确（available → active → completed/failed）
```

### 3. 区域解锁逻辑错误

**现象**：
- 区域解锁接口测试失败
- 玩家无法解锁新区域

**解决方案**：
```bash
cd services/player && pytest -k "unlock" -v
# 检查文件：services/player/app/repositories/player_region_repo.py
# 确认区域解锁逻辑是否正确
```

### 4. UUID 类型兼容问题

**现象**：
- SQLite 测试环境下 UUID 类型转换失败

**解决方案**：
```bash
cd services/player && pytest -xvs
# 检查文件：services/player/app/domain/uuid_type.py
# 确认自定义 UUID 类型是否正确实现
```

## 手动执行

```bash
cd services/player && pytest
cd services/player && pytest tests/test_player_api.py -v
cd services/player && pytest tests/test_ops_api.py::test_unlock_region -v
cd services/player && pytest --cov=app --cov-report=html
```

## 升级路径

| 级别 | 处理方式 |
|------|----------|
| 数据库问题 | 启动 Docker 数据库或检查连接字符串 |
| 状态机问题 | 检查 models.py 中的状态转换逻辑 |
| UUID 类型问题 | 检查 uuid_type.py 中的自定义类型实现 |
| 无法解决 | 联系 Backend Agent |

## 相关链接

- 规范文档：`docs/30-api/api-overview.md`
- 测试文件：`services/player/tests/`
- 门禁注册表：`docs/40-dev-loop/gate_registry.yaml`
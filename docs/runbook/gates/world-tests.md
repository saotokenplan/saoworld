# Runbook: World Service Unit Tests (G-UNIT-002)

> gate_id: G-UNIT-002
> gate_name: Service Unit Tests (world)
> gate_type: unit
> owner: Backend Agent

## 门禁概述

World Service Unit Tests 是 world-service 的单元测试门禁，验证区域管理、区域状态机、审计日志等功能。

**触发条件**：
- 路径：`services/world/**`
- 触发：`on_pr`

**执行命令**：
```bash
cd services/world && pytest
```

**预期耗时**：45 秒

## 常见失败原因

### 1. 数据库连接失败

**现象**：
- `sqlalchemy.exc.OperationalError`
- 测试数据库未启动

**解决方案**：
```bash
# 启动本地开发数据库
cd infra && docker compose -f docker-compose.dev.yml up -d

# 等待数据库就绪
sleep 10

# 执行迁移
cd services/world && alembic upgrade head

# 重新运行测试
cd services/world && pytest
```

### 2. 区域状态机校验失败

**现象**：
- 区域状态迁移测试失败
- 非法状态转换被允许

**解决方案**：
```bash
# 查看失败的测试用例
cd services/world && pytest -v --tb=short

# 检查状态机实现
# 文件：services/world/app/domain/models.py
# 确认状态转换逻辑是否正确（locked → active → unstable → archived）
```

### 3. 区域权限检查失败

**现象**：
- 玩家接口权限测试失败
- 应该返回 403 但返回了其他状态码

**解决方案**：
```bash
# 运行权限相关测试
cd services/world && pytest -k "auth" -v

# 检查权限校验逻辑
# 文件：services/world/app/core/auth.py
# 确认 world:read scope 校验是否正确
```

## 手动执行

```bash
# 运行所有测试
cd services/world && pytest

# 运行特定测试文件
cd services/world && pytest tests/test_world_regions.py -v

# 查看覆盖率报告
cd services/world && pytest --cov=app --cov-report=html
```

## 升级路径

| 级别 | 处理方式 |
|------|----------|
| 数据库问题 | 启动 Docker 数据库或检查连接字符串 |
| 状态机错误 | 检查区域状态转换逻辑 |
| 权限错误 | 检查 auth.py 中的 scope 校验 |
| 无法解决 | 联系 Backend Agent |

## 相关链接

- 规范文档：`docs/30-api/api-overview.md`
- 测试文件：`services/world/tests/`
- 门禁注册表：`docs/40-dev-loop/gate_registry.yaml`
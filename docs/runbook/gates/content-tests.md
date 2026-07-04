# Runbook: Content Service Unit Tests (G-UNIT-003)

> gate_id: G-UNIT-003
> gate_name: Service Unit Tests (content)
> gate_type: unit
> owner: Backend Agent

## 门禁概述

Content Service Unit Tests 是 content-service 的单元测试门禁，验证内容包管理、灰度发布、回滚等核心功能。

**触发条件**：
- 路径：`services/content/**`
- 触发：`on_pr`

**执行命令**：
```bash
cd services/content && pytest
```

**预期耗时**：50 秒

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
cd services/content && alembic upgrade head

# 重新运行测试
cd services/content && pytest
```

### 2. 灰度发布可见性判断失败

**现象**：
- 灰度范围判断测试失败
- 玩家应该看到/看不到灰度内容包但结果相反

**解决方案**：
```bash
# 运行灰度相关测试
cd services/content && pytest -k "gray" -v

# 检查灰度判断逻辑
# 文件：services/content/app/repositories/content_repo.py
# 确认 player_ids > player_percent > region_ids 的优先级是否正确
```

### 3. 内容包状态机校验失败

**现象**：
- 内容包状态迁移测试失败
- 非法状态转换被允许

**解决方案**：
```bash
# 查看失败的测试用例
cd services/content && pytest -v --tb=short

# 检查状态机实现
# 文件：services/content/app/domain/models.py
# 确认状态转换逻辑是否正确（packaged → gray → live → archived）
```

### 4. 回滚逻辑错误

**现象**：
- 回滚测试失败
- rolled_back 状态的包被允许重新发布

**解决方案**：
```bash
# 运行回滚相关测试
cd services/content && pytest -k "rollback" -v

# 检查回滚逻辑
# 文件：services/content/app/repositories/content_repo.py
# 确认 rolled_back 是终态，不可再向 live/gray 迁移
```

## 手动执行

```bash
# 运行所有测试
cd services/content && pytest

# 运行特定测试文件
cd services/content && pytest tests/test_content_packages.py -v

# 查看覆盖率报告
cd services/content && pytest --cov=app --cov-report=html
```

## 升级路径

| 级别 | 处理方式 |
|------|----------|
| 数据库问题 | 启动 Docker 数据库或检查连接字符串 |
| 灰度判断错误 | 检查 content_repo.py 中的灰度可见性逻辑 |
| 状态机错误 | 检查内容包状态转换逻辑 |
| 回滚错误 | 确认 rolled_back 终态约束 |
| 无法解决 | 联系 Backend Agent |

## 相关链接

- 规范文档：`docs/30-api/api-overview.md`
- 测试文件：`services/content/tests/`
- 门禁注册表：`docs/40-dev-loop/gate_registry.yaml`
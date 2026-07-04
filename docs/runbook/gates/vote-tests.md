# Runbook: Vote Service Unit Tests (G-UNIT-001)

> gate_id: G-UNIT-001
> gate_name: Service Unit Tests (vote)
> gate_type: unit
> owner: Backend Agent

## 门禁概述

Vote Service Unit Tests 是 vote-service 的单元测试门禁，验证投票周期管理、投票提交、结算逻辑等核心功能。

**触发条件**：
- 路径：`services/vote/**`
- 触发：`on_pr`

**执行命令**：
```bash
cd services/vote && pytest
```

**预期耗时**：60 秒

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
cd services/vote && alembic upgrade head

# 重新运行测试
cd services/vote && pytest
```

### 2. 测试数据冲突

**现象**：
- `IntegrityError: UNIQUE constraint failed`
- 测试中创建了重复的投票周期或候选项

**解决方案**：
```bash
# 使用 pytest 的 --clear-db 选项（如果配置）
cd services/vote && pytest --clear-db

# 或手动清理测试数据库
# 删除测试数据库并重建
```

### 3. 状态机校验失败

**现象**：
- 投票周期状态迁移测试失败
- 非法状态转换被允许

**解决方案**：
```bash
# 查看失败的测试用例
cd services/vote && pytest -v --tb=short

# 检查状态机实现
# 文件：services/vote/app/domain/models.py
# 确认状态转换逻辑是否正确（draft → scheduled → open → closed → finalized）
```

### 4. 投票结算逻辑错误

**现象**：
- 关闭投票时计票结果不正确
- 获胜候选项计算错误

**解决方案**：
```bash
# 运行结算相关测试
cd services/vote && pytest -k "close" -v

# 检查结算逻辑实现
# 文件：services/vote/app/repositories/vote_repo.py
# 确认加权计算是否正确
```

### 5. 幂等键验证失败

**现象**：
- 相同幂等键提交多次时测试失败
- 应该返回首次结果但没有

**解决方案**：
```bash
# 运行幂等性相关测试
cd services/vote && pytest -k "idempotent" -v

# 检查幂等键处理逻辑
# 文件：services/vote/app/api/routes.py
# 确认数据库 UNIQUE 约束和幂等检查是否正确
```

## 手动执行

```bash
# 运行所有测试
cd services/vote && pytest

# 运行特定测试文件
cd services/vote && pytest tests/test_vote_flow.py -v

# 运行特定测试函数
cd services/vote && pytest tests/test_vote_flow.py::test_submit_vote_success -v

# 查看覆盖率报告
cd services/vote && pytest --cov=app --cov-report=html
```

## 升级路径

| 级别 | 处理方式 |
|------|----------|
| 数据库问题 | 启动 Docker 数据库或检查连接字符串 |
| 数据冲突 | 使用 --clear-db 或清理测试数据 |
| 逻辑错误 | 检查对应的 repository 或 route 实现 |
| 无法解决 | 联系 Backend Agent |

## 相关链接

- 规范文档：`docs/30-api/api-overview.md`
- 测试文件：`services/vote/tests/`
- 门禁注册表：`docs/40-dev-loop/gate_registry.yaml`
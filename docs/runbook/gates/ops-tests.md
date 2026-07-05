# Runbook: Ops Service Unit Tests (G-UNIT-008)

> gate_id: G-UNIT-008
> gate_name: Service Unit Tests (ops)
> gate_type: unit
> owner: Backend Agent

## 门禁概述

Ops Service Unit Tests 是 ops-service 的单元测试门禁，验证运营仪表盘、运营操作记录、系统状态查询等核心功能。

**门禁名称**：Service Unit Tests (ops)
**门禁 ID**：G-UNIT-008
**门禁类型**：unit
**触发条件**：
- 路径：`services/ops/**`
- 触发：`on_pr`
**覆盖的风险类型**：regression, data-integrity

**执行命令**：
```bash
cd services/ops && pytest
```

**预期耗时**：40 秒

## 常见失败原因

以下按发生频率从高到低排序：

### 1. 数据库连接失败

**现象**：
- `sqlalchemy.exc.OperationalError`
- 测试数据库未启动或连接字符串错误

### 2. 测试数据问题

**现象**：
- `IntegrityError: UNIQUE constraint failed`
- 测试 fixture 数据冲突或清理不彻底
- 运营操作记录数据与预期不一致

### 3. 断言失败

**现象**：
- `AssertionError`
- 仪表盘数据聚合结果不符合预期
- 运营操作记录查询结果与预期不符

### 4. 异步测试问题

**现象**：
- 异步测试超时
- `asyncio` 事件循环相关错误
- 数据库会话未正确关闭

### 5. Mock 配置错误

**现象**：
- Mock 对象返回值不正确
- Mock 路径配置错误导致实际方法被调用
- 依赖项未正确 Mock

### 6. 环境变量缺失

**现象**：
- `pydantic-settings` 配置加载失败
- 必需的环境变量未设置
- 测试环境配置不正确

### 7. 依赖未安装

**现象**：
- `ModuleNotFoundError`
- 依赖包版本不兼容
- `pip install -e ".[dev]"` 未执行

### 8. 认证/权限问题

**现象**：
- 运营接口权限检查测试失败
- JWT Token 验证失败
- `ops:vote-cycles:write` scope 校验不通过

## 解决方案

### 1. 数据库连接失败

```bash
# 启动本地开发数据库
cd infra && docker compose -f docker-compose.dev.yml up -d

# 等待数据库就绪
sleep 10

# 确认数据库连接正常
docker compose -f docker-compose.dev.yml ps

# 重新运行测试
cd services/ops && pytest
```

### 2. 测试数据问题

```bash
# 查看具体失败的测试用例
cd services/ops && pytest -v --tb=short

# 清理测试环境后重新运行
cd services/ops && pytest --cache-clear

# 单独运行失败的测试，检查数据准备逻辑
cd services/ops && pytest tests/test_dashboard.py::test_specific_case -xvs
```

### 3. 断言失败

```bash
# 查看详细断言信息
cd services/ops && pytest -v --tb=long

# 运行特定测试文件定位问题
cd services/ops && pytest tests/test_dashboard.py -v

# 检查数据聚合逻辑
# 文件：services/ops/app/repositories/dashboard_repo.py
# 确认数据聚合和统计逻辑是否正确
```

### 4. 异步测试问题

```bash
# 检查 pytest-asyncio 配置
cd services/ops && pytest -v --tb=short -k "async"

# 确认测试使用正确的 async 标记
# 检查 conftest.py 中的 event_loop fixture
# 文件：services/ops/tests/conftest.py
```

### 5. Mock 配置错误

```bash
# 运行带详细输出的测试
cd services/ops && pytest -xvs -k "mock"

# 检查 mock 路径是否正确
# 确认 Mock 的是使用处的引用，而非定义处
```

### 6. 环境变量缺失

```bash
# 检查环境变量模板
cat services/ops/.env.example

# 确认测试环境变量设置
cd services/ops && python -c "from app.core.config import settings; print(settings.model_dump())"

# 设置必需的环境变量后运行
export OPS_ENVIRONMENT=test
cd services/ops && pytest
```

### 7. 依赖未安装

```bash
# 安装开发依赖
cd services/ops && pip install -e ".[dev]"

# 验证依赖安装
cd services/ops && pip list | grep -E "pytest|sqlalchemy|fastapi"

# 重新运行测试
cd services/ops && pytest
```

### 8. 认证/权限问题

```bash
# 运行认证相关测试
cd services/ops && pytest -k "auth" -v

# 检查权限校验逻辑
# 文件：services/ops/app/core/auth.py
# 确认 ops scope 校验是否正确

# 检查测试中的 Token 生成逻辑
# 文件：services/ops/tests/conftest.py
```

## 手动执行

```bash
# 运行所有测试
cd services/ops && pytest

# 运行特定测试文件
cd services/ops && pytest tests/test_dashboard.py -v

# 运行特定测试函数
cd services/ops && pytest tests/test_ops_actions.py::test_create_action -v

# 查看详细输出
cd services/ops && pytest -xvs

# 查看覆盖率报告
cd services/ops && pytest --cov=app --cov-report=html
```

## 升级路径

| 级别 | 处理方式 |
|------|----------|
| 数据库问题 | 启动 Docker 数据库或检查连接字符串 |
| 测试数据问题 | 清理测试缓存或检查 fixture 数据 |
| 断言失败 | 检查对应的 repository 或 route 实现 |
| 异步问题 | 检查 conftest.py 中的 event_loop 配置 |
| Mock 问题 | 确认 mock 路径和返回值配置 |
| 环境变量问题 | 检查 .env 文件和 settings 配置 |
| 依赖问题 | 重新执行 pip install -e ".[dev]" |
| 权限问题 | 检查 auth.py 中的 scope 校验逻辑 |
| 无法解决 | 联系 Backend Agent |

## 相关链接

- 规范文档：`docs/30-api/api-overview.md`
- 测试文件：`services/ops/tests/`
- 门禁注册表：`docs/40-dev-loop/gate_registry.yaml`

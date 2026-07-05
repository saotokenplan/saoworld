# Runbook: Gateway Service Unit Tests (G-UNIT-009)

> gate_id: G-UNIT-009
> gate_name: Service Unit Tests (gateway)
> gate_type: unit
> owner: Backend Agent

## 门禁概述

Gateway Service Unit Tests 是 gateway-service 的单元测试门禁，验证 API 网关核心功能：JWT 认证中间件、令牌桶限流、请求追踪、反向代理路由等。

**门禁名称**：Service Unit Tests (gateway)
**门禁 ID**：G-UNIT-009
**门禁类型**：unit
**触发条件**：
- 路径：`services/gateway/**`
- 触发：`on_pr`
**覆盖的风险类型**：regression, security

**执行命令**：
```bash
cd services/gateway && pytest
```

**预期耗时**：45 秒

## 常见失败原因

以下按发生频率从高到低排序：

### 1. 数据库连接失败

**现象**：
- `sqlalchemy.exc.OperationalError`
- 测试数据库未启动或连接字符串错误
- Redis 连接失败（限流依赖）

### 2. 测试数据问题

**现象**：
- `IntegrityError: UNIQUE constraint failed`
- 测试 fixture 数据冲突或清理不彻底
- 限流计数器状态与预期不一致

### 3. 断言失败

**现象**：
- `AssertionError`
- JWT 认证结果不符合预期
- 限流阈值计算结果与预期不符
- 路由转发目标与预期不一致

### 4. 异步测试问题

**现象**：
- 异步测试超时
- `asyncio` 事件循环相关错误
- HTTP 客户端会话未正确关闭

### 5. Mock 配置错误

**现象**：
- Mock 对象返回值不正确
- Mock 路径配置错误导致实际方法被调用
- 下游服务依赖未正确 Mock

### 6. 环境变量缺失

**现象**：
- `pydantic-settings` 配置加载失败
- 必需的环境变量未设置
- JWT 密钥或 Redis 连接配置缺失

### 7. 依赖未安装

**现象**：
- `ModuleNotFoundError`
- 依赖包版本不兼容
- `pip install -e ".[dev]"` 未执行

### 8. 认证/权限问题

**现象**：
- JWT Token 签名验证测试失败
- 无效 Token 被放行或有效 Token 被拒绝
- Scope 权限校验逻辑不正确

## 解决方案

### 1. 数据库连接失败

```bash
# 启动本地开发基础设施（PostgreSQL + Redis）
cd infra && docker compose -f docker-compose.dev.yml up -d

# 等待服务就绪
sleep 10

# 确认服务运行状态
docker compose -f docker-compose.dev.yml ps

# 重新运行测试
cd services/gateway && pytest
```

### 2. 测试数据问题

```bash
# 查看具体失败的测试用例
cd services/gateway && pytest -v --tb=short

# 清理测试环境后重新运行
cd services/gateway && pytest --cache-clear

# 单独运行失败的测试，检查数据准备逻辑
cd services/gateway && pytest tests/test_auth.py::test_specific_case -xvs
```

### 3. 断言失败

```bash
# 查看详细断言信息
cd services/gateway && pytest -v --tb=long

# 运行特定测试文件定位问题
cd services/gateway && pytest tests/test_limiter.py -v

# 检查限流逻辑实现
# 文件：services/gateway/app/core/limiter.py
# 确认令牌桶限流配置和计算逻辑是否正确
```

### 4. 异步测试问题

```bash
# 检查 pytest-asyncio 配置
cd services/gateway && pytest -v --tb=short -k "async"

# 确认测试使用正确的 async 标记
# 检查 conftest.py 中的 event_loop fixture
# 文件：services/gateway/tests/conftest.py
```

### 5. Mock 配置错误

```bash
# 运行带详细输出的测试
cd services/gateway && pytest -xvs -k "mock"

# 检查 mock 路径是否正确
# 确认 Mock 的是使用处的引用，而非定义处
# 特别注意 httpx.AsyncClient 的 mock 配置
```

### 6. 环境变量缺失

```bash
# 检查环境变量模板
cat services/gateway/.env.example

# 确认测试环境变量设置
cd services/gateway && python -c "from app.core.config import settings; print(settings.model_dump())"

# 设置必需的环境变量后运行
export GATEWAY_ENVIRONMENT=test
cd services/gateway && pytest
```

### 7. 依赖未安装

```bash
# 安装开发依赖
cd services/gateway && pip install -e ".[dev]"

# 验证依赖安装
cd services/gateway && pip list | grep -E "pytest|fastapi|httpx|redis"

# 重新运行测试
cd services/gateway && pytest
```

### 8. 认证/权限问题

```bash
# 运行认证相关测试
cd services/gateway && pytest -k "auth" -v

# 检查 JWT 验证逻辑
# 文件：services/gateway/app/core/auth.py
# 确认 JWT 签名验证和 scope 校验是否正确

# 检查测试中的 Token 生成逻辑
# 文件：services/gateway/tests/conftest.py
```

## 手动执行

```bash
# 运行所有测试
cd services/gateway && pytest

# 运行特定测试文件
cd services/gateway && pytest tests/test_auth.py -v

# 运行特定测试函数
cd services/gateway && pytest tests/test_proxy.py::test_route_mapping -v

# 查看详细输出
cd services/gateway && pytest -xvs

# 查看覆盖率报告
cd services/gateway && pytest --cov=app --cov-report=html
```

## 升级路径

| 级别 | 处理方式 |
|------|----------|
| 数据库问题 | 启动 Docker 数据库/Redis 或检查连接字符串 |
| 测试数据问题 | 清理测试缓存或检查 fixture 数据 |
| 断言失败 | 检查对应的 middleware 或 route 实现 |
| 异步问题 | 检查 conftest.py 中的 event_loop 配置 |
| Mock 问题 | 确认 mock 路径和返回值配置 |
| 环境变量问题 | 检查 .env 文件和 settings 配置 |
| 依赖问题 | 重新执行 pip install -e ".[dev]" |
| 安全/权限问题 | 检查 auth.py 中的 JWT 验证和 scope 校验 |
| 无法解决 | 联系 Backend Agent |

## 相关链接

- 规范文档：`docs/30-api/api-overview.md`
- 测试文件：`services/gateway/tests/`
- 门禁注册表：`docs/40-dev-loop/gate_registry.yaml`

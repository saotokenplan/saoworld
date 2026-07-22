# Runbook: Vote Service Unit Tests (G-UNIT-001)

> gate_id: G-UNIT-001
> gate_name: Service Unit Tests (vote)
> gate_type: unit
> owner: Backend Agent

## 门禁概述

Vote Service Unit Tests 是 vote-service 的单元测试门禁，验证投票周期管理、投票提交、结算逻辑、幂等处理等核心功能。

**门禁信息**：
- 名称：Service Unit Tests (vote)
- ID：G-UNIT-001
- 类型：unit
- 触发条件：`services/vote/**` 路径变更时，在 PR 上自动触发
- 覆盖风险类型：regression, data-integrity

**执行命令**：
```bash
cd services/vote && pytest
```

**预期耗时**：60 秒

## 常见失败原因

按发生频率从高到低排序：

1. **数据库连接失败** - 测试数据库未启动或连接字符串错误
2. **测试数据问题** - 测试数据冲突、唯一约束违反、fixture 数据不完整
3. **断言失败** - 业务逻辑变更导致预期结果不匹配
4. **异步测试问题** - 异步数据库操作未正确等待、事件循环配置错误
5. **Mock 配置错误** - Mock 对象行为与实际不符、补丁作用域不正确
6. **环境变量缺失** - 必要的配置项未设置或使用了默认不安全值
7. **依赖未安装** - 开发依赖未完整安装、Python 版本不匹配

## 解决方案

### 1. 数据库连接失败

**现象**：
- `sqlalchemy.exc.OperationalError`
- `asyncpg.exceptions.CannotConnectNowError`
- 测试启动时直接报数据库连接错误

**解决步骤**：
```bash
# 步骤1：启动本地开发数据库
cd infra && docker compose -f docker-compose.dev.yml up -d

# 步骤2：等待数据库就绪（约10秒）
sleep 10

# 步骤3：确认数据库容器运行正常
docker compose -f docker-compose.dev.yml ps

# 步骤4：检查数据库连接配置
cd services/vote && cat .env | grep DATABASE_URL

# 步骤5：执行数据库迁移
cd services/vote && alembic upgrade head

# 步骤6：重新运行测试
cd services/vote && pytest
```

### 2. 测试数据问题

**现象**：
- `IntegrityError: UNIQUE constraint failed`
- 测试中创建了重复的投票周期或候选项
- fixture 数据加载失败

**解决步骤**：
```bash
# 步骤1：查看具体失败的测试用例
cd services/vote && pytest -v --tb=short

# 步骤2：使用 -x 选项在第一个失败处停止，便于定位
cd services/vote && pytest -x -v

# 步骤3：清理测试数据库（使用 SQLite 内存库时无需此步）
# 如使用独立测试库，可执行：
cd services/vote && alembic downgrade base && alembic upgrade head

# 步骤4：检查 fixture 数据，确保 ID 唯一且不冲突
# 文件：services/vote/tests/conftest.py

# 步骤5：重新运行测试
cd services/vote && pytest
```

### 3. 断言失败

**现象**：
- `AssertionError` - 预期结果与实际结果不匹配
- 状态码、返回字段、计票结果等不符合预期

**解决步骤**：
```bash
# 步骤1：查看详细的失败信息
cd services/vote && pytest -v --tb=long

# 步骤2：运行单个失败的测试用例，便于调试
cd services/vote && pytest tests/test_vote_flow.py::test_submit_vote_success -v

# 步骤3：检查对应的业务逻辑实现
# 投票提交逻辑：services/vote/app/api/routes.py
# 投票结算逻辑：services/vote/app/repositories/vote_repo.py
# 状态机定义：services/vote/app/domain/models.py

# 步骤4：确认状态机路径（draft → scheduled → open → closed → finalized）
# 确认投票权重范围（0 < weight <= 10.0）
# 确认一人一票约束（UNIQUE vote_cycle_id, player_id）

# 步骤5：修复代码或测试，重新运行
cd services/vote && pytest
```

### 4. 异步测试问题

**现象**：
- `asyncio.TimeoutError`
- 测试挂起超时
- 数据库会话未正确关闭

**解决步骤**：
```bash
# 步骤1：确认 pytest-asyncio 已正确安装
cd services/vote && pip list | grep pytest-asyncio

# 步骤2：检查 pyproject.toml 中的 asyncio_mode 配置
cd services/vote && grep -A2 "asyncio_mode" pyproject.toml

# 步骤3：确保测试函数使用 async def 并正确 await
# 检查：tests/test_vote_flow.py

# 步骤4：检查数据库会话是否正确获取和关闭
# 检查：tests/conftest.py 中的 fixture 定义

# 步骤5：重新运行测试
cd services/vote && pytest
```

### 5. Mock 配置错误

**现象**：
- Mock 的方法返回值不正确
- 补丁作用域错误导致 Mock 未生效
- Mock 调用次数断言失败

**解决步骤**：
```bash
# 步骤1：查看失败的 Mock 相关测试
cd services/vote && pytest -k "mock" -v --tb=short

# 步骤2：检查 unittest.mock.patch 的目标路径是否正确
# 注意：patch 的目标应该是"使用处"而非"定义处"

# 步骤3：确认 pytest-mock 或 unittest.mock 的使用方式
# 文件：services/vote/tests/ 下的相关测试文件

# 步骤4：修复 Mock 配置后重新运行
cd services/vote && pytest
```

### 6. 环境变量缺失

**现象**：
- `ValidationError` - pydantic-settings 配置加载失败
- 使用了默认值 `change-me-in-production` 导致警告或错误
- 测试环境配置不正确

**解决步骤**：
```bash
# 步骤1：检查 .env 文件是否存在
cd services/vote && ls -la .env

# 步骤2：如不存在，从模板复制
cd services/vote && cp .env.example .env

# 步骤3：设置测试环境
export VOTE_ENVIRONMENT=test

# 步骤4：检查所有必需的配置项
# 参考：services/vote/app/core/config.py

# 步骤5：重新运行测试
cd services/vote && pytest
```

### 7. 依赖未安装

**现象**：
- `ModuleNotFoundError` - 找不到模块
- `ImportError` - 导入失败
- Python 版本不兼容

**解决步骤**：
```bash
# 步骤1：检查 Python 版本（要求 >= 3.11）
python --version

# 步骤2：安装开发依赖
cd services/vote && pip install -e ".[dev]"

# 步骤3：确认所有依赖已安装
cd services/vote && pip list

# 步骤4：重新运行测试
cd services/vote && pytest
```

## 手动执行

```bash
# 运行所有测试
cd services/vote && pytest

# 运行特定测试文件
cd services/vote && pytest tests/test_vote_flow.py -v

# 运行特定测试函数
cd services/vote && pytest tests/test_vote_flow.py::test_submit_vote_success -v

# 运行包含特定关键词的测试
cd services/vote && pytest -k "idempotent" -v

# 在第一个失败处停止，便于调试
cd services/vote && pytest -x -v

# 查看详细失败信息
cd services/vote && pytest -v --tb=long

# 查看覆盖率报告
cd services/vote && pytest --cov=app --cov-report=html

# 运行测试并生成 JUnit XML 报告
cd services/vote && pytest --junitxml=test-results.xml
```

## 升级路径

| 级别 | 处理方式 | 负责人 |
|------|----------|--------|
| L1 - 环境问题 | 启动 Docker 数据库、检查连接字符串、安装依赖 | 开发者自行解决 |
| L2 - 数据问题 | 清理测试数据、检查 fixture 唯一性约束 | 开发者自行解决 |
| L3 - 逻辑错误 | 检查对应的 repository 或 route 实现，对照状态机规范 | 后端开发 |
| L4 - 测试框架问题 | 异步测试配置、Mock 配置、pytest 插件问题 | Backend Agent |
| L5 - 无法解决 | 提交 Issue，附带测试输出和 trace_id | Backend Agent / 架构师 |

**升级流程**：
1. 先尝试 L1-L3 级别的自助解决方案
2. 如 30 分钟内无法解决，联系 Backend Agent
3. 如 Backend Agent 也无法解决，升级到架构师评审

## 相关链接

- 规范文档：`docs/30-api/api-overview.md`
- 数据库规范：`.trae/rules/11-database.md`
- 测试文件：`services/vote/tests/`
- 门禁注册表：`docs/40-dev-loop/gate_registry.yaml`

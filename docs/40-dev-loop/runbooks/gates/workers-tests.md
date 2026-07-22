# Runbook: Workers Unit Tests (G-UNIT-004)

> gate_id: G-UNIT-004
> gate_name: Workers Unit Tests
> gate_type: unit
> owner: Backend Agent

## 门禁概述

Workers Unit Tests 是 Celery Workers 的单元测试门禁，验证异步任务执行、内容审核、内容打包、发布回滚、事件发布等核心功能。

**门禁信息**：
- 名称：Workers Unit Tests
- ID：G-UNIT-004
- 类型：unit
- 触发条件：`workers/**` 或 `tools/content_check/**` 路径变更时，在 PR 上自动触发
- 覆盖风险类型：regression, data-integrity

**执行命令**：
```bash
cd workers && pytest
```

**预期耗时**：45 秒

## 常见失败原因

按发生频率从高到低排序：

1. **Redis 连接失败** - Redis 未启动或连接字符串错误（Celery Broker/Backend）
2. **测试数据问题** - 任务参数数据冲突、fixture 数据不完整
3. **断言失败** - 任务执行结果、审核逻辑、状态流转等不匹配
4. **异步测试问题** - Celery 任务异步执行、事件循环配置错误
5. **Mock 配置错误** - Mock 对象行为与实际不符、外部服务补丁不正确
6. **环境变量缺失** - 必要的配置项未设置或使用了默认值
7. **依赖未安装** - 开发依赖未完整安装、Python 版本不匹配

## 解决方案

### 1. Redis 连接失败

**现象**：
- `redis.exceptions.ConnectionError`
- `kombu.exceptions.OperationalError`
- Celery 应用初始化失败
- 测试启动时报 Broker 连接错误

**解决步骤**：
```bash
# 步骤1：启动本地开发基础设施（包含 Redis）
cd infra && docker compose -f docker-compose.dev.yml up -d

# 步骤2：等待 Redis 就绪（约5秒）
sleep 5

# 步骤3：确认 Redis 容器运行正常
docker compose -f docker-compose.dev.yml ps

# 步骤4：测试 Redis 连接
redis-cli ping

# 步骤5：检查 Redis 连接配置
cd workers && cat .env | grep REDIS

# 步骤6：设置环境变量
export REDIS_URL=redis://localhost:6379/0

# 步骤7：重新运行测试
cd workers && pytest
```

### 2. 测试数据问题

**现象**：
- 任务输入数据格式错误
- fixture 加载的测试内容数据不完整
- 测试用例间数据相互干扰

**解决步骤**：
```bash
# 步骤1：查看具体失败的测试用例
cd workers && pytest -v --tb=short

# 步骤2：使用 -x 选项在第一个失败处停止，便于定位
cd workers && pytest -x -v

# 步骤3：检查 fixture 数据
# 文件：workers/tests/conftest.py
# 确认任务参数、模拟内容数据是否完整

# 步骤4：检查测试隔离
# 确认每个测试用例使用独立的测试数据，避免相互影响

# 步骤5：重新运行测试
cd workers && pytest
```

### 3. 断言失败

**现象**：
- `AssertionError` - 任务执行结果与预期不符
- 内容审核四项检查结果不正确
- 任务状态流转不符合预期
- 事件发布内容或时机不正确

**解决步骤**：
```bash
# 步骤1：查看详细的失败信息
cd workers && pytest -v --tb=long

# 步骤2：运行单个失败的测试用例，便于调试
cd workers && pytest tests/test_content_review.py::test_review_flow -v

# 步骤3：检查对应的任务实现
# 内容审核任务：workers/tasks/content_review.py
# 内容打包任务：workers/tasks/content_package.py
# 发布回滚任务：workers/tasks/release_rollback.py
# HTTP 客户端：workers/clients/http_client.py

# 步骤4：确认四项内容检查（一致性、数值、安全、重复度）
# 确认任务状态流转
# 确认事件发布格式和时机

# 步骤5：修复代码或测试，重新运行
cd workers && pytest
```

### 4. 异步测试问题

**现象**：
- `asyncio.TimeoutError`
- 测试挂起超时
- Celery 任务结果未正确等待
- 事件循环配置错误

**解决步骤**：
```bash
# 步骤1：确认 pytest-asyncio 已正确安装
cd workers && pip list | grep pytest-asyncio

# 步骤2：检查 pyproject.toml 中的 asyncio_mode 配置
cd workers && grep -A2 "asyncio_mode" pyproject.toml

# 步骤3：确认 Celery 测试配置
# 检查是否使用了 task_always_eager 或类似的测试模式
# 文件：workers/tests/conftest.py

# 步骤4：确保异步测试函数正确使用 async/await
# 检查：workers/tests/ 下的相关测试文件

# 步骤5：重新运行测试
cd workers && pytest
```

### 5. Mock 配置错误

**现象**：
- Mock 的外部服务调用返回值不正确
- 补丁作用域错误导致 Mock 未生效
- HTTP 客户端 Mock 行为与实际不符
- Mock 调用次数断言失败

**解决步骤**：
```bash
# 步骤1：查看失败的 Mock 相关测试
cd workers && pytest -k "mock" -v --tb=short

# 步骤2：检查 unittest.mock.patch 的目标路径是否正确
# 注意：patch 的目标应该是"使用处"而非"定义处"

# 步骤3：检查 HTTP 客户端 Mock
# 文件：workers/clients/http_client.py
# 确认 Mock 的方法和路径正确

# 步骤4：确认 pytest-mock 或 unittest.mock 的使用方式
# 文件：workers/tests/ 下的相关测试文件

# 步骤5：修复 Mock 配置后重新运行
cd workers && pytest
```

### 6. 环境变量缺失

**现象**：
- `ValidationError` - 配置加载失败
- Celery Broker/Backend URL 未配置
- 外部服务 API 地址未设置
- 测试环境配置不正确

**解决步骤**：
```bash
# 步骤1：检查 .env 文件是否存在
cd workers && ls -la .env

# 步骤2：如不存在，从模板复制
cd workers && cp .env.example .env

# 步骤3：设置测试环境变量
export WORKERS_ENVIRONMENT=test
export REDIS_URL=redis://localhost:6379/0

# 步骤4：检查所有必需的配置项
# 参考：workers/config.py 或相关配置文件

# 步骤5：重新运行测试
cd workers && pytest
```

### 7. 依赖未安装

**现象**：
- `ModuleNotFoundError` - 找不到模块
- `ImportError` - 导入失败
- Python 版本不兼容
- Celery 或 Redis 相关包缺失

**解决步骤**：
```bash
# 步骤1：检查 Python 版本（要求 >= 3.11）
python --version

# 步骤2：安装开发依赖
cd workers && pip install -e ".[dev]"

# 步骤3：确认所有依赖已安装
cd workers && pip list | grep -E "celery|redis|pytest"

# 步骤4：重新运行测试
cd workers && pytest
```

## 手动执行

```bash
# 运行所有测试
cd workers && pytest

# 运行特定测试文件
cd workers && pytest tests/test_content_review.py -v

# 运行特定测试函数
cd workers && pytest tests/test_content_review.py::test_review_task_success -v

# 运行包含特定关键词的测试
cd workers && pytest -k "review or package" -v

# 在第一个失败处停止，便于调试
cd workers && pytest -x -v

# 查看详细失败信息
cd workers && pytest -v --tb=long

# 查看覆盖率报告
cd workers && pytest --cov=. --cov-report=html

# 运行测试并生成 JUnit XML 报告
cd workers && pytest --junitxml=test-results.xml
```

## 升级路径

| 级别 | 处理方式 | 负责人 |
|------|----------|--------|
| L1 - 环境问题 | 启动 Docker Redis、检查连接字符串、安装依赖 | 开发者自行解决 |
| L2 - 数据问题 | 检查 fixture 数据完整性、测试隔离性 | 开发者自行解决 |
| L3 - 逻辑错误 | 检查任务实现、审核逻辑、状态流转 | 后端开发 |
| L4 - 测试框架问题 | Celery 测试配置、异步测试、Mock 配置 | Backend Agent |
| L5 - 无法解决 | 提交 Issue，附带测试输出和 trace_id | Backend Agent / 架构师 |

**升级流程**：
1. 先尝试 L1-L3 级别的自助解决方案
2. 如 30 分钟内无法解决，联系 Backend Agent
3. 如 Backend Agent 也无法解决，升级到架构师评审

## 相关链接

- 规范文档：`docs/20-specs/async-tasks-and-events/`
- 发布与回滚规范：`.trae/rules/42-release-rollback.md`
- 测试文件：`workers/tests/`
- 门禁注册表：`docs/40-dev-loop/gate_registry.yaml`

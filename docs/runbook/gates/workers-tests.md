# Runbook: Workers Unit Tests (G-UNIT-004)

> gate_id: G-UNIT-004
> gate_name: Workers Unit Tests
> gate_type: unit
> owner: Backend Agent

## 门禁概述

Workers Unit Tests 是 Celery Workers 的单元测试门禁，验证异步任务、内容审核、打包、发布等功能。

**触发条件**：
- 路径：`workers/**`, `tools/content_check/**`
- 触发：`on_pr`

**执行命令**：
```bash
cd workers && pytest
```

**预期耗时**：45 秒

## 常见失败原因

### 1. Redis 连接失败

**现象**：
- `redis.exceptions.ConnectionError`
- Redis 未启动

**解决方案**：
```bash
# 启动本地开发基础设施
cd infra && docker compose -f docker-compose.dev.yml up -d

# 等待 Redis 就绪
sleep 5

# 重新运行测试
cd workers && pytest
```

### 2. Celery 应用初始化失败

**现象**：
- 测试无法加载 Celery 应用
- 配置错误

**解决方案**：
```bash
# 检查 Celery 配置
# 文件：workers/config.py
# 确认 BROKER_URL 和 BACKEND_URL 是否正确

# 设置环境变量
export REDIS_URL=redis://localhost:6379/0

# 重新运行测试
cd workers && pytest
```

### 3. 内容审核检查失败

**现象**：
- content_review 任务测试失败
- 四项检查（一致性、数值、安全、重复度）未通过

**解决方案**：
```bash
# 运行内容审核相关测试
cd workers && pytest -k "review" -v

# 检查审核逻辑
# 文件：workers/tasks/content_review.py
# 确认四项检查工具调用是否正确
```

### 4. API 路径不匹配

**现象**：
- Workers 调用后端服务 API 失败
- 路径或方法不匹配

**解决方案**：
```bash
# 运行相关测试
cd workers && pytest -v --tb=short

# 检查 API 路径配置
# 文件：workers/clients/http_client.py
# 确认路径与后端服务实际路径一致
```

## 手动执行

```bash
# 运行所有测试
cd workers && pytest

# 运行特定测试文件
cd workers && pytest tests/test_content_review.py -v

# 查看覆盖率报告
cd workers && pytest --cov=. --cov-report=html
```

## 升级路径

| 级别 | 处理方式 |
|------|----------|
| Redis 问题 | 启动 Docker Redis 或检查连接字符串 |
| Celery 配置 | 检查 config.py 和环境变量 |
| 审核逻辑 | 检查 content_review.py 和检查工具 |
| API 路径 | 确认 http_client.py 中的路径与后端一致 |
| 无法解决 | 联系 Backend Agent |

## 相关链接

- 规范文档：`docs/20-specs/async-tasks-and-events/`
- 测试文件：`workers/tests/`
- 门禁注册表：`docs/40-dev-loop/gate_registry.yaml`
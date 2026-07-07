# workers/ - 异步任务与事件总线

Celery 异步任务 Worker 与基于 Redis Pub/Sub 的事件总线，负责长耗时任务（内容生成、审核、打包、发布、回滚、门禁扫描）的异步执行和服务间事件通信。

## 目录结构

```
workers/
├── clients/            # 服务客户端
│   ├── auth_client.py      # 认证客户端
│   ├── db_client.py        # 数据库客户端
│   └── http_client.py      # HTTP 客户端
├── events/             # 事件总线
│   ├── event_bus.py        # 事件总线核心
│   ├── event_publisher.py  # 事件发布者
│   ├── event_subscriber.py # 事件订阅者（含重试+死信队列）
│   ├── handlers.py         # 事件处理器（链路串联）
│   └── schemas.py          # 事件消息 Schema
├── tasks/              # Celery 任务定义
│   ├── content_generation.py # AI 内容生成任务
│   ├── content_review.py     # 内容审核任务（一致性/数值/安全/重复度）
│   ├── content_packaging.py  # 内容包打包任务
│   ├── content_release.py    # 内容发布与回滚任务
│   ├── gate_scan.py          # 每日门禁扫描任务
│   └── scheduled_tasks.py    # Celery Beat 定时任务
├── utils/              # 工具模块
│   ├── logging.py          # 结构化日志配置
│   ├── metrics.py          # Prometheus 指标
│   └── tracing.py          # 链路追踪工具
├── tests/              # 测试用例（29 个）
├── __init__.py
├── celery_app.py       # Celery 应用入口
├── celery_beat_schedule.py # Beat 定时任务配置
├── config.py           # 配置管理（pydantic-settings）
├── pyproject.toml      # 项目配置与依赖
├── .env.example        # 环境变量模板
└── Dockerfile          # Docker 镜像构建
```

## 核心功能

### 异步任务（Celery）

| 任务 | 队列 | 说明 |
|------|------|------|
| `generate_content_batch` | generation | AI 批量内容生成 |
| `run_world_consistency_review` | review | 世界一致性审核 |
| `run_balance_review` | review | 数值平衡审核 |
| `package_content_batch` | packaging | 内容包打包 |
| `release_content_package` | release | 内容灰度/全量发布 |
| `rollback_content_package` | release | 内容包回滚 |
| `daily_gate_scan` | gate | 每日门禁扫描 |

### 事件总线（Redis Pub/Sub）

基于 Redis Pub/Sub 实现的服务间事件通信，支持指数退避重试和死信队列。

**核心事件类型**：

| 事件 | 触发时机 | 处理器 |
|------|---------|--------|
| `vote.cycle.closed` | 投票周期关闭 | - |
| `vote.result.finalized` | 投票结果结算完成 | 触发内容生成 |
| `generation.request.created` | 生成请求创建 | - |
| `generation.batch.completed` | 批量生成完成 | 触发审核流程 |
| `review.batch.completed` | 批量审核完成 | 触发布打包 |
| `content.package.released` | 内容包发布 | - |
| `content.package.rolled_back` | 内容包回滚 | - |

**重试策略**：指数退避（最大 3 次重试，2^n * base_delay），超过重试次数进入 `event.dead_letter` 死信通道。

### 定时任务（Celery Beat）

| 任务 | 频率 | 说明 |
|------|------|------|
| `daily-gate-scan` | 每日 03:00 | 每日门禁扫描 |
| `hourly-metrics-sync` | 每小时 | 指标同步 |
| `daily-content-review` | 每日 02:00 | 每日内容审核 |

## 与后端服务的集成

- **vote-service**：投票结算后发布 `vote.result.finalized` 事件
- **generation-service**：生成完成后发布 `generation.batch.completed` 事件
- **review-service**：审核完成后发布 `review.batch.completed` 事件
- **content-service**：发布/回滚后发布 `content.package.released` / `content.package.rolled_back` 事件
- 事件处理器串联完整链路：投票结算 → 内容生成 → 内容审核 → 内容打包 → 内容发布

## 快速开始

### 环境要求

- Python >= 3.11
- Redis 7（Broker + 结果后端 + 事件总线）
- PostgreSQL 16（业务数据）

### 安装依赖

```bash
cd workers
pip install -e ".[dev]"
```

### 启动 Worker

```bash
# 启动 worker（监听所有队列）
celery -A workers.celery_app worker --loglevel=info

# 启动 Beat 定时任务调度器
celery -A workers.celery_app beat --loglevel=info
```

### 运行测试

```bash
cd workers
python -m pytest -q
```

**测试覆盖**：29 个测试用例（7 个 Redis 环境限制），覆盖：
- Celery 应用配置
- 内容生成任务
- 内容打包任务
- 内容发布任务
- 内容审核任务
- 门禁扫描任务
- 定时任务
- 事件总线（发布/订阅/重试/死信队列）

### 代码质量检查

```bash
cd workers
ruff check .
```

## 配置

使用 `pydantic-settings` 从环境变量加载配置，环境变量前缀 `WORKER_`。

**关键配置项**：

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| broker_url | WORKER_BROKER_URL | redis://localhost:6379/0 | Celery Broker |
| result_backend | WORKER_RESULT_BACKEND | redis://localhost:6379/1 | 结果后端 |
| database_url | WORKER_DATABASE_URL | postgresql+asyncpg://... | 数据库连接 |
| log_level | WORKER_LOG_LEVEL | INFO | 日志级别 |

更多配置见 `.env.example`。

## Next Steps

- 完善任务失败告警与自动重试策略
- 增加任务执行进度追踪
- 接入真实 AI 生成服务（当前为模拟实现）
- 完善死信队列告警与人工处理流程

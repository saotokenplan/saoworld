# 重试策略与死信队列规范

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 适用范围

本文档定义异步任务和事件的重试策略、死信队列（DLQ）机制、错误分类和幂等性要求。所有异步任务实现必须严格遵循本规范。

## 错误分类

所有异步错误分为两大类：**可重试错误**和**不可重试错误**。

### 可重试错误（Retryable）

临时故障，重试后可能成功：

| 错误类型 | 示例 | 说明 |
|----------|------|------|
| 网络超时 | HTTP 连接超时、读取超时 | 下游服务暂时不可达 |
| 5xx 错误 | 500 Internal Server Error、502 Bad Gateway、503 Service Unavailable | 服务端临时故障 |
| 数据库连接失败 | 连接池耗尽、数据库重启 | 数据库暂时不可用 |
| 缓存连接失败 | Redis 连接超时、连接被拒绝 | 缓存暂时不可用 |
| 限流触发 | 429 Too Many Requests | 被下游限流，稍后重试 |
| 资源锁冲突 | 行锁等待超时、乐观锁冲突 | 并发冲突，重试可解决 |

### 不可重试错误（Non-retryable）

逻辑错误，重试必然失败：

| 错误类型 | 示例 | 说明 |
|----------|------|------|
| 4xx 错误 | 400 Bad Request、401 Unauthorized、403 Forbidden、404 Not Found | 请求参数错误或权限不足 |
| 数据校验失败 | 字段格式错误、必填字段缺失 | 输入数据不合法 |
| 状态机冲突 | 状态迁移不合法、重复操作 | 业务状态不允许 |
| 资源不存在 | 内容包不存在、生成请求不存在 | 资源 ID 无效 |
| 配置错误 | 模板不存在、规则版本不兼容 | 配置问题需人工修复 |
| 安全违规 | 签名验证失败、token 无效 | 安全问题，禁止重试 |

---

## 重试策略

### 通用重试配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `max_retries` | 3 | 最大重试次数 |
| `retry_backoff` | 指数退避 | 退避策略 |
| `backoff_base` | 2 秒 | 退避基数 |
| `backoff_max` | 300 秒 | 最大退避时间 |
| `jitter` | 启用 | 抖动，避免惊群效应 |

### 指数退避公式

```
wait_time = min(backoff_base * (2 ^ retry_count), backoff_max)
wait_time = wait_time * (0.5 + random() * 0.5)  # 加抖动
```

重试等待时间示例：

| 重试次数 | 基础等待时间 | 范围（加抖动） |
|----------|-------------|----------------|
| 第 1 次 | 2 秒 | 1 - 2 秒 |
| 第 2 次 | 4 秒 | 2 - 4 秒 |
| 第 3 次 | 8 秒 | 4 - 8 秒 |

### 各任务重试配置

| 任务 | 最大重试 | 退避基数 | 说明 |
|------|----------|----------|------|
| generate_content_batch | 3 | 2 秒 | 生成任务失败可重试 |
| run_world_consistency_review | 3 | 2 秒 | 审核任务失败可重试 |
| run_balance_review | 3 | 2 秒 | 审核任务失败可重试 |
| package_content_batch | 3 | 2 秒 | 打包任务失败可重试 |
| release_content_package | 3 | 2 秒 | 发布任务失败可重试 |
| rollback_content_package | 3 | 2 秒 | 回滚任务失败可重试 |
| daily_gate_scan | 3 | 2 秒 | 门禁扫描失败可重试 |

---

## 死信队列（DLQ）

### 什么是死信队列

死信队列（Dead Letter Queue，DLQ）是用于存放"无法正常处理"的消息的特殊队列。当消息重试次数达到上限仍然失败时，会被移到 DLQ 中，等待人工介入处理。

### DLQ 触发条件

满足以下任一条件的消息进入 DLQ：

1. **重试次数耗尽**：重试次数达到 `max_retries` 仍然失败
2. **格式错误**：消息格式无法解析，根本无法开始处理
3. **过期消息**：消息超过 TTL（Time-To-Live）仍未被消费
4. **队列溢出**：队列长度超过最大限制，新消息被丢弃到 DLQ

### DLQ 消息结构

DLQ 中的消息除了原始消息内容外，还包含死信元数据：

| 字段 | 类型 | 说明 |
|------|------|------|
| `original_message` | object | 原始消息内容 |
| `dlq_reason` | string | 进入 DLQ 的原因 |
| `dlq_timestamp` | string | 进入 DLQ 的时间 |
| `retry_count` | int | 已重试次数 |
| `last_error` | string | 最后一次错误信息 |
| `last_error_trace` | string | 最后一次错误栈追踪 |
| `original_queue` | string | 原始队列名 |

### DLQ 消息示例

```json
{
  "original_message": {
    "task": "generate_content_batch",
    "args": {
      "template_type": "npc",
      "count": 5,
      "trace_id": "trace_001"
    }
  },
  "dlq_reason": "max_retries_exceeded",
  "dlq_timestamp": "2026-07-04T12:00:00Z",
  "retry_count": 3,
  "last_error": "Connection refused to generation-service",
  "last_error_trace": "...",
  "original_queue": "generation"
}
```

### DLQ 处理流程

```
消息消费失败
    ↓
判断是否可重试
    ↓
可重试 → 重试（指数退避）
    ↓        ↓
重试成功  重试耗尽 → 进入 DLQ
    ↓                ↓
正常结束         人工介入处理
                     ↓
                修复后重新入队
```

### DLQ 管理要求

1. **监控告警**：DLQ 中有新消息时必须触发告警
2. **定期巡检**：每日巡检 DLQ 中的消息，及时处理
3. **重放机制**：支持将 DLQ 中的消息重新入队
4. **保留期限**：DLQ 消息至少保留 30 天
5. **审计记录**：DLQ 消息的处理必须有审计记录

---

## 幂等性要求

### 为什么需要幂等

- 消息队列采用"至少一次投递"（at-least-once）保证
- 同一任务可能被执行多次
- 消费者必须保证幂等，避免重复副作用

### 幂等键（Idempotency Key）

所有写操作必须支持幂等键：

| 场景 | 幂等键来源 | 说明 |
|------|------------|------|
| 任务执行 | `task_id` + 重试次数 | Celery 任务 ID 全局唯一 |
| 事件消费 | `event_id` | 事件 ID 全局唯一 |
| API 调用 | `Idempotency-Key` 请求头 | 客户端传入 |
| 投票提交 | `vote_cycle_id` + `player_id` | 业务唯一约束 |

### 幂等实现模式

#### 1. 数据库唯一约束

利用数据库 `UNIQUE` 约束实现幂等：

```python
# 示例：投票表的唯一约束
UNIQUE (vote_cycle_id, player_id)
```

#### 2. 状态机校验

通过状态机约束操作顺序：

```
draft → scheduled → open → closed → finalized
```

同一状态迁移重复执行时，直接返回成功（幂等）。

#### 3. 幂等记录表

对于复杂操作，使用专门的幂等记录表：

| 字段 | 说明 |
|------|------|
| `idempotency_key` | 幂等键（主键） |
| `status` | 处理状态：processing / succeeded / failed |
| `result` | 处理结果（JSON） |
| `created_at` | 创建时间 |
| `completed_at` | 完成时间 |

---

## 任务状态机

### 通用状态迁移

```
pending → processing → succeeded
                ↓
           failed_retryable → pending（重试）
                ↓
           failed_permanent → DLQ
```

### 状态定义

| 状态 | 说明 | 可迁移到 |
|------|------|----------|
| `pending` | 待处理 | `processing` |
| `processing` | 处理中 | `succeeded`、`failed_retryable`、`failed_permanent` |
| `succeeded` | 成功 | 终态 |
| `failed_retryable` | 可重试失败 | `pending`（重试） |
| `failed_permanent` | 不可重试失败 | 终态（进入 DLQ） |

---

## 熔断与降级

### 熔断器模式

当下游服务连续失败时，触发熔断，避免雪崩：

| 状态 | 说明 | 行为 |
|------|------|------|
| Closed | 闭合 | 正常请求，统计失败率 |
| Open | 打开 | 直接失败，不调用下游 |
| Half-Open | 半开 | 放行少量请求，探测服务是否恢复 |

### 熔断配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `failure_threshold` | 50% | 失败率阈值 |
| `window_size` | 30 秒 | 统计窗口 |
| `min_requests` | 10 | 最小请求数 |
| `open_timeout` | 60 秒 | 打开状态持续时间 |
| `half_open_max_calls` | 5 | 半开状态最大请求数 |

### 降级策略

触发熔断时的降级策略：

| 场景 | 降级策略 |
|------|----------|
| 内容生成 | 返回缓存内容，或推迟生成 |
| 内容审核 | 跳过自动审核，进入人工复核 |
| 发布操作 | 暂停发布，通知运营人员 |

---

## 与其他文档的关系

- [README.md](./README.md) - 规范总览
- [task-payloads.md](./task-payloads.md) - 异步任务 payload
- [event-schemas.md](./event-schemas.md) - 事件消息格式
- [trace-and-audit.md](./trace-and-audit.md) - 追踪与审计

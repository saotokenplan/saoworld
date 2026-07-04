# 全链路追踪与审计字段规范

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 适用范围

本文档定义异步任务和事件的全链路追踪规范、审计日志字段规范和结构化日志要求。所有异步任务和事件必须严格遵循本规范。

## 全链路追踪

### 追踪 ID 规范

#### trace_id（全链路追踪 ID）

- **格式**：`trace_<uuid4 hex前12位>`
- **示例**：`trace_a1b2c3d4e5f6`
- **生成时机**：用户请求进入网关时生成
- **传递方式**：通过 HTTP 头 `X-Trace-Id` 或消息 payload 中的 `trace_id` 字段透传
- **作用范围**：整个调用链，跨服务、跨异步任务

#### request_id（请求追踪 ID）

- **格式**：`req_<uuid4 hex前12位>`
- **示例**：`req_a1b2c3d4e5f6`
- **生成时机**：每个 HTTP 请求进入服务时生成
- **传递方式**：通过 HTTP 头 `X-Request-Id` 传递
- **作用范围**：单个 HTTP 请求

#### task_id（任务追踪 ID）

- **格式**：Celery 任务 UUID
- **示例**：`a1b2c3d4-e5f6-7890-abcd-ef1234567890`
- **生成时机**：任务创建时由 Celery 生成
- **作用范围**：单个异步任务

#### event_id（事件追踪 ID）

- **格式**：`evt_<uuid4 hex前12位>`
- **示例**：`evt_a1b2c3d4e5f6`
- **生成时机**：事件发布时生成
- **作用范围**：单个事件

### 追踪 ID 传递规则

1. **trace_id 必须始终透传**：从请求入口到异步任务，再到下游服务调用，trace_id 必须全程携带
2. **如果没有 trace_id，自动生成**：异步任务或事件处理时，如果没有传入 trace_id，必须自动生成
3. **日志必须绑定 trace_id**：所有日志输出必须包含 trace_id 字段
4. **审计日志必须包含 trace_id**：所有审计记录必须绑定 trace_id

### 追踪 ID 传递链路

```
用户请求
    ↓
Gateway（生成 trace_id + request_id）
    ↓
vote-service（透传 trace_id）
    ↓
发布事件 vote.result.finalized（携带 trace_id）
    ↓
generation-service 消费事件（透传 trace_id）
    ↓
调用 AI 生成 API（透传 trace_id）
    ↓
发布事件 generation.batch.completed（携带 trace_id）
    ↓
review-service 消费事件（透传 trace_id）
    ↓
...
```

---

## 审计日志规范

### 审计日志表结构

所有服务的 `audit_logs` 表结构必须一致：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `audit_log_id` | UUID | 是 | 审计日志 ID（主键） |
| `trace_id` | VARCHAR(64) | 是 | 全链路追踪 ID |
| `operator_id` | VARCHAR(64) | 是 | 操作人 ID |
| `operator_role` | VARCHAR(32) | 是 | 操作人角色：`player` / `ops` / `reviewer` / `system` |
| `action` | VARCHAR(64) | 是 | 操作类型 |
| `resource_type` | VARCHAR(32) | 是 | 资源类型 |
| `resource_id` | VARCHAR(64) | 是 | 资源 ID |
| `details_jsonb` | JSONB | 否 | 详细信息 |
| `ip_address` | VARCHAR(45) | 否 | IP 地址 |
| `user_agent` | VARCHAR(255) | 否 | User-Agent |
| `created_at` | TIMESTAMPTZ | 是 | 创建时间 |

### CHECK 约束

```sql
CHECK (operator_role IN ('player', 'ops', 'reviewer', 'system'))
```

### 索引

| 索引名 | 字段 | 说明 |
|--------|------|------|
| `audit_logs_trace_id_idx` | `trace_id` | 追踪 ID 索引 |
| `audit_logs_operator_id_idx` | `operator_id, created_at` | 操作人索引 |
| `audit_logs_resource_idx` | `resource_type, resource_id` | 资源索引 |
| `audit_logs_action_idx` | `action, created_at` | 操作类型索引 |

### 操作类型命名规范

操作类型使用点分隔的命名方式：`<domain>.<action>`

| 操作类型 | 说明 |
|----------|------|
| `vote.submitted` | 投票提交 |
| `vote.cycle.created` | 投票周期创建 |
| `vote.cycle.scheduled` | 投票周期计划 |
| `vote.cycle.opened` | 投票周期开放 |
| `vote.cycle.closed` | 投票周期关闭 |
| `vote.cycle.finalized` | 投票周期确认 |
| `content.package.created` | 内容包创建 |
| `content.package.released` | 内容包发布 |
| `content.package.rolled_back` | 内容包回滚 |
| `generation.batch_started` | 生成批次开始 |
| `generation.batch_completed` | 生成批次完成 |
| `review.consistency_completed` | 一致性审核完成 |
| `review.balance_completed` | 平衡审核完成 |
| `world.region.created` | 区域创建 |
| `world.region.status_updated` | 区域状态更新 |
| `player.created` | 玩家创建 |
| `player.updated` | 玩家更新 |
| `player.region_unlocked` | 玩家区域解锁 |

### 资源类型

| 资源类型 | 说明 |
|----------|------|
| `vote_cycle` | 投票周期 |
| `vote_candidate` | 投票候选项 |
| `vote` | 投票记录 |
| `content_package` | 内容包 |
| `release_record` | 发布记录 |
| `rollback_record` | 回滚记录 |
| `generation_request` | 生成请求 |
| `generated_object` | 生成对象 |
| `review_record` | 审核记录 |
| `region` | 区域 |
| `player` | 玩家 |
| `player_quest` | 玩家任务 |
| `player_region` | 玩家区域 |
| `ops_action` | 运营操作 |
| `ops_dashboard` | 运营仪表盘 |

---

## 结构化日志规范

### 日志库

必须使用 `structlog` 输出结构化 JSON 日志。

### 日志处理器配置

structlog 必须配置以下 processors：

- `TimeStamper(fmt="iso")` - ISO 格式时间戳
- `add_log_level` - 日志级别
- `StackInfoRenderer()` - 栈信息
- `format_exc_info` - 异常格式化
- `JSONRenderer()` - JSON 输出

### 必备日志字段

每条日志必须包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| `timestamp` | string | ISO 8601 时间戳 |
| `level` | string | 日志级别（debug / info / warning / error） |
| `event` | string | 事件名称 |
| `logger` | string | 日志记录器名称 |
| `trace_id` | string | 全链路追踪 ID（请求/任务上下文中） |
| `request_id` | string | 请求追踪 ID（HTTP 请求上下文中） |

### HTTP 请求上下文字段

HTTP 请求日志额外包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| `method` | string | HTTP 方法 |
| `path` | string | 请求路径 |
| `status_code` | int | 响应状态码 |
| `duration_ms` | int | 请求耗时（毫秒） |
| `client_ip` | string | 客户端 IP |

### 任务日志事件命名

任务日志使用 snake_case 命名：

| 事件 | 说明 |
|------|------|
| `task_started` | 任务开始 |
| `task_completed` | 任务完成 |
| `task_failed` | 任务失败 |
| `task_retried` | 任务重试 |
| `task_dead_letter` | 任务进入死信队列 |

### 任务日志示例

**任务开始：**

```json
{
  "timestamp": "2026-07-04T12:00:00.000Z",
  "level": "info",
  "event": "task_started",
  "logger": "generate_content_batch",
  "trace_id": "trace_abc123def456",
  "template_type": "npc",
  "count": 5,
  "region_id": "region_wasteland_01"
}
```

**任务完成：**

```json
{
  "timestamp": "2026-07-04T12:05:00.000Z",
  "level": "info",
  "event": "task_completed",
  "logger": "generate_content_batch",
  "trace_id": "trace_abc123def456",
  "request_id": "gen_20260704_001",
  "duration_ms": 300000
}
```

**任务失败：**

```json
{
  "timestamp": "2026-07-04T12:02:00.000Z",
  "level": "error",
  "event": "task_failed",
  "logger": "generate_content_batch",
  "trace_id": "trace_abc123def456",
  "error": "Connection refused",
  "exc_info": "...",
  "retry_count": 1
}
```

---

## 任务必须记录的审计点

### generate_content_batch

| 操作 | 触发时机 |
|------|----------|
| `generation.batch_started` | 任务开始，创建生成请求后 |

### run_world_consistency_review

| 操作 | 触发时机 |
|------|----------|
| `review.consistency_completed` | 审核完成，写入审核记录后 |

### run_balance_review

| 操作 | 触发时机 |
|------|----------|
| `review.balance_completed` | 审核完成，写入审核记录后 |

### release_content_package

| 操作 | 触发时机 |
|------|----------|
| `content.package_released` | 发布成功后 |

### rollback_content_package

| 操作 | 触发时机 |
|------|----------|
| `content.package_rolled_back` | 回滚成功后 |

---

## 日志级别使用规范

| 级别 | 使用场景 | 示例 |
|------|----------|------|
| `debug` | 调试信息，详细的执行轨迹 | 参数值、中间结果、循环迭代 |
| `info` | 正常业务事件 | 任务开始、任务完成、操作成功 |
| `warning` | 警告，不影响主流程但需要关注 | 重试、降级、性能下降 |
| `error` | 错误，功能异常或失败 | 任务失败、服务不可用、数据异常 |
| `critical` | 严重错误，系统不可用 | 数据库连接失败、配置错误 |

---

## 性能与开销

### 日志采样

- `debug` 级别：生产环境建议采样或关闭
- `info` 级别：正常记录
- `warning` 及以上：全部记录

### 敏感信息处理

日志中禁止出现：
- 密码、密钥、Token
- 身份证号、手机号等个人敏感信息
- 完整的请求/响应体（可能包含敏感数据）

如需记录，必须脱敏后再记录。

---

## 与其他文档的关系

- [README.md](./README.md) - 规范总览
- [task-payloads.md](./task-payloads.md) - 异步任务 payload
- [event-schemas.md](./event-schemas.md) - 事件消息格式
- [retry-and-dlq.md](./retry-and-dlq.md) - 重试与死信队列

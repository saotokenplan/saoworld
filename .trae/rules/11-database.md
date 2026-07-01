# 11 - 数据库设计规范

> 适用角色：后端开发、DBA
> 本文件定义数据库通用约定、状态机约束、关键表特殊规则。

## 数据库选型

- **主数据库**：PostgreSQL 16+
- **驱动**：asyncpg（异步）
- **ORM**：SQLAlchemy 2.0 异步模式
- **迁移工具**：Alembic

---

## 通用约定

### 主键

- 所有表统一使用 UUID 主键（PostgreSQL `uuid` 类型）
- Python 侧默认值：`uuid.uuid4`
- 数据库侧推荐默认值：`gen_random_uuid()`（需启用 pgcrypto 扩展）

### 审计字段

**所有业务表**必须包含以下审计字段：
```python
created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), nullable=False, server_default=func.now()
)
updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
)
```

**例外**：`votes` 表为 append-only，不包含 `updated_at` 字段。

### 外键策略

- **默认策略**：`ON DELETE RESTRICT`（禁止误删级联）
- **例外使用 CASCADE**：
  - `vote_candidates.vote_cycle_id` → `vote_cycles.vote_cycle_id`（候选随投票周期删除）
  - `generated_objects.request_id` → `generation_requests.request_id`（生成产物随请求删除）

### 状态字段

- 使用 `VARCHAR(32)` 存储状态值
- **必须**通过 `CHECK` 约束限制合法值
- **禁止使用 PostgreSQL native enum 类型**（避免迁移锁表风险）
- 在 Python 侧使用 `str, Enum` 定义状态枚举

### 时间字段

- 所有时间字段使用 `TIMESTAMPTZ`（带时区）
- Python 侧使用 `datetime`，必须带 `timezone` 信息
- 应用层统一使用 UTC 时间存储

### 半结构化数据

- 半结构化/可变 schema 的数据使用 PostgreSQL `JSONB` 类型
- 以下字段必须使用 JSONB：
  - `region_scope`、`risk_tags`、`generated_params`
  - `reputation_snapshot`、`progress_jsonb`、`objectives_jsonb`、`rewards_jsonb`
  - `input_payload_jsonb`、`object_payload_jsonb`、`detail_jsonb`
  - `gray_scope_jsonb`、`payload_jsonb`、`unlock_condition_jsonb`
  - `request_payload_jsonb`

### Schema 版本

所有内容对象必须携带 `schema_version INTEGER NOT NULL DEFAULT 1`：
- `content_packages.schema_version`
- `generated_objects.schema_version`
- `quest_definitions.schema_version`

---

## 状态机约束（必须严格遵守）

所有状态迁移必须严格按照以下合法路径执行，禁止跳跃迁移。

### 投票周期状态机

**表**：`vote_cycles`
**字段**：`status`
**合法值**：`draft`, `scheduled`, `open`, `closed`, `finalized`

```
draft → scheduled → open → closed → finalized
                             ↑
                             └── 管理员可重新开放（需审计）
```

**CHECK 约束**：
```sql
CHECK (status IN ('draft', 'scheduled', 'open', 'closed', 'finalized'))
```

**业务规则**：同一 `chapter_id` 下同时只能有一个 `status = 'open'` 的周期。

### 投票候选项状态机

**表**：`vote_candidates`
**字段**：`status`
**合法值**：`active`, `withdrawn`, `selected`

**CHECK 约束**：
```sql
CHECK (status IN ('active', 'withdrawn', 'selected'))
```

### 内容包状态机

**表**：`content_packages`
**字段**：`status`
**合法值**：`packaged`, `gray`, `live`, `archived`, `rolled_back`

```
packaged → gray → live → archived
                 ↑  ↓
                 rolled_back
```

状态迁移规则：
- `packaged → gray`：灰度发布
- `gray → live`：全量发布
- `gray → rolled_back`：灰度回滚
- `live → rolled_back`：线上回滚
- `live → archived`：归档（历史版本）
- `rolled_back` 是**终态**，不可再向 `live`/`gray` 迁移

**CHECK 约束**：
```sql
CHECK (status IN ('packaged', 'gray', 'live', 'archived', 'rolled_back'))
```

### 其他状态枚举值

| 表 | 字段 | 合法值 |
|---|---|---|
| `regions` | `status` | `locked`, `active`, `unstable`, `archived` |
| `player_quests` | `status` | `available`, `active`, `completed`, `failed` |
| `review_records` | `result` | `approved`, `rejected`, `manual_review` |
| `review_records` | `risk_level` | `low`, `medium`, `high`, `critical` |
| `release_records` | `release_mode` | `gray`, `full` |
| `release_records` | `status` | `queued`, `running`, `completed`, `failed` |
| `rollback_records` | `status` | `queued`, `running`, `completed`, `failed` |
| `generation_requests` | `status` | `pending`, `processing`, `succeeded`, `failed_retryable`, `failed_permanent` |
| `generated_objects` | `status` | `pending_review`, `approved`, `rejected`, `needs_revision` |
| `audit_logs` | `operator_role` | `player`, `ops`, `reviewer`, `system` |

---

## 关键表特殊约束

### `votes` 表（投票记录）

**核心规则**：append-only 表，只允许 INSERT，禁止 UPDATE 和 DELETE。

| 约束 | 说明 |
|------|------|
| 无 `updated_at` 字段 | append-only 特征 |
| `UNIQUE (vote_cycle_id, player_id)` | 一个投票周期内每个玩家只能投一票 |
| `UNIQUE (idempotency_key)` | 幂等键全局唯一，防止重复提交 |
| `CHECK (weight > 0 AND weight <= 10.0)` | 投票权重范围 |
| 外键 `player_id` → `players.player_id` | 玩家必须存在 |

**索引**：
- `votes_candidate_id_idx` (`candidate_id`)
- `votes_idempotency_key_idx` UNIQUE (`idempotency_key`)

### `audit_logs` 表（审计日志）

**核心规则**：高吞吐 append-only 表，按月分区，应用账号无 UPDATE/DELETE 权限。

| 要求 | 说明 |
|------|------|
| 按月范围分区 | 按 `created_at` 做 RANGE 分区 |
| 无 UPDATE/DELETE 权限 | 应用数据库账号只授予 INSERT/SELECT |
| `trace_id` 必填 | 用于全链路追踪 |

**索引**：
- `audit_logs_trace_id_idx` (`trace_id`)
- `audit_logs_operator_id_idx` (`operator_id`, `created_at`)
- `audit_logs_resource_idx` (`resource_type`, `resource_id`)
- `audit_logs_action_idx` (`action`, `created_at`)

---

## 索引设计原则

- 所有外键字段必须建索引
- 频繁查询的过滤字段建索引（如 `status`、`chapter_id`）
- 唯一约束自动创建唯一索引
- JSONB 字段按需建 GIN 索引
- 复合索引遵循最左前缀原则

---

## 相关规则

- Python 后端开发规范 → [10-python-backend.md](./10-python-backend.md)
- API 设计规范 → [12-api-design.md](./12-api-design.md)
- 内容发布/回滚 → [42-release-rollback.md](./42-release-rollback.md)

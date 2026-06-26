# 后端与数据详细规范

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 适用范围

- 适用于服务边界、核心数据模型、接口契约、异步任务和事件流的后端执行约束说明。
- 适用于后端服务实现、数据建模、接口设计、任务调度和审计链路建设。
- 不替代产品边界、内容生成规则和工程协作规范中的专项约束。

## 当前定位

- 本文档是后端与数据层的核心执行规范，用于回答“服务如何拆、数据如何存、接口和状态如何流转”。
- 本文档聚焦实现边界、数据契约和系统协作，不单独定义产品目标、内容模板或 Agent 闭环策略。
- 当 API 文档、实现细节或历史讨论与系统契约冲突时，应优先以本文档为准。

## 目标

本规范定义服务边界、核心数据模型、接口契约、异步任务和事件流。目标是让投票、生成、审核、投放、回滚链路形成可追踪、可重试、可审计的后端系统。

## 服务拆分

## 服务列表

- `gateway-service`
  - 客户端统一入口
  - 鉴权、限流、会话上下文
- `player-service`
  - 账号、角色、成长、声望、章节进度
- `world-service`
  - 区域状态、阵营状态、地图与任务可见性
- `vote-service`
  - 候选池、投票资格、投票记录、结算
- `generation-service`
  - 组织生成请求、模板加载、结果落库
- `review-service`
  - 结构化校验、风险判断、人工复核流转
- `content-service`
  - 内容包、灰度投放、版本归档、回滚
- `ops-service`
  - 后台运营入口、指标汇总、Issue 触发

## 服务边界规则

- 客户端不得直接访问生成和审核内部接口
- `vote-service` 不直接修改世界状态，只输出结果
- `generation-service` 不直接上线内容，只产出草案
- `content-service` 是唯一允许改变内容上线状态的服务

## 数据分层

### 业务运行数据

- `players`：玩家账号与进度
- `player_quests`：玩家任务进度实例
- `votes`：投票记录（append-only）

### 世界内容数据（静态/半静态）

- `regions`：区域定义
- `quest_definitions`：任务定义
- `vote_cycles`：投票周期定义
- `vote_candidates`：投票候选项
- `content_packages`：内容包版本
- `generated_objects`：AI 生成的内容对象（待审核）

### 流程状态数据

- `generation_requests`：AI 生成请求队列
- `review_records`：审核记录
- `release_records`：发布操作记录
- `rollback_records`：回滚操作记录

### 审计与回溯数据

- `audit_logs`：通用审计日志（按月分区，append-only）
- `generation_requests.input_payload_jsonb`：生成输入快照
- `generated_objects.object_payload_jsonb`：模型输出快照

## 核心表结构

> **约定**：所有表统一使用 `UUID` 主键（PostgreSQL `uuid` 类型，默认 `gen_random_uuid()`），所有表自动包含 `created_at TIMESTAMPTZ NOT NULL DEFAULT now()` 和 `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()` 审计字段。外键采用 `ON DELETE RESTRICT` 策略（禁止误删级联），业务软删除使用 `deleted_at TIMESTAMPTZ` 字段。状态字段统一使用 `VARCHAR` 存储，通过 `CHECK` 约束或应用层校验限制合法值（避免 PostgreSQL enum 类型的迁移风险）。

### 通用枚举值定义

| 枚举类别 | 字段名 | 合法值 | 说明 |
|---|---|---|---|
| 投票周期状态 | `vote_cycles.status` | `draft`, `scheduled`, `open`, `closed`, `finalized` | 运营创建→定时开放→玩家投票→关闭计票→内容落定 |
| 投票候选项状态 | `vote_candidates.status` | `active`, `withdrawn`, `selected` | 有效/撤回/当选 |
| 内容包状态 | `content_packages.status` | `packaged`, `gray`, `live`, `archived`, `rolled_back` | 打包完成→灰度→全量→归档→已回滚 |
| 区域状态 | `regions.status` | `locked`, `active`, `unstable`, `archived` | 未解锁→活跃→不稳定→归档 |
| 任务状态 | `quests.status` | `available`, `active`, `completed`, `failed` | 可接取→进行中→完成→失败 |
| 审核结果 | `review_records.result` | `approved`, `rejected`, `manual_review` | 自动通过/拒绝/人工复核 |
| 风险等级 | `review_records.risk_level` | `low`, `medium`, `high`, `critical` | 审核风险分级 |
| 发布模式 | `release_records.release_mode` | `gray`, `full` | 灰度/全量发布 |
| 回滚状态 | `rollback_records.status` | `queued`, `running`, `completed`, `failed` | 排队→执行中→完成→失败 |
| 生成任务状态 | `generation_requests.status` | `pending`, `processing`, `succeeded`, `failed_retryable`, `failed_permanent` | 任务队列状态 |
| 操作者角色 | `audit_logs.operator_role` | `player`, `ops`, `reviewer`, `system` | 审计操作者类型 |

### 状态机约束

关键资源的状态迁移必须满足以下合法转移路径：

**投票周期 `vote_cycles.status`：**

```
draft → scheduled → open → closed → finalized
                             ↑
                             └── 管理员可重新开放（需审计）
```

**内容包 `content_packages.status`：**

```
packaged → gray → live → archived
                 ↑  ↓
                 rolled_back
```

- `packaged → gray`：灰度发布
- `gray → live`：全量发布
- `gray → rolled_back`：灰度回滚
- `live → rolled_back`：线上回滚
- `live → archived`：归档（历史版本）
- 任何 `rolled_back` 状态不可再向 `live`/`gray` 迁移

### `players`

玩家主表，存储账号绑定和进度信息。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `player_id` | UUID | PK | 玩家唯一标识 |
| `account_id` | VARCHAR(128) | NOT NULL, UNIQUE | 外部账号系统 ID（OIDC sub） |
| `level` | INTEGER | NOT NULL DEFAULT 1, CHECK (>=1) | 玩家等级 |
| `chapter_id` | VARCHAR(64) | NOT NULL | 当前所在章节 |
| `active_region_id` | UUID | FK → regions.region_id, NULLABLE | 当前活跃区域 |
| `reputation_snapshot` | JSONB | NOT NULL DEFAULT '{}'::jsonb | 各阵营声望快照（结构化 JSON） |
| `created_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |

**索引**：`players_account_id_idx` UNIQUE (`account_id`)

### `regions`

区域定义表，属于世界内容数据。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `region_id` | UUID | PK | 区域唯一标识 |
| `chapter_id` | VARCHAR(64) | NOT NULL | 所属章节 |
| `title` | VARCHAR(256) | NOT NULL | 区域名称 |
| `summary` | TEXT | NULLABLE | 区域摘要 |
| `status` | VARCHAR(32) | NOT NULL DEFAULT 'locked', CHECK IN (...) | 区域状态（见枚举表） |
| `visible` | BOOLEAN | NOT NULL DEFAULT false | 玩家是否可见 |
| `unlock_condition_jsonb` | JSONB | NULLABLE | 解锁条件定义 |
| `created_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |

**索引**：`regions_chapter_id_idx` (`chapter_id`), `regions_status_idx` (`status`)

### `vote_cycles`

投票周期表，控制投票窗口。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `vote_cycle_id` | UUID | PK | 投票周期 ID |
| `chapter_id` | VARCHAR(64) | NOT NULL | 所属章节 |
| `status` | VARCHAR(32) | NOT NULL DEFAULT 'draft', CHECK IN (...) | 周期状态（见枚举表） |
| `starts_at` | TIMESTAMPTZ | NOT NULL | 投票开始时间 |
| `ends_at` | TIMESTAMPTZ | NOT NULL, CHECK (ends_at > starts_at) | 投票结束时间 |
| `created_by` | VARCHAR(128) | NOT NULL | 创建者 operator（OIDC sub） |
| `created_reason` | TEXT | NOT NULL | 创建原因（审计） |
| `finalized_at` | TIMESTAMPTZ | NULLABLE | 计票完成时间 |
| `winning_candidate_id` | UUID | FK → vote_candidates.candidate_id, NULLABLE | 获胜候选项（finalized 后填入） |
| `created_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |

**索引**：`vote_cycles_status_idx` (`status`), `vote_cycles_chapter_id_idx` (`chapter_id`)
**CHECK 约束**：同一 `chapter_id` 下同时只能有一个 `status = 'open'` 的周期（应用层保证或使用部分唯一索引）

### `vote_candidates`

投票候选项表，每个周期包含多个候选项。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `candidate_id` | UUID | PK | 候选项 ID |
| `vote_cycle_id` | UUID | FK → vote_cycles.vote_cycle_id ON DELETE CASCADE, NOT NULL | 所属投票周期 |
| `title` | VARCHAR(512) | NOT NULL | 候选项标题 |
| `summary` | TEXT | NOT NULL | 候选项描述摘要 |
| `description` | TEXT | NULLABLE | 详细描述 |
| `region_scope` | JSONB | NOT NULL DEFAULT '[]'::jsonb | 影响区域 ID 列表（UUID 数组） |
| `risk_tags` | JSONB | NOT NULL DEFAULT '[]'::jsonb | 风险标签（字符串数组） |
| `generated_params` | JSONB | NULLABLE | AI 生成参数快照 |
| `status` | VARCHAR(32) | NOT NULL DEFAULT 'active', CHECK IN ('active','withdrawn','selected') | 候选项状态 |
| `vote_count` | INTEGER | NOT NULL DEFAULT 0 | 得票数（计票后写入） |
| `created_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |

**索引**：`vote_candidates_cycle_id_idx` (`vote_cycle_id`)

### `votes`

投票记录表，记录玩家投票行为。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `vote_id` | UUID | PK | 投票记录 ID |
| `vote_cycle_id` | UUID | FK → vote_cycles.vote_cycle_id, NOT NULL | 投票周期 |
| `player_id` | UUID | FK → players.player_id, NOT NULL | 投票玩家 |
| `candidate_id` | UUID | FK → vote_candidates.candidate_id, NOT NULL | 投给的候选项 |
| `weight` | REAL | NOT NULL DEFAULT 1.0, CHECK (weight > 0 AND weight <= 10.0) | 投票权重 |
| `device_fingerprint_hash` | VARCHAR(128) | NOT NULL | 设备指纹哈希（风控） |
| `idempotency_key` | VARCHAR(128) | NOT NULL | 客户端幂等键 |
| `created_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | 投票时间 |

**唯一约束**：`votes_cycle_player_uniq` UNIQUE (`vote_cycle_id`, `player_id`) — 一个周期每玩家一票
**索引**：`votes_candidate_id_idx` (`candidate_id`), `votes_idempotency_key_idx` UNIQUE (`idempotency_key`)
**注意**：此表为追加写（append-only），不提供 `updated_at`，投票不可修改

### `quests`

任务定义表（静态数据）和任务实例表（玩家任务进度）分离为两张表：

**`quest_definitions`**（静态内容数据）：

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `quest_id` | UUID | PK | 任务定义 ID |
| `chapter_id` | VARCHAR(64) | NOT NULL | 所属章节 |
| `active_region_id` | UUID | FK → regions.region_id | 关联区域 |
| `title` | VARCHAR(256) | NOT NULL | 任务名称 |
| `summary` | TEXT | NULLABLE | 任务摘要 |
| `quest_type` | VARCHAR(32) | NOT NULL | 任务类型（main/side/event） |
| `objectives_jsonb` | JSONB | NOT NULL | 目标定义 |
| `rewards_jsonb` | JSONB | NOT NULL DEFAULT '{}'::jsonb | 奖励定义 |
| `unlock_condition_jsonb` | JSONB | NULLABLE | 解锁条件 |
| `schema_version` | INTEGER | NOT NULL DEFAULT 1 | 内容 schema 版本 |
| `created_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |

**`player_quests`**（玩家任务进度）：

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `player_quest_id` | UUID | PK | 进度记录 ID |
| `player_id` | UUID | FK → players.player_id, NOT NULL | 玩家 |
| `quest_id` | UUID | FK → quest_definitions.quest_id, NOT NULL | 任务定义 |
| `status` | VARCHAR(32) | NOT NULL DEFAULT 'available', CHECK IN (...) | 任务状态 |
| `progress_jsonb` | JSONB | NOT NULL DEFAULT '{}'::jsonb | 任务进度数据 |
| `accepted_at` | TIMESTAMPTZ | NULLABLE | 接取时间 |
| `completed_at` | TIMESTAMPTZ | NULLABLE | 完成时间 |
| `created_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |

**索引**：`player_quests_player_id_idx` (`player_id`, `status`)

### `content_packages`

内容包表，管理内容版本生命周期。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `content_package_id` | UUID | PK | 内容包 ID |
| `chapter_id` | VARCHAR(64) | NOT NULL | 所属章节 |
| `region_id` | UUID | FK → regions.region_id | 目标区域 |
| `package_version` | VARCHAR(32) | NOT NULL | 版本号（如 `v1.2.3`） |
| `source_vote_cycle_id` | UUID | FK → vote_cycles.vote_cycle_id, NULLABLE | 来源投票周期 |
| `source_request_id` | UUID | FK → generation_requests.request_id, NULLABLE | 来源生成请求 |
| `title` | VARCHAR(512) | NOT NULL | 内容包标题 |
| `summary` | TEXT | NULLABLE | 内容包摘要 |
| `status` | VARCHAR(32) | NOT NULL DEFAULT 'packaged', CHECK IN (...) | 内容包状态 |
| `gray_scope_jsonb` | JSONB | NULLABLE | 灰度范围（`{region_ids: [...], player_percent: N}`） |
| `payload_jsonb` | JSONB | NOT NULL | 内容包内容载荷 |
| `schema_version` | INTEGER | NOT NULL DEFAULT 1 | 内容 schema 版本 |
| `released_at` | TIMESTAMPTZ | NULLABLE | 发布时间 |
| `created_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |

**索引**：`content_packages_chapter_id_idx` (`chapter_id`), `content_packages_status_idx` (`status`), `content_packages_region_id_idx` (`region_id`)

### `generation_requests`

AI 内容生成请求表，记录异步生成任务。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `request_id` | UUID | PK | 请求 ID |
| `vote_cycle_id` | UUID | FK → vote_cycles.vote_cycle_id, NULLABLE | 关联投票周期 |
| `source_candidate_id` | UUID | FK → vote_candidates.candidate_id, NULLABLE | 来源候选项 |
| `template_id` | VARCHAR(128) | NOT NULL | 使用的内容模板 ID |
| `input_payload_jsonb` | JSONB | NOT NULL | 生成输入参数 |
| `status` | VARCHAR(32) | NOT NULL DEFAULT 'pending', CHECK IN (...) | 任务状态 |
| `retry_count` | INTEGER | NOT NULL DEFAULT 0 | 已重试次数 |
| `max_retries` | INTEGER | NOT NULL DEFAULT 3 | 最大重试次数 |
| `error_message` | TEXT | NULLABLE | 失败原因（仅 failed 状态） |
| `trace_id` | VARCHAR(128) | NOT NULL | 追踪 ID |
| `created_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |

**索引**：`generation_requests_status_idx` (`status`), `generation_requests_trace_id_idx` (`trace_id`)

### `generated_objects`

AI 生成的内容对象表，产出审核。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `object_id` | UUID | PK | 对象 ID |
| `request_id` | UUID | FK → generation_requests.request_id ON DELETE CASCADE, NOT NULL | 来源请求 |
| `object_type` | VARCHAR(64) | NOT NULL | 对象类型（region/npc/quest/event 等） |
| `schema_version` | INTEGER | NOT NULL DEFAULT 1 | 对象 schema 版本 |
| `object_payload_jsonb` | JSONB | NOT NULL | 对象内容 |
| `quality_score` | REAL | NULLABLE, CHECK (quality_score >= 0 AND quality_score <= 1) | AI 自评质量分 |
| `status` | VARCHAR(32) | NOT NULL DEFAULT 'pending_review' | 审核状态（pending_review/approved/rejected/needs_revision） |
| `created_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |

**索引**：`generated_objects_request_id_idx` (`request_id`), `generated_objects_status_idx` (`status`), `generated_objects_type_idx` (`object_type`)

### `review_records`

审核记录表，记录人工和自动审核结果。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `review_id` | UUID | PK | 审核记录 ID |
| `object_id` | UUID | NOT NULL | 审核对象 ID（generated_object 或 content_package） |
| `review_type` | VARCHAR(32) | NOT NULL | 审核类型（auto/manual/release_check） |
| `rule_version` | VARCHAR(32) | NOT NULL | 使用的审核规则版本 |
| `result` | VARCHAR(32) | NOT NULL, CHECK IN (...) | 审核结果 |
| `risk_level` | VARCHAR(16) | NOT NULL DEFAULT 'low', CHECK IN (...) | 风险等级 |
| `reviewer_id` | VARCHAR(128) | NULLABLE | 审核人（manual 类型必填，对应 OIDC sub） |
| `detail_jsonb` | JSONB | NOT NULL DEFAULT '{}'::jsonb | 审核详情（违规项、建议等） |
| `reviewed_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | 审核时间 |
| `created_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |

**索引**：`review_records_object_id_idx` (`object_id`, `review_type`)

### `release_records`

发布记录表，记录每次发布操作。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `release_id` | UUID | PK | 发布记录 ID |
| `content_package_id` | UUID | FK → content_packages.content_package_id, NOT NULL | 发布的内容包 |
| `release_mode` | VARCHAR(16) | NOT NULL, CHECK IN ('gray','full') | 发布模式 |
| `status` | VARCHAR(16) | NOT NULL DEFAULT 'queued' | 发布状态（queued/running/completed/failed） |
| `gray_scope_jsonb` | JSONB | NULLABLE | 灰度范围（gray 模式必填） |
| `operator_id` | VARCHAR(128) | NOT NULL | 操作者（OIDC sub） |
| `reason` | TEXT | NOT NULL | 发布原因（审计） |
| `trace_id` | VARCHAR(128) | NOT NULL | 追踪 ID |
| `released_at` | TIMESTAMPTZ | NULLABLE | 完成发布时间 |
| `created_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |

### `rollback_records`

回滚记录表，记录每次回滚操作。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `rollback_id` | UUID | PK | 回滚记录 ID |
| `content_package_id` | UUID | FK → content_packages.content_package_id, NOT NULL | 回滚的内容包 |
| `target_version` | VARCHAR(32) | NOT NULL | 回滚目标版本号 |
| `rollback_reason` | TEXT | NOT NULL | 回滚原因 |
| `operator_type` | VARCHAR(16) | NOT NULL DEFAULT 'ops', CHECK IN ('ops','system') | 操作者类型 |
| `operator_id` | VARCHAR(128) | NULLABLE | 操作者 ID（ops 类型必填） |
| `status` | VARCHAR(16) | NOT NULL DEFAULT 'queued', CHECK IN (...) | 回滚状态 |
| `trace_id` | VARCHAR(128) | NOT NULL | 追踪 ID |
| `rolled_back_at` | TIMESTAMPTZ | NULLABLE | 完成回滚时间 |
| `created_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |

### `audit_logs`（通用审计日志表）

所有敏感操作（投票提交、发布、回滚、审核、周期创建）的审计日志。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `audit_id` | UUID | PK | 审计记录 ID |
| `trace_id` | VARCHAR(128) | NOT NULL | 追踪 ID（串联同一操作的所有日志） |
| `request_id` | VARCHAR(128) | NULLABLE | API 请求 ID |
| `operator_id` | VARCHAR(128) | NOT NULL | 操作者标识（OIDC sub 或 system） |
| `operator_role` | VARCHAR(16) | NOT NULL, CHECK IN (...) | 操作者角色 |
| `action` | VARCHAR(64) | NOT NULL | 操作类型（vote_submit/content_release/content_rollback/vote_cycle_create/review_approve） |
| `resource_type` | VARCHAR(64) | NOT NULL | 资源类型 |
| `resource_id` | UUID | NULLABLE | 资源 ID |
| `reason` | TEXT | NULLABLE | 操作原因（运营写接口必填） |
| `request_payload_jsonb` | JSONB | NULLABLE | 请求体快照 |
| `result_status` | SMALLINT | NULLABLE | HTTP 响应码或任务结果状态 |
| `created_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |

**索引**：`audit_logs_trace_id_idx` (`trace_id`), `audit_logs_operator_id_idx` (`operator_id`, `created_at`), `audit_logs_resource_idx` (`resource_type`, `resource_id`), `audit_logs_action_idx` (`action`, `created_at`)
**分区建议**：按月对 `created_at` 做范围分区，审计日志增长快

## 数据库约束

- 强事务主数据统一进入 PostgreSQL
- 半结构化对象使用 `jsonb`（包括 `region_scope`、`risk_tags`、`gray_scope_jsonb`、`payload_jsonb`、`reputation_snapshot`、`progress_jsonb`、`objectives_jsonb`、`rewards_jsonb`、`input_payload_jsonb`、`object_payload_jsonb`、`detail_jsonb`、`request_payload_jsonb`、`unlock_condition_jsonb`、`generated_params`）
- 所有内容对象必须带 `schema_version`（`content_packages`、`generated_objects`、`quest_definitions`）
- 所有业务表必须包含 `created_at` 和 `updated_at`（`votes` 表例外：追加写，无 `updated_at`）
- 关键状态字段必须使用 `VARCHAR` + `CHECK` 约束限制合法值（不使用 PostgreSQL native enum，避免迁移锁表）
- 所有外键默认 `ON DELETE RESTRICT`，仅 `vote_candidates` → `vote_cycles` 和 `generated_objects` → `generation_requests` 使用 `ON DELETE CASCADE`（候选和生成产物随父记录删除）
- 审计日志表 `audit_logs` 按月做范围分区，不提供 UPDATE/DELETE 权限给应用账号
- `votes` 表为 append-only，应用层不得执行 UPDATE 或 DELETE
- 幂等键（`idempotency_key`）必须全局唯一，防止客户端重试导致重复操作
- 所有写操作必须携带 `trace_id`，通过 `audit_logs.trace_id` 可串联同一操作的全链路日志

## API 规范

### 通用约定

- 协议：`HTTPS + JSON`
- 认证：OIDC 签发的 JWT Bearer Token；细粒度 scope 与角色矩阵详见 `docs/30-api/api-permissions.md`
- 时间字段统一使用 ISO 8601（RFC 3339 格式，如 `2025-01-15T10:30:00Z`）
- 接口版本统一前缀 `/api/v1`
- 所有写接口必须携带 `X-Trace-Id` 请求头；运营写接口还需携带 `Idempotency-Key`
- 成功响应统一使用 envelope 包装：`request_id` + `data`（+ `meta` 用于分页）+ `trace_id`（写接口）
- 错误响应统一结构（详见 `docs/30-api/api-error-codes.md` 与 OpenAPI 草案中的特化错误 schema）：

```json
{
  "code": "INVALID_VOTE_STATE",
  "message": "当前投票周期不可投票",
  "request_id": "req_vote_current_409",
  "details": [
    {
      "location": "body",
      "field": "vote_cycle_id",
      "issue": "state_conflict",
      "rejected_value": "vc_001"
    }
  ]
}
```

- `code`：机器可读错误码，错误码枚举见 `docs/30-api/api-error-codes.md`
- `message`：人类可读描述，不应作为客户端分支判断依据
- `request_id`：服务端生成的请求追踪 ID，对应响应头 `X-Request-Id`
- `details`：可选的字段级错误细节数组；参数校验、scope 不足、路径错误等高频错误有特化 schema 约束

### 玩家与世界接口

- `GET /api/v1/world/regions`
  - 获取当前可见区域列表
- `GET /api/v1/world/regions/{region_id}`
  - 获取区域详情和状态
- `GET /api/v1/quests`
  - 获取玩家任务列表

### 投票接口

- `GET /api/v1/votes/current`
  - 获取当前投票周期与候选项
- `POST /api/v1/votes/submit`
  - 提交投票
- `GET /api/v1/votes/history`
  - 获取历史投票结果与落地情况

### 内容投放接口

- `GET /api/v1/content/updates`
  - 获取当前玩家可见的新内容包
- `GET /api/v1/content/packages/{content_package_id}`
  - 获取内容包摘要

### 运营接口

- `POST /api/v1/ops/vote-cycles`
  - 创建投票周期
- `POST /api/v1/ops/review/{object_id}/approve`
  - 批准内容对象
- `POST /api/v1/ops/content-packages/{id}/release`
  - 发布内容包
- `POST /api/v1/ops/content-packages/{id}/rollback`
  - 回滚内容包

## 异步任务规范

所有长任务必须走任务队列，不允许在同步接口里直接执行。

### 推荐任务

- `generate_content_batch`
- `run_world_consistency_review`
- `run_balance_review`
- `package_content_batch`
- `release_content_package`
- `rollback_content_package`
- `daily_gate_scan`

### 任务要求

- 每个任务必须有 `task_id`
- 支持重试与幂等
- 必须写入状态迁移日志
- 必须区分“可重试失败”和“不可重试失败”

## 事件流规范

建议内部事件总线至少包含以下主题：

- `vote.cycle.closed`
- `vote.result.finalized`
- `generation.request.created`
- `generation.batch.completed`
- `review.batch.completed`
- `content.package.released`
- `content.package.rolled_back`

### 事件消息字段

- `event_id`
- `event_type`
- `occurred_at`
- `trace_id`
- `producer`
- `payload`

## 权限与安全

### 权限层级

- `player`
  - 普通玩家行为（世界查询、任务查询、投票、内容更新查询）
- `ops`
  - 运营和配置行为（创建投票周期、发布内容包、回滚内容包）
- `reviewer`
  - 审核与批准行为（审核批准内容对象；默认不具备发布权限）
- `system`
  - Agent 和自动化任务（内部长任务、事件消费、状态流转；不对外暴露）

### OAuth 2.0 Scope

认证采用 OIDC 签发的 JWT Bearer Token，通过细粒度 scope 控制接口访问。当前已定义的 scope：

| Scope | 适用角色 | 说明 |
|---|---|---|
| `world:read` | player, system | 查询世界区域信息 |
| `quests:read` | player, system | 查询玩家任务列表 |
| `votes:read` | player, system | 查询当前投票周期与候选项 |
| `votes:history:read` | player, ops, system | 查询历史投票结果与落地情况 |
| `votes:submit` | player | 提交投票 |
| `content:read` | player, system, ops | 查询内容包和更新列表 |
| `content:release` | ops | 发布内容包 |
| `content:rollback` | ops | 回滚内容包 |
| `review:approve` | reviewer, ops | 审核批准内容对象 |
| `ops:vote-cycles:write` | ops | 创建投票周期 |

接口到 scope 的完整映射见 `docs/30-api/api-permissions.md`。

### 安全要求

- 所有运营接口必须记录操作者（通过 JWT 中的 `sub` 声明）和原因（请求体中 `reason` 字段）
- 敏感操作必须支持二次确认或审批链（发布、回滚、批准）
- 投票接口必须做设备与行为风控（`device_fingerprint_hash`、投票资格校验）
- 内容管理接口必须审计请求体和结果（通过 `X-Trace-Id` 串联）
- 所有写接口必须携带 `Idempotency-Key` 请求头以支持幂等重试

## 性能与一致性要求

- 投票提交接口 p95 响应时间应小于 `300ms`
- 当前投票结果查询应支持缓存
- 内容包发布与回滚必须串行执行
- 单个投票周期的结算必须保证幂等
- 所有状态变更必须可根据 `trace_id` 串联追踪

## 与其他文档的关系

- `docs/20-specs/product-spec.md`
  - 定义产品闭环、MVP 范围和验收口径，本文档负责把这些要求下沉为系统与数据实现约束。
- `docs/20-specs/content-generation-spec.md`
  - 约束生成对象、审核状态和内容生命周期，需与本文档中的数据模型和发布链路保持一致。
- `docs/20-specs/agent-loop-spec.md`
  - 规定 Agent 和门禁如何围绕本文档中的接口、任务和回滚要求开展实现与验证。
- `docs/20-specs/engineering-conventions.md`
  - 定义仓库结构、命名、测试和发布协作规则，约束本文档在工程层的落地方式。
- `docs/30-api/`
  - 基于本文档整理接口总览、权限矩阵、错误码和请求响应样例。

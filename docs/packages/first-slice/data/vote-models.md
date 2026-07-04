# 投票核心数据模型

> 版本：v1.0.0
> 创建时间：2026-07-04

## 通用约定

### 主键
- 所有表统一使用 UUID 主键（PostgreSQL uuid 类型）
- Python 侧默认值：uuid.uuid4
- 数据库侧默认值：gen_random_uuid()

### 审计字段
所有业务表必须包含以下审计字段：
- created_at：TIMESTAMPTZ NOT NULL DEFAULT now()
- updated_at：TIMESTAMPTZ NOT NULL DEFAULT now()

### 状态字段
- 使用 VARCHAR(32) 存储状态值
- 必须通过 CHECK 约束限制合法值
- 在 Python 侧使用 str 或 Enum 定义状态枚举

### 时间字段
- 所有时间字段使用 TIMESTAMPTZ（带时区）
- Python 侧使用 datetime，必须带 timezone 信息
- 应用层统一使用 UTC 时间存储

---

## vote_cycles 表

投票周期表，控制投票窗口。

### 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| vote_cycle_id | UUID | PK | 投票周期唯一标识 |
| chapter_id | VARCHAR(64) | NOT NULL | 所属章节 |
| status | VARCHAR(32) | NOT NULL DEFAULT 'draft', CHECK IN (...) | 周期状态 |
| starts_at | TIMESTAMPTZ | NOT NULL | 投票开始时间 |
| ends_at | TIMESTAMPTZ | NOT NULL, CHECK (ends_at > starts_at) | 投票结束时间 |
| created_by | VARCHAR(128) | NOT NULL | 创建者 operator（OIDC sub） |
| created_reason | TEXT | NOT NULL | 创建原因（审计） |
| finalized_at | TIMESTAMPTZ | NULLABLE | 计票完成时间 |
| winning_candidate_id | UUID | FK → vote_candidates.candidate_id, NULLABLE | 获胜候选项 |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 更新时间 |

### 索引

| 索引名称 | 字段 | 类型 |
|----------|------|------|
| vote_cycles_status_idx | status | 普通索引 |
| vote_cycles_chapter_id_idx | chapter_id | 普通索引 |

### CHECK 约束

- CHECK (status IN ('draft', 'scheduled', 'open', 'closed', 'finalized'))
- CHECK (ends_at > starts_at)

### 业务规则

- 同一 chapter_id 下同时只能有一个 status = 'open' 的周期
- 状态迁移路径：draft → scheduled → open → closed → finalized

---

## vote_candidates 表

投票候选项表，每个周期包含多个候选项。

### 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| candidate_id | UUID | PK | 候选项唯一标识 |
| vote_cycle_id | UUID | FK → vote_cycles.vote_cycle_id ON DELETE CASCADE, NOT NULL | 所属投票周期 |
| title | VARCHAR(512) | NOT NULL | 候选项标题 |
| summary | TEXT | NOT NULL | 候选项描述摘要 |
| description | TEXT | NULLABLE | 详细描述 |
| region_scope | JSONB | NOT NULL DEFAULT '[]'::jsonb | 影响区域 ID 列表 |
| risk_tags | JSONB | NOT NULL DEFAULT '[]'::jsonb | 风险标签 |
| generated_params | JSONB | NULLABLE | AI 生成参数快照 |
| status | VARCHAR(32) | NOT NULL DEFAULT 'active', CHECK IN (...) | 候选项状态 |
| vote_count | INTEGER | NOT NULL DEFAULT 0 | 得票数（计票后写入） |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 创建时间 |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 更新时间 |

### 索引

| 索引名称 | 字段 | 类型 |
|----------|------|------|
| vote_candidates_cycle_id_idx | vote_cycle_id | 普通索引 |

### CHECK 约束

- CHECK (status IN ('active', 'withdrawn', 'selected'))

---

## votes 表

投票记录表，记录玩家投票行为。

### 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| vote_id | UUID | PK | 投票记录唯一标识 |
| vote_cycle_id | UUID | FK → vote_cycles.vote_cycle_id, NOT NULL | 投票周期 |
| player_id | UUID | FK → players.player_id, NOT NULL | 投票玩家 |
| candidate_id | UUID | FK → vote_candidates.candidate_id, NOT NULL | 投给的候选项 |
| weight | REAL | NOT NULL DEFAULT 1.0, CHECK (weight > 0 AND weight <= 10.0) | 投票权重 |
| device_fingerprint_hash | VARCHAR(128) | NOT NULL | 设备指纹哈希（风控） |
| idempotency_key | VARCHAR(128) | NOT NULL | 客户端幂等键 |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 投票时间 |

### 索引

| 索引名称 | 字段 | 类型 |
|----------|------|------|
| votes_candidate_id_idx | candidate_id | 普通索引 |
| votes_idempotency_key_idx | idempotency_key | 唯一索引 |

### CHECK 约束

- CHECK (weight > 0 AND weight <= 10.0)

### 唯一约束

- UNIQUE (vote_cycle_id, player_id) — 一个周期每玩家一票
- UNIQUE (idempotency_key) — 幂等键全局唯一

### 特殊说明

- 此表为 append-only，不提供 updated_at，投票不可修改
- 不允许 UPDATE 和 DELETE 操作

---

## 实体关系图

```
vote_cycles (1) ────(*) vote_candidates
    │
    │
vote_cycles (1) ────(*) votes
vote_candidates (1) ────(*) votes
players (1) ────(*) votes
```

### 外键策略

| 外键 | 目标表 | 策略 | 说明 |
|------|--------|------|------|
| vote_candidates.vote_cycle_id | vote_cycles | CASCADE | 候选随投票周期删除 |
| votes.vote_cycle_id | vote_cycles | RESTRICT | 禁止删除有投票的周期 |
| votes.candidate_id | vote_candidates | RESTRICT | 禁止删除有投票的候选 |
| votes.player_id | players | RESTRICT | 禁止删除有投票的玩家 |
| vote_cycles.winning_candidate_id | vote_candidates | RESTRICT | 禁止删除获胜候选 |

---

## 状态机约束

### 投票周期状态机

```
draft → scheduled → open → closed → finalized
                             ↑
                             └── 管理员可重新开放（需审计）
```

### 候选项状态机

```
active ←── withdrawn
   │
   ↓
selected
```

---

## 数据一致性要求

1. 同一章节下只能有一个 open 状态的投票周期
2. 投票周期关闭后不允许新的投票提交
3. 投票记录的 player_id 必须在 players 表中存在
4. 投票记录的 candidate_id 必须属于对应的投票周期
5. 幂等键必须全局唯一
6. 投票权重必须在有效范围内
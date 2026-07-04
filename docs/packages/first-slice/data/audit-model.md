# 审计日志模型

> 版本：v1.0.0
> 创建时间：2026-07-04

## audit_logs 表

通用审计日志表，记录所有敏感操作的详细信息。

### 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| audit_id | UUID | PK | 审计记录唯一标识 |
| trace_id | VARCHAR(128) | NOT NULL | 全链路追踪ID |
| request_id | VARCHAR(128) | NULLABLE | API请求ID |
| operator_id | VARCHAR(128) | NOT NULL | 操作者标识（OIDC sub 或 system） |
| operator_role | VARCHAR(16) | NOT NULL, CHECK IN (...) | 操作者角色 |
| action | VARCHAR(64) | NOT NULL | 操作类型 |
| resource_type | VARCHAR(64) | NOT NULL | 资源类型 |
| resource_id | UUID | NULLABLE | 资源ID |
| reason | TEXT | NULLABLE | 操作原因（运营写接口必填） |
| request_payload_jsonb | JSONB | NULLABLE | 请求体快照 |
| result_status | SMALLINT | NULLABLE | HTTP响应码或任务结果状态 |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | 创建时间 |

### 索引

| 索引名称 | 字段 | 类型 |
|----------|------|------|
| audit_logs_trace_id_idx | trace_id | 普通索引 |
| audit_logs_operator_id_idx | operator_id, created_at | 复合索引 |
| audit_logs_resource_idx | resource_type, resource_id | 复合索引 |
| audit_logs_action_idx | action, created_at | 复合索引 |

### CHECK 约束

- CHECK (operator_role IN ('player', 'ops', 'reviewer', 'system'))

---

## 操作类型（action）

### 投票相关

| action 值 | 说明 | 触发场景 |
|-----------|------|----------|
| vote_submit | 玩家提交投票 | POST /api/v1/votes/submit |
| vote_cycle_create | 创建投票周期 | POST /api/v1/ops/vote-cycles |
| vote_cycle_scheduled | 计划投票周期 | POST /api/v1/ops/vote-cycles/{id}/schedule |
| vote_cycle_opened | 开放投票 | POST /api/v1/ops/vote-cycles/{id}/open |
| vote_cycle_closed | 关闭投票 | POST /api/v1/ops/vote-cycles/{id}/close |
| vote_cycle_finalized | 结算投票 | POST /api/v1/ops/vote-cycles/{id}/finalize |

### 内容相关

| action 值 | 说明 | 触发场景 |
|-----------|------|----------|
| content_release | 发布内容包 | POST /api/v1/ops/content-packages/{id}/release |
| content_rollback | 回滚内容包 | POST /api/v1/ops/content-packages/{id}/rollback |

### 审核相关

| action 值 | 说明 | 触发场景 |
|-----------|------|----------|
| review_approve | 审核批准 | POST /api/v1/ops/review/{object_id}/approve |

---

## 资源类型（resource_type）

| resource_type 值 | 说明 |
|------------------|------|
| vote | 投票记录 |
| vote_cycle | 投票周期 |
| vote_candidate | 投票候选项 |
| content_package | 内容包 |
| generated_object | 生成对象 |

---

## 操作者角色（operator_role）

| 角色 | 说明 |
|------|------|
| player | 普通玩家 |
| ops | 运营人员 |
| reviewer | 审核人员 |
| system | 系统/自动化任务 |

---

## 表特性

### Append-Only

- 审计日志表为 append-only
- 不允许 UPDATE 和 DELETE 操作
- 应用数据库账号只授予 INSERT 和 SELECT 权限

### 分区策略

- 按月对 created_at 做范围分区
- 审计日志增长快，分区便于管理和归档
- 建议保留期限：至少 6 个月

---

## 全链路追踪

所有写操作必须携带 trace_id，通过 audit_logs.trace_id 可串联同一操作的全链路日志。

### 请求追踪头

| 请求头 | 说明 |
|--------|------|
| X-Request-Id | 请求ID，服务端生成或客户端传递 |
| X-Trace-Id | 全链路追踪ID，客户端传递 |

### 响应追踪头

所有响应必须返回：
- X-Request-Id：请求追踪ID
- X-Trace-Id：全链路追踪ID（如果请求携带了）

---

## 审计记录写入时机

### 投票提交时
- operator_id：玩家ID
- operator_role：player
- action：vote_submit
- resource_type：vote
- resource_id：vote_id
- request_payload_jsonb：请求体快照

### 投票周期状态迁移时
- operator_id：运营ID
- operator_role：ops
- action：vote_cycle_xxx
- resource_type：vote_cycle
- resource_id：vote_cycle_id
- reason：操作原因

### 投票结算时
- operator_id：系统或运营ID
- operator_role：system 或 ops
- action：vote_cycle_finalized
- resource_type：vote_cycle
- resource_id：vote_cycle_id
- request_payload_jsonb：结算结果快照

---

## 合规要求

- 审计日志必须加密存储
- 审计日志访问必须记录访问日志
- 定期审计日志完整性检查
- 审计日志保留期限：至少 6 个月
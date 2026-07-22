# 审计日志

> 版本：v1.0.0
> 创建时间：2026-07-04

## 功能描述

审计日志是系统安全和合规的重要组成部分，记录所有敏感操作的详细信息，支持全链路追踪和问题排查。

## 审计范围

以下操作必须记录审计日志：

### 投票相关操作

| 操作 | action 值 | 说明 |
|------|-----------|------|
| 投票提交 | vote_submit | 玩家提交投票 |
| 投票周期创建 | vote_cycle_create | 运营创建投票周期 |
| 投票周期计划 | vote_cycle_scheduled | 投票周期计划 |
| 投票周期开放 | vote_cycle_opened | 投票周期开放 |
| 投票周期关闭 | vote_cycle_closed | 投票周期关闭 |
| 投票周期结算 | vote_cycle_finalized | 投票周期结算 |

### 内容相关操作

| 操作 | action 值 | 说明 |
|------|-----------|------|
| 内容包发布 | content_release | 运营发布内容包 |
| 内容包回滚 | content_rollback | 运营回滚内容包 |

### 审核相关操作

| 操作 | action 值 | 说明 |
|------|-----------|------|
| 审核批准 | review_approve | 审核批准内容对象 |

## 审计记录结构

### 核心字段

| 字段 | 类型 | 说明 |
|------|------|------|
| audit_id | UUID | 审计记录唯一标识 |
| trace_id | VARCHAR(128) | 全链路追踪ID |
| request_id | VARCHAR(128) | API请求ID |
| operator_id | VARCHAR(128) | 操作者标识（OIDC sub 或 system） |
| operator_role | VARCHAR(16) | 操作者角色（player/ops/reviewer/system） |
| action | VARCHAR(64) | 操作类型 |
| resource_type | VARCHAR(64) | 资源类型 |
| resource_id | UUID | 资源ID |
| reason | TEXT | 操作原因（运营写接口必填） |
| request_payload_jsonb | JSONB | 请求体快照 |
| result_status | SMALLINT | HTTP响应码或任务结果状态 |
| created_at | TIMESTAMPTZ | 创建时间 |

### 操作者角色

| 角色 | 说明 |
|------|------|
| player | 普通玩家 |
| ops | 运营人员 |
| reviewer | 审核人员 |
| system | 系统/自动化任务 |

## 审计日志表特性

### Append-Only

审计日志表为 append-only，不允许 UPDATE 和 DELETE 操作。

### 分区策略

按月对 `created_at` 做范围分区，审计日志增长快，分区便于管理和归档。

### 权限控制

应用数据库账号只授予 INSERT 和 SELECT 权限，不授予 UPDATE 和 DELETE 权限。

## 索引设计

| 索引名称 | 字段 | 类型 |
|----------|------|------|
| audit_logs_trace_id_idx | trace_id | 普通索引 |
| audit_logs_operator_id_idx | operator_id, created_at | 复合索引 |
| audit_logs_resource_idx | resource_type, resource_id | 复合索引 |
| audit_logs_action_idx | action, created_at | 复合索引 |

## 全链路追踪

所有写操作必须携带 `trace_id`，通过 `audit_logs.trace_id` 可串联同一操作的全链路日志。

### 请求追踪头

| 请求头 | 说明 |
|--------|------|
| X-Request-Id | 请求ID，服务端生成或客户端传递 |
| X-Trace-Id | 全链路追踪ID，客户端传递 |

### 响应追踪头

所有响应必须返回：
- X-Request-Id：请求追踪ID
- X-Trace-Id：全链路追踪ID（如果请求携带了）

## 审计日志写入时机

### 投票提交时
- 记录投票提交审计日志
- 包含投票周期ID、候选项ID、玩家ID、权重、设备指纹

### 投票周期状态迁移时
- 创建、计划、开放、关闭、结算操作均需记录
- 包含投票周期ID、原状态、新状态、操作原因

### 投票结算时
- 记录结算结果审计日志
- 包含各候选项票数、获胜者、总票数

## 审计日志查询

审计日志主要用于：
- 问题排查
- 安全审计
- 合规检查
- 操作追溯

查询接口（运营）：
- 按 trace_id 查询
- 按 operator_id 查询
- 按 action 查询
- 按 resource_type 和 resource_id 查询
- 按时间范围查询

## 合规要求

- 审计日志保留期限：至少 6 个月
- 审计日志必须加密存储
- 审计日志访问必须记录访问日志
- 定期审计日志完整性检查
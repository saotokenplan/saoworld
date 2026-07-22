# 审计追踪流程

> 版本：v1.0.0
> 创建时间：2026-07-04

## 概述

审计追踪流程描述了系统如何记录和追踪所有敏感操作的详细信息，支持全链路追踪和问题排查。

## 审计记录结构

### 核心字段

| 字段 | 类型 | 说明 |
|------|------|------|
| audit_id | UUID | 审计记录唯一标识 |
| trace_id | VARCHAR(128) | 全链路追踪ID |
| request_id | VARCHAR(128) | API请求ID |
| operator_id | VARCHAR(128) | 操作者标识 |
| operator_role | VARCHAR(16) | 操作者角色 |
| action | VARCHAR(64) | 操作类型 |
| resource_type | VARCHAR(64) | 资源类型 |
| resource_id | UUID | 资源ID |
| reason | TEXT | 操作原因 |
| request_payload_jsonb | JSONB | 请求体快照 |
| result_status | SMALLINT | 结果状态 |
| created_at | TIMESTAMPTZ | 创建时间 |

## 全链路追踪

### 请求追踪头

| 请求头 | 说明 | 必填 |
|--------|------|------|
| X-Request-Id | 请求ID，服务端生成或客户端传递 | 否 |
| X-Trace-Id | 全链路追踪ID，客户端传递 | 写接口必填 |

### 响应追踪头

所有响应必须返回：
- X-Request-Id：请求追踪ID
- X-Trace-Id：全链路追踪ID（如果请求携带了）

### 追踪流程

1. 客户端发起请求时生成并携带 X-Trace-Id
2. 网关服务接收请求，记录追踪ID
3. 各后端服务处理请求时，传递追踪ID
4. 所有写操作记录审计日志时，关联追踪ID
5. 通过追踪ID可串联同一操作的全链路日志

## 审计记录写入时机

### 投票提交时

**触发**：玩家提交投票

**记录内容**：
- operator_id：玩家ID
- operator_role：player
- action：vote_submit
- resource_type：vote
- resource_id：vote_id
- request_payload_jsonb：请求体快照
- trace_id：追踪ID

### 投票周期创建时

**触发**：运营创建投票周期

**记录内容**：
- operator_id：运营ID
- operator_role：ops
- action：vote_cycle_create
- resource_type：vote_cycle
- resource_id：vote_cycle_id
- reason：创建原因
- request_payload_jsonb：请求体快照
- trace_id：追踪ID

### 投票周期状态迁移时

**触发**：运营执行状态迁移操作（计划、开放、关闭）

**记录内容**：
- operator_id：运营ID
- operator_role：ops
- action：vote_cycle_xxx（scheduled/opened/closed）
- resource_type：vote_cycle
- resource_id：vote_cycle_id
- reason：操作原因
- trace_id：追踪ID

### 投票结算时

**触发**：系统或运营执行结算操作

**记录内容**：
- operator_id：系统或运营ID
- operator_role：system 或 ops
- action：vote_cycle_finalized
- resource_type：vote_cycle
- resource_id：vote_cycle_id
- reason：结算原因
- request_payload_jsonb：结算结果快照
- trace_id：追踪ID

## 审计日志查询

### 查询接口（运营）

**按 trace_id 查询**：
```
GET /api/v1/ops/audit-logs?trace_id=xxx
```

**按 operator_id 查询**：
```
GET /api/v1/ops/audit-logs?operator_id=xxx&start_time=xxx&end_time=xxx
```

**按 action 查询**：
```
GET /api/v1/ops/audit-logs?action=vote_submit&start_time=xxx&end_time=xxx
```

**按 resource_type 和 resource_id 查询**：
```
GET /api/v1/ops/audit-logs?resource_type=vote&resource_id=xxx
```

### 查询响应

```json
{
  "request_id": "req_audit_query_xxx",
  "data": [
    {
      "audit_id": "uuid-string",
      "trace_id": "trace_xxx",
      "request_id": "req_vote_submit_xxx",
      "operator_id": "player_xxx",
      "operator_role": "player",
      "action": "vote_submit",
      "resource_type": "vote",
      "resource_id": "vote_xxx",
      "reason": null,
      "request_payload_jsonb": {...},
      "result_status": 200,
      "created_at": "2026-07-04T10:30:00Z"
    }
  ],
  "meta": {
    "total": 1,
    "limit": 20,
    "offset": 0
  }
}
```

## 审计日志特性

### Append-Only

- 审计日志表为 append-only
- 不允许 UPDATE 和 DELETE 操作
- 应用数据库账号只授予 INSERT 和 SELECT 权限

### 分区策略

- 按月对 created_at 做范围分区
- 审计日志增长快，分区便于管理和归档
- 建议保留期限：至少 6 个月

### 索引设计

| 索引名称 | 字段 | 类型 |
|----------|------|------|
| audit_logs_trace_id_idx | trace_id | 普通索引 |
| audit_logs_operator_id_idx | operator_id, created_at | 复合索引 |
| audit_logs_resource_idx | resource_type, resource_id | 复合索引 |
| audit_logs_action_idx | action, created_at | 复合索引 |

## 合规要求

### 存储要求

- 审计日志必须加密存储
- 审计日志访问必须记录访问日志
- 定期审计日志完整性检查

### 保留期限

- 审计日志保留期限：至少 6 个月
- 超过保留期限的审计日志应归档或删除

### 访问控制

- 审计日志查询只能由 ops 角色执行
- 查询操作必须记录访问日志
- 敏感审计记录的查询需二次确认

## 问题排查流程

### 步骤 1：获取追踪ID

**来源**：
- 请求响应头 X-Trace-Id
- 请求响应体 request_id
- 客户端日志

### 步骤 2：查询审计日志

**操作**：
- 使用 trace_id 查询审计日志
- 获取所有关联的操作记录

### 步骤 3：分析日志

**分析内容**：
- 操作顺序
- 操作结果
- 请求体快照
- 错误信息

### 步骤 4：定位问题

**定位依据**：
- 异常操作的位置
- 错误码和错误信息
- 时间戳

### 步骤 5：解决问题

**解决方案**：
- 根据分析结果采取相应措施
- 记录解决方案
- 验证修复效果

## 审计日志完整性检查

### 定期检查

- 检查审计日志表是否正常写入
- 检查索引是否正常工作
- 检查分区是否正常管理

### 异常检测

- 检测审计日志写入失败
- 检测追踪ID缺失
- 检测异常操作模式

### 告警规则

- 审计日志写入失败超过阈值时告警
- 异常操作模式触发告警
- 敏感操作频繁执行时告警
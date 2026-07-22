# 投票接口清单

> 版本：v1.0.0
> 创建时间：2026-07-04

> 说明：本文档用于快速理解“最小投票链路”涉及的接口切片；正式 API 契约、请求头要求、错误码与响应结构以 `docs/30-api/` 和 `docs/20-specs/backend-data-spec.md` 为准。

## 通用约定

### 协议与格式
- 协议：HTTPS
- 数据格式：JSON（Content-Type: application/json）
- API 版本前缀：/api/v1
- 时间格式：ISO 8601 / RFC 3339（UTC）

### 响应格式

所有成功响应使用统一 envelope 包装：

```json
{
  "request_id": "req_abc123def456",
  "data": { ... },
  "meta": {
    "total": 100,
    "limit": 20,
    "offset": 0
  },
  "trace_id": "trace_xxx"
}
```

### 错误响应格式

所有错误响应使用统一结构：

```json
{
  "code": "ERROR_CODE",
  "message": "人类可读错误描述",
  "request_id": "req_abc123def456",
  "details": [
    {
      "location": "body",
      "field": "candidate_id",
      "issue": "not_found",
      "rejected_value": "xxx"
    }
  ],
  "trace_id": "trace_xxx"
}
```

## 玩家接口

### 1. 获取当前投票周期

**方法**：GET
**路径**：/api/v1/votes/current
**Scope**：votes:read

**说明**：获取当前开放的投票周期与候选项

**请求头**：
- Authorization: Bearer <token>

**成功响应**（200）：
```json
{
  "request_id": "req_vote_current_xxx",
  "data": {
    "vote_cycle_id": "uuid-string",
    "chapter_id": "chapter_01",
    "status": "open",
    "starts_at": "2026-07-04T00:00:00Z",
    "ends_at": "2026-07-11T00:00:00Z",
    "candidates": [
      {
        "candidate_id": "uuid-string",
        "title": "候选项标题",
        "summary": "描述摘要",
        "description": "详细描述",
        "region_scope": ["region_id_1"],
        "risk_tags": [],
        "status": "active",
        "vote_count": 0
      }
    ],
    "winning_candidate_id": null,
    "finalized_at": null
  },
  "meta": {
    "total": 1,
    "limit": 20,
    "offset": 0
  }
}
```

**错误响应**：
- 404 VOTE_CYCLE_NOT_FOUND：当前不存在有效投票周期
- 409 INVALID_VOTE_STATE：当前投票周期不可投票

---

### 2. 提交投票

**方法**：POST
**路径**：/api/v1/votes/submit
**Scope**：votes:submit

**说明**：玩家提交投票

**请求头**：
- Authorization: Bearer <token>
- X-Trace-Id: <trace_id>
- Idempotency-Key: <idempotency_key>
- X-Player-Id: <player_id>

**请求体**：
```json
{
  "vote_cycle_id": "uuid-string",
  "candidate_id": "uuid-string",
  "player_id": "uuid-string",
  "weight": 1.0,
  "device_fingerprint_hash": "string-hash",
  "reason": "可选，投票原因"
}
```

**成功响应**（200）：
```json
{
  "request_id": "req_vote_submit_xxx",
  "data": {
    "vote_id": "uuid-string",
    "vote_cycle_id": "uuid-string",
    "candidate_id": "uuid-string",
    "player_id": "uuid-string",
    "weight": 1.0,
    "created_at": "2026-07-04T10:30:00Z"
  },
  "trace_id": "trace_xxx"
}
```

**错误响应**：
- 404 VOTE_CYCLE_NOT_FOUND：投票周期不存在
- 404 CANDIDATE_NOT_FOUND：候选项不存在
- 409 INVALID_VOTE_STATE：投票周期状态不允许投票
- 409 VOTE_CYCLE_CLOSED：投票周期已关闭
- 409 CANDIDATE_OUT_OF_SCOPE：候选项不属于当前投票周期
- 409 DUPLICATE_VOTE：同一玩家在同一周期重复投票
- 403 PLAYER_NOT_ELIGIBLE：玩家不满足投票资格
- 403 VOTE_RISK_BLOCKED：命中设备或行为风控

---

### 3. 获取历史投票结果

**方法**：GET
**路径**：/api/v1/votes/history
**Scope**：votes:history:read

**说明**：获取历史投票结果与落地情况

**请求头**：
- Authorization: Bearer <token>

**查询参数**：
- limit（可选）：每页数量，默认 20
- offset（可选）：偏移量，默认 0
- chapter_id（可选）：按章节过滤

**成功响应**（200）：
```json
{
  "request_id": "req_vote_history_xxx",
  "data": [
    {
      "vote_cycle_id": "uuid-string",
      "chapter_id": "chapter_01",
      "status": "finalized",
      "starts_at": "2026-06-27T00:00:00Z",
      "ends_at": "2026-07-04T00:00:00Z",
      "winning_candidate_id": "uuid-string",
      "winning_candidate": {
        "title": "获胜候选项",
        "region_scope": ["region_id_1"]
      },
      "total_votes": 1000,
      "candidate_results": [
        {
          "candidate_id": "uuid-string",
          "title": "候选项A",
          "vote_count": 600,
          "vote_percentage": 60.0
        }
      ],
      "finalized_at": "2026-07-04T00:05:00Z",
      "content_package_id": "pkg_xxx"
    }
  ],
  "meta": {
    "total": 10,
    "limit": 20,
    "offset": 0
  },
  "trace_id": "trace_xxx"
}
```

---

## 运营接口

### 4. 创建投票周期

**方法**：POST
**路径**：/api/v1/ops/vote-cycles
**Scope**：ops:vote-cycles:write

**说明**：创建投票周期

**请求头**：
- Authorization: Bearer <token>
- X-Trace-Id: <trace_id>
- Idempotency-Key: <idempotency_key>

**请求体**：
```json
{
  "chapter_id": "chapter_01",
  "starts_at": "2026-07-04T00:00:00Z",
  "ends_at": "2026-07-11T00:00:00Z",
  "created_by": "operator_id",
  "created_reason": "创建投票周期原因",
  "candidates": [
    {
      "title": "候选项标题",
      "summary": "描述摘要",
      "description": "详细描述",
      "region_scope": ["region_id_1"],
      "risk_tags": [],
      "generated_params": {}
    }
  ]
}
```

**成功响应**（201）：
```json
{
  "request_id": "req_ops_create_xxx",
  "data": {
    "vote_cycle_id": "uuid-string",
    "chapter_id": "chapter_01",
    "status": "draft",
    "starts_at": "2026-07-04T00:00:00Z",
    "ends_at": "2026-07-11T00:00:00Z",
    "created_at": "2026-07-04T09:00:00Z"
  },
  "trace_id": "trace_xxx"
}
```

**错误响应**：
- 400 INVALID_ARGUMENT：参数校验失败
- 409 VOTE_CYCLE_CONFLICT：投票周期创建冲突

---

### 5. 计划投票周期

**方法**：POST
**路径**：/api/v1/ops/vote-cycles/{vote_cycle_id}/schedule
**Scope**：ops:vote-cycles:write

**说明**：将投票周期从 draft 状态转换为 scheduled 状态

**请求头**：
- Authorization: Bearer <token>
- X-Trace-Id: <trace_id>

**请求体**：
```json
{
  "reason": "计划投票周期原因"
}
```

**成功响应**（200）：
```json
{
  "request_id": "req_ops_schedule_xxx",
  "data": {
    "vote_cycle_id": "uuid-string",
    "status": "scheduled"
  },
  "trace_id": "trace_xxx"
}
```

**错误响应**：
- 404 VOTE_CYCLE_NOT_FOUND：投票周期不存在
- 409 INVALID_VOTE_STATE：投票周期状态不允许计划

---

### 6. 开放投票

**方法**：POST
**路径**：/api/v1/ops/vote-cycles/{vote_cycle_id}/open
**Scope**：ops:vote-cycles:write

**说明**：将投票周期从 scheduled 状态转换为 open 状态

**请求头**：
- Authorization: Bearer <token>
- X-Trace-Id: <trace_id>

**请求体**：
```json
{
  "reason": "开放投票原因"
}
```

**成功响应**（200）：
```json
{
  "request_id": "req_ops_open_xxx",
  "data": {
    "vote_cycle_id": "uuid-string",
    "status": "open"
  },
  "trace_id": "trace_xxx"
}
```

**错误响应**：
- 404 VOTE_CYCLE_NOT_FOUND：投票周期不存在
- 409 INVALID_VOTE_STATE：投票周期状态不允许开放
- 409 VOTE_CYCLE_CONFLICT：同一章节下已有开放的投票周期

---

### 7. 关闭投票

**方法**：POST
**路径**：/api/v1/ops/vote-cycles/{vote_cycle_id}/close
**Scope**：ops:vote-cycles:write

**说明**：将投票周期从 open 状态转换为 closed 状态

**请求头**：
- Authorization: Bearer <token>
- X-Trace-Id: <trace_id>

**请求体**：
```json
{
  "reason": "关闭投票原因"
}
```

**成功响应**（200）：
```json
{
  "request_id": "req_ops_close_xxx",
  "data": {
    "vote_cycle_id": "uuid-string",
    "status": "closed"
  },
  "trace_id": "trace_xxx"
}
```

**错误响应**：
- 404 VOTE_CYCLE_NOT_FOUND：投票周期不存在
- 409 INVALID_VOTE_STATE：投票周期状态不允许关闭

---

### 8. 结算投票

**方法**：POST
**路径**：/api/v1/ops/vote-cycles/{vote_cycle_id}/finalize
**Scope**：ops:vote-cycles:write

**说明**：将投票周期从 closed 状态转换为 finalized 状态，自动计票

**请求头**：
- Authorization: Bearer <token>
- X-Trace-Id: <trace_id>

**请求体**：
```json
{
  "reason": "结算投票原因"
}
```

**成功响应**（200）：
```json
{
  "request_id": "req_ops_finalize_xxx",
  "data": {
    "vote_cycle_id": "uuid-string",
    "status": "finalized",
    "winning_candidate_id": "uuid-string",
    "total_votes": 1000,
    "candidate_results": [
      {
        "candidate_id": "uuid-string",
        "vote_count": 600,
        "vote_percentage": 60.0
      }
    ],
    "finalized_at": "2026-07-04T00:05:00Z"
  },
  "trace_id": "trace_xxx"
}
```

**错误响应**：
- 404 VOTE_CYCLE_NOT_FOUND：投票周期不存在
- 409 INVALID_VOTE_STATE：投票周期状态不允许结算
- 409 NO_CANDIDATES_FOUND：投票周期下无有效候选项

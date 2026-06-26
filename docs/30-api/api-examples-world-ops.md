# 世界与运营接口样例

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本文档用于补充第三批世界查询、任务查询以及运营敏感写接口的请求响应样例，帮助后续服务端实现、客户端接入以及 OpenAPI 草案下沉时保持一致的契约形态。

## 适用范围

- 适用于 `GET /api/v1/world/regions`
- 适用于 `GET /api/v1/world/regions/{region_id}`
- 适用于 `GET /api/v1/quests`
- 适用于 `POST /api/v1/ops/vote-cycles`
- 适用于 `POST /api/v1/ops/review/{object_id}/approve`
- 不替代接口总览、权限矩阵和错误码文档，而是作为具体接口层面的补充样例

## 当前定位

- 本文档是接口样例，不替代详细规范
- 接口边界以 `docs/30-api/api-overview.md` 为准
- 权限与审计要求以 `docs/30-api/api-permissions.md` 为准
- 错误码以 `docs/30-api/api-error-codes.md` 为准

## 通用约定

- 协议：`HTTPS + JSON`
- 认证：`Bearer Token`
- 时间格式：ISO 8601
- 列表接口统一使用 `request_id + data + meta`
- 详情接口统一使用 `request_id + data + meta`
- 写接口统一使用 `request_id + trace_id + data + meta + audit`
- 写接口需要 `Idempotency-Key` 时，`meta.idempotent_replay` 表示是否命中幂等重放

## `GET /api/v1/world/regions`

### 作用

- 获取当前玩家可见区域列表
- 返回区域摘要与统一分页 `meta`
- 返回统一审计字段

### 请求示例

```http
GET /api/v1/world/regions?page=1&page_size=20 HTTP/1.1
Authorization: Bearer <player_token>
Accept: application/json
```

### 成功响应示例

```json
{
  "request_id": "req_region_list_001",
  "data": [
    {
      "region_id": "region_wasteland_01",
      "chapter_id": "chapter_02",
      "title": "荒原边境",
      "summary": "玩家已解锁的荒原外围区域。",
      "status": "active",
      "visible": true,
      "created_at": "2026-06-20T08:00:00Z",
      "updated_at": "2026-06-26T08:00:00Z",
      "created_by": "system_world_seed",
      "updated_by": "system_world_projection"
    },
    {
      "region_id": "region_ruins_02",
      "chapter_id": "chapter_02",
      "title": "遗迹深处",
      "summary": "当前章节主线推进后的新探索区域。",
      "status": "unstable",
      "visible": true,
      "created_at": "2026-06-21T08:00:00Z",
      "updated_at": "2026-06-29T09:00:00Z",
      "created_by": "system_world_seed",
      "updated_by": "ops_001"
    }
  ],
  "meta": {
    "resource_type": "region",
    "page": 1,
    "page_size": 20,
    "total": 2,
    "returned": 2,
    "has_more": false
  }
}
```

### 空结果示例

```json
{
  "request_id": "req_region_list_002",
  "data": [],
  "meta": {
    "resource_type": "region",
    "page": 1,
    "page_size": 20,
    "total": 0,
    "returned": 0,
    "has_more": false
  }
}
```

### 分页越界示例

```json
{
  "request_id": "req_region_list_003",
  "data": [],
  "meta": {
    "resource_type": "region",
    "page": 4,
    "page_size": 20,
    "total": 2,
    "returned": 0,
    "has_more": false
  }
}
```

### 常见错误

分页参数非法：

```json
{
  "code": "INVALID_ARGUMENT",
  "message": "分页参数不合法",
  "request_id": "req_pagination_400",
  "details": [
    {
      "location": "query",
      "field": "page_size",
      "issue": "must_be_between_1_and_100",
      "rejected_value": "0"
    }
  ]
}
```

作用域不足：

```json
{
  "code": "INSUFFICIENT_SCOPE",
  "message": "当前访问令牌缺少所需作用域",
  "request_id": "req_scope_403",
  "details": [
    {
      "location": "header",
      "field": "Authorization",
      "issue": "missing_required_scope",
      "rejected_value": "<required-scope>"
    }
  ]
}
```

## `GET /api/v1/world/regions/{region_id}`

### 作用

- 获取单个区域详情
- 返回区域当前状态和统一审计字段

### 请求示例

```http
GET /api/v1/world/regions/region_ruins_02 HTTP/1.1
Authorization: Bearer <player_token>
Accept: application/json
```

### 成功响应示例

```json
{
  "request_id": "req_region_detail_001",
  "data": {
    "region_id": "region_ruins_02",
    "chapter_id": "chapter_02",
    "title": "遗迹深处",
    "summary": "遗迹能量波动导致区域状态不稳定。",
    "status": "unstable",
    "visible": true,
    "created_at": "2026-06-21T08:00:00Z",
    "updated_at": "2026-06-29T09:00:00Z",
    "created_by": "system_world_seed",
    "updated_by": "ops_001"
  },
  "meta": {
    "resource_type": "region"
  }
}
```

### 常见错误

区域 ID 格式非法：

```json
{
  "code": "INVALID_ARGUMENT",
  "message": "区域 ID 格式不合法",
  "request_id": "req_region_id_400",
  "details": [
    {
      "location": "path",
      "field": "region_id",
      "issue": "pattern_mismatch",
      "rejected_value": "ruins-02"
    }
  ]
}
```

区域不可见：

```json
{
  "code": "REGION_NOT_VISIBLE",
  "message": "区域当前对玩家不可见",
  "request_id": "req_region_403"
}
```

区域不存在：

```json
{
  "code": "REGION_NOT_FOUND",
  "message": "区域不存在",
  "request_id": "req_region_404"
}
```

## `GET /api/v1/quests`

### 作用

- 获取当前玩家任务列表
- 返回任务摘要和统一分页 `meta`
- 返回统一审计字段

### 请求示例

```http
GET /api/v1/quests?page=1&page_size=20 HTTP/1.1
Authorization: Bearer <player_token>
Accept: application/json
```

### 成功响应示例

```json
{
  "request_id": "req_quest_list_001",
  "data": [
    {
      "quest_id": "quest_ruins_scan_01",
      "chapter_id": "chapter_02",
      "active_region_id": "region_ruins_02",
      "title": "调查遗迹异变",
      "summary": "进入遗迹深处并完成三处异常点扫描。",
      "status": "active",
      "created_at": "2026-06-29T09:05:00Z",
      "updated_at": "2026-06-29T10:00:00Z",
      "created_by": "system_quest_projection",
      "updated_by": "system_quest_projection"
    }
  ],
  "meta": {
    "resource_type": "quest",
    "page": 1,
    "page_size": 20,
    "total": 1,
    "returned": 1,
    "has_more": false
  }
}
```

### 空结果示例

```json
{
  "request_id": "req_quest_list_002",
  "data": [],
  "meta": {
    "resource_type": "quest",
    "page": 1,
    "page_size": 20,
    "total": 0,
    "returned": 0,
    "has_more": false
  }
}
```

### 分页越界示例

```json
{
  "request_id": "req_quest_list_003",
  "data": [],
  "meta": {
    "resource_type": "quest",
    "page": 2,
    "page_size": 20,
    "total": 1,
    "returned": 0,
    "has_more": false
  }
}
```

### 常见错误

分页参数非法：

```json
{
  "code": "INVALID_ARGUMENT",
  "message": "分页参数不合法",
  "request_id": "req_pagination_400",
  "details": [
    {
      "location": "query",
      "field": "page_size",
      "issue": "must_be_between_1_and_100",
      "rejected_value": "0"
    }
  ]
}
```

作用域不足：

```json
{
  "code": "INSUFFICIENT_SCOPE",
  "message": "当前访问令牌缺少所需作用域",
  "request_id": "req_scope_403",
  "details": [
    {
      "location": "header",
      "field": "Authorization",
      "issue": "missing_required_scope",
      "rejected_value": "<required-scope>"
    }
  ]
}
```

任务列表暂不可用：

```json
{
  "code": "QUEST_LIST_UNAVAILABLE",
  "message": "任务列表暂不可用",
  "request_id": "req_quest_503"
}
```

## `POST /api/v1/ops/vote-cycles`

### 作用

- 创建投票周期
- 返回统一幂等与审计信息
- 对时间窗口冲突进行显式约束

### 请求示例

```http
POST /api/v1/ops/vote-cycles HTTP/1.1
Authorization: Bearer <ops_token>
Content-Type: application/json
Accept: application/json
Idempotency-Key: 6b3efcbf-9331-4c10-a70d-bf9048f5d90f
X-Trace-Id: trace_vote_cycle_001
```

```json
{
  "chapter_id": "chapter_03",
  "starts_at": "2026-07-01T08:00:00Z",
  "ends_at": "2026-07-03T08:00:00Z",
  "candidate_ids": ["candidate_101", "candidate_102", "candidate_103"],
  "reason": "第三章主线剧情投票创建"
}
```

### 成功响应示例

```json
{
  "request_id": "req_ops_vote_cycle_001",
  "trace_id": "trace_vote_cycle_001",
  "data": {
    "vote_cycle_id": "cycle_202607",
    "status": "scheduled"
  },
  "meta": {
    "resource_type": "vote_cycle",
    "idempotent_replay": false,
    "accepted_at": "2026-06-30T08:00:00Z",
    "audit_record_id": "audit_vote_cycle_001"
  },
  "audit": {
    "audit_record_id": "audit_vote_cycle_001",
    "operator_id": "ops_001",
    "operator_role": "ops",
    "action": "vote_cycle.create",
    "target_id": "cycle_202607",
    "reason": "第三章主线剧情投票创建",
    "result": "created",
    "occurred_at": "2026-06-30T08:00:00Z",
    "trace_id": "trace_vote_cycle_001"
  }
}
```

### 幂等重复提交响应示例

```json
{
  "request_id": "req_ops_vote_cycle_002",
  "trace_id": "trace_vote_cycle_001",
  "data": {
    "vote_cycle_id": "cycle_202607",
    "status": "scheduled"
  },
  "meta": {
    "resource_type": "vote_cycle",
    "idempotent_replay": true,
    "accepted_at": "2026-06-30T08:00:00Z",
    "audit_record_id": "audit_vote_cycle_001"
  },
  "audit": {
    "audit_record_id": "audit_vote_cycle_001",
    "operator_id": "ops_001",
    "operator_role": "ops",
    "action": "vote_cycle.create",
    "target_id": "cycle_202607",
    "reason": "第三章主线剧情投票创建",
    "result": "created",
    "occurred_at": "2026-06-30T08:00:00Z",
    "trace_id": "trace_vote_cycle_001"
  }
}
```

### 常见错误

请求体非法：

```json
{
  "code": "INVALID_ARGUMENT",
  "message": "投票周期请求体不合法",
  "request_id": "req_vote_cycle_400",
  "details": [
    {
      "location": "body",
      "field": "candidate_ids",
      "issue": "min_items_2",
      "rejected_value": "[candidate_101]"
    }
  ]
}
```

缺少作用域或无创建权限：

```json
{
  "code": "INSUFFICIENT_SCOPE",
  "message": "当前访问令牌缺少所需作用域",
  "request_id": "req_scope_403",
  "details": [
    {
      "location": "header",
      "field": "Authorization",
      "issue": "missing_required_scope",
      "rejected_value": "<required-scope>"
    }
  ]
}
```

时间窗口冲突：

```json
{
  "code": "VOTE_CYCLE_CONFLICT",
  "message": "当前章节已存在时间窗口重叠的投票周期",
  "request_id": "req_vote_cycle_409"
}
```

## `POST /api/v1/ops/review/{object_id}/approve`

### 作用

- 批准审核对象
- 返回统一幂等与审计信息
- 对审核状态冲突进行显式约束

### 请求示例

```http
POST /api/v1/ops/review/object_story_001/approve HTTP/1.1
Authorization: Bearer <reviewer_token>
Content-Type: application/json
Accept: application/json
Idempotency-Key: 62fa9d07-4d29-4cf2-b4bf-61b2e579cc4f
X-Trace-Id: trace_review_001
```

```json
{
  "review_result": "approved",
  "reason": "结构化审核通过，允许进入打包阶段"
}
```

### 成功响应示例

```json
{
  "request_id": "req_review_approve_001",
  "trace_id": "trace_review_001",
  "data": {
    "review_id": "review_001",
    "object_id": "object_story_001",
    "review_result": "approved",
    "reviewed_at": "2026-06-29T09:30:00Z"
  },
  "meta": {
    "resource_type": "review",
    "idempotent_replay": false,
    "accepted_at": "2026-06-29T09:30:00Z",
    "audit_record_id": "audit_review_001"
  },
  "audit": {
    "audit_record_id": "audit_review_001",
    "operator_id": "reviewer_001",
    "operator_role": "reviewer",
    "action": "review.approve",
    "target_id": "object_story_001",
    "reason": "结构化审核通过，允许进入打包阶段",
    "result": "approved",
    "occurred_at": "2026-06-29T09:30:00Z",
    "trace_id": "trace_review_001"
  }
}
```

### 幂等重复提交响应示例

```json
{
  "request_id": "req_review_approve_002",
  "trace_id": "trace_review_001",
  "data": {
    "review_id": "review_001",
    "object_id": "object_story_001",
    "review_result": "approved",
    "reviewed_at": "2026-06-29T09:30:00Z"
  },
  "meta": {
    "resource_type": "review",
    "idempotent_replay": true,
    "accepted_at": "2026-06-29T09:30:00Z",
    "audit_record_id": "audit_review_001"
  },
  "audit": {
    "audit_record_id": "audit_review_001",
    "operator_id": "reviewer_001",
    "operator_role": "reviewer",
    "action": "review.approve",
    "target_id": "object_story_001",
    "reason": "结构化审核通过，允许进入打包阶段",
    "result": "approved",
    "occurred_at": "2026-06-29T09:30:00Z",
    "trace_id": "trace_review_001"
  }
}
```

### 常见错误

请求体非法：

```json
{
  "code": "INVALID_ARGUMENT",
  "message": "审核批准请求体不合法",
  "request_id": "req_review_approve_400",
  "details": [
    {
      "location": "body",
      "field": "review_result",
      "issue": "unsupported_enum",
      "rejected_value": "approved_now"
    }
  ]
}
```

无审核批准权限：

```json
{
  "code": "REVIEW_APPROVAL_FORBIDDEN",
  "message": "当前角色无审核批准权限",
  "request_id": "req_review_403"
}
```

审核对象不存在：

```json
{
  "code": "REVIEW_OBJECT_NOT_FOUND",
  "message": "审核对象不存在",
  "request_id": "req_review_404"
}
```

对象当前不可批准：

```json
{
  "code": "INVALID_REVIEW_STATE",
  "message": "当前对象不处于可批准状态",
  "request_id": "req_review_409"
}
```

## 审计与实现建议

### `GET /api/v1/world/regions`

- 列表响应应统一返回 `meta.page/page_size/total/returned/has_more`
- 区域摘要应保持最小可评审字段，不提前虚构完整世界对象
- 区域查询与详情查询的 `resource_type` 应保持一致

### `GET /api/v1/world/regions/{region_id}`

- 详情响应应统一返回 `request_id + data + meta`
- 不可见与不存在必须区分 `403` 和 `404`
- 审计字段应与主草案中的 `created_at/updated_at/created_by/updated_by` 保持一致

### `GET /api/v1/quests`

- 列表响应应统一返回 `meta.page/page_size/total/returned/has_more`
- 任务摘要字段应保持最小可评审集合
- 服务降级时应稳定返回 `QUEST_LIST_UNAVAILABLE`

### `POST /api/v1/ops/vote-cycles`

- 应支持 `Idempotency-Key`
- 应返回统一 `audit` 字段，记录操作者、原因和目标对象
- 应显式校验章节时间窗口冲突和候选项数量边界

### `POST /api/v1/ops/review/{object_id}/approve`

- 应支持 `Idempotency-Key`
- 应返回统一 `audit` 字段，记录审核人、原因和目标对象
- 必须区分“参数非法”“对象不存在”“状态冲突”和“权限不足”

## 建议下一步

1. 继续把样例文档与 `docs/30-api/openapi-v1-draft.yaml` 的复用层进一步抽象对齐
2. 再评估是否把单文件 OpenAPI 草案拆成按服务组织的子草案
3. 最后补齐可能需要的排序、过滤和 SDK 友好性说明

## 与其他文档的关系

- `docs/30-api/api-overview.md`
  - 作为世界查询、任务查询和运营写接口的上游总览，定义接口入口、职责和服务归属
- `docs/30-api/api-permissions.md`
  - 定义世界、任务和运营审核接口的角色边界与审计要求
- `docs/30-api/api-error-codes.md`
  - 定义本文件中成功与失败样例所对应的错误码语义
- `docs/20-specs/backend-data-spec.md`
  - 作为更高权威的执行规范，约束世界投影、任务投影、审核链和接口实现边界
- `docs/30-api/openapi-draft.md`
  - 作为本文件后续下沉到 OpenAPI 草案的汇总入口
- `docs/30-api/openapi-v1-draft.yaml`
  - 当前单文件 OpenAPI 草案输出，是本文件样例结构的直接契约来源

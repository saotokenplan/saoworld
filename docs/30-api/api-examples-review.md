# 审核接口样例

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本文档用于补充审核记录查询、审核批准与拒绝链路的请求响应样例，帮助后续服务端实现、客户端接入以及 OpenAPI 草案下沉时保持一致的契约形态。

## 适用范围

- 适用于 `GET /api/v1/ops/review/records`
- 适用于 `GET /api/v1/ops/review/records/{record_id}`
- 适用于 `POST /api/v1/ops/review/{object_id}/approve`
- 适用于 `POST /api/v1/ops/review/{object_id}/reject`
- 不替代接口总览、权限矩阵和错误码文档，而是作为具体接口层面的补充样例

## 当前定位

- 本文档是接口样例，不替代详细规范
- 接口边界以 `docs/30-api/api-overview.md` 为准
- 权限与审计要求以 `docs/30-api/api-permissions.md` 为准
- 错误码以 `docs/30-api/api-error-codes.md` 为准

## 通用约定

- 协议：`HTTPS + JSON`
- 认证：OIDC 签发的 JWT Bearer Token（`Authorization: Bearer <token>`）
- 时间格式：ISO 8601
- 列表接口统一使用 `request_id + data + meta`
- 详情接口统一使用 `request_id + data + meta`
- 写接口统一使用 `request_id + trace_id + data + meta + audit`
- 写接口需要 `Idempotency-Key` 时，`meta.idempotent_replay` 表示是否命中幂等重放

## `GET /api/v1/ops/review/records`

### 作用

- 获取审核记录列表（运营/审核接口）
- 返回审核记录摘要和统一分页 `meta`
- 支持按状态、风险等级、对象类型筛选

### 请求示例

```http
GET /api/v1/ops/review/records?page=1&page_size=20&status=pending&risk_level=high HTTP/1.1
Authorization: Bearer <reviewer_token>
Accept: application/json
```

### 成功响应示例

```json
{
  "request_id": "req_review_records_001",
  "data": [
    {
      "review_record_id": "review_001",
      "object_id": "object_story_001",
      "object_type": "story",
      "object_title": "遗迹异变调查",
      "status": "pending",
      "risk_level": "high",
      "risk_tags": ["敏感主题", "高冲突"],
      "review_score": 0.72,
      "created_at": "2026-06-29T08:00:00Z",
      "updated_at": "2026-06-29T08:00:00Z",
      "created_by": "system_review_pipeline",
      "updated_by": "system_review_pipeline"
    },
    {
      "review_record_id": "review_002",
      "object_id": "object_npc_001",
      "object_type": "npc",
      "object_title": "露娜·暗星",
      "status": "pending",
      "risk_level": "medium",
      "risk_tags": ["阵营对抗"],
      "review_score": 0.85,
      "created_at": "2026-06-29T09:00:00Z",
      "updated_at": "2026-06-29T09:00:00Z",
      "created_by": "system_review_pipeline",
      "updated_by": "system_review_pipeline"
    }
  ],
  "meta": {
    "resource_type": "review_record",
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
  "request_id": "req_review_records_002",
  "data": [],
  "meta": {
    "resource_type": "review_record",
    "page": 1,
    "page_size": 20,
    "total": 0,
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

## `GET /api/v1/ops/review/records/{record_id}`

### 作用

- 获取审核记录详情（运营/审核接口）
- 返回审核记录完整信息和审计字段

### 请求示例

```http
GET /api/v1/ops/review/records/review_001 HTTP/1.1
Authorization: Bearer <reviewer_token>
Accept: application/json
```

### 成功响应示例

```json
{
  "request_id": "req_review_detail_001",
  "data": {
    "review_record_id": "review_001",
    "object_id": "object_story_001",
    "object_type": "story",
    "object_title": "遗迹异变调查",
    "status": "pending",
    "risk_level": "high",
    "risk_tags": ["敏感主题", "高冲突"],
    "review_score": 0.72,
    "check_results": {
      "world_consistency": "passed",
      "reward_boundary": "passed",
      "content_safety": "warning",
      "duplication": "passed"
    },
    "content_safety_details": {
      "score": 0.65,
      "flags": ["可能涉及暴力描述"],
      "suggestion": "建议人工复核"
    },
    "created_at": "2026-06-29T08:00:00Z",
    "updated_at": "2026-06-29T08:00:00Z",
    "created_by": "system_review_pipeline",
    "updated_by": "system_review_pipeline"
  },
  "meta": {
    "resource_type": "review_record"
  }
}
```

### 常见错误

审核记录不存在：

```json
{
  "code": "REVIEW_RECORD_NOT_FOUND",
  "message": "审核记录不存在",
  "request_id": "req_review_detail_404"
}
```

## `POST /api/v1/ops/review/{object_id}/approve`

### 作用

- 批准审核对象（审核接口）
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

## `POST /api/v1/ops/review/{object_id}/reject`

### 作用

- 拒绝审核对象（审核接口）
- 返回统一幂等与审计信息

### 请求示例

```http
POST /api/v1/ops/review/object_story_002/reject HTTP/1.1
Authorization: Bearer <reviewer_token>
Content-Type: application/json
Accept: application/json
Idempotency-Key: 7db2ba7d-cbe5-49a2-9237-9e2cc7190e1d
X-Trace-Id: trace_review_reject_001
```

```json
{
  "review_result": "rejected",
  "reason": "内容安全检查未通过，涉及敏感主题",
  "rejection_reasons": ["内容安全", "敏感主题"],
  "suggestion": "建议修改后重新提交"
}
```

### 成功响应示例

```json
{
  "request_id": "req_review_reject_001",
  "trace_id": "trace_review_reject_001",
  "data": {
    "review_id": "review_002",
    "object_id": "object_story_002",
    "review_result": "rejected",
    "reviewed_at": "2026-06-29T10:00:00Z",
    "rejection_reasons": ["内容安全", "敏感主题"],
    "suggestion": "建议修改后重新提交"
  },
  "meta": {
    "resource_type": "review",
    "idempotent_replay": false,
    "accepted_at": "2026-06-29T10:00:00Z",
    "audit_record_id": "audit_review_reject_001"
  },
  "audit": {
    "audit_record_id": "audit_review_reject_001",
    "operator_id": "reviewer_001",
    "operator_role": "reviewer",
    "action": "review.reject",
    "target_id": "object_story_002",
    "reason": "内容安全检查未通过，涉及敏感主题",
    "result": "rejected",
    "occurred_at": "2026-06-29T10:00:00Z",
    "trace_id": "trace_review_reject_001"
  }
}
```

### 常见错误

对象当前不可拒绝：

```json
{
  "code": "INVALID_REVIEW_STATE",
  "message": "当前对象不处于可拒绝状态",
  "request_id": "req_review_reject_409"
}
```

## 审计与实现建议

### `GET /api/v1/ops/review/records`

- 列表响应应统一返回 `meta.page/page_size/total/returned/has_more`
- 支持按状态、风险等级、对象类型筛选

### `GET /api/v1/ops/review/records/{record_id}`

- 详情响应应统一返回 `request_id + data + meta`
- 检查结果应明确表达每项检查的状态

### `POST /api/v1/ops/review/{object_id}/approve`

- 应支持 `Idempotency-Key`
- 应返回统一 `audit` 字段，记录审核人、原因和目标对象
- 必须区分"参数非法""对象不存在""状态冲突"和"权限不足"

### `POST /api/v1/ops/review/{object_id}/reject`

- 应支持 `Idempotency-Key`
- 应返回统一 `audit` 字段，记录审核人、原因和目标对象
- 拒绝时应提供拒绝原因和修改建议

## 与其他文档的关系

- `docs/30-api/api-overview.md`
  - 作为审核接口的上游总览，定义接口入口、职责和服务归属
- `docs/30-api/api-permissions.md`
  - 定义审核接口的角色边界和审计要求
- `docs/30-api/api-error-codes.md`
  - 定义本文件中成功与失败样例所对应的错误码语义
- `docs/20-specs/backend-data-spec.md`
  - 作为更高权威的执行规范，约束审核数据模型和接口实现边界
- `docs/30-api/openapi-draft.md`
  - 作为本文件后续下沉到 OpenAPI 草案的汇总入口
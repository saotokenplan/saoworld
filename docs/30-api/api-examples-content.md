# 内容接口样例

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本文档用于补充内容查询、发布与回滚链路的请求响应样例，帮助后续服务端实现、客户端接入以及 OpenAPI 草案下沉时保持一致的契约形态。

## 适用范围

- 适用于 `GET /api/v1/content/updates`
- 适用于 `GET /api/v1/content/packages/{content_package_id}`
- 适用于 `POST /api/v1/ops/content-packages/{id}/release`
- 适用于 `POST /api/v1/ops/content-packages/{id}/rollback`
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

## `GET /api/v1/content/updates`

### 作用

- 获取当前玩家可见的新内容包列表
- 返回内容包基础摘要、影响区域和灰度可见标记
- 返回统一分页 `meta`

### 请求示例

```http
GET /api/v1/content/updates?page=1&page_size=20 HTTP/1.1
Authorization: Bearer <player_token>
Accept: application/json
```

### 成功响应示例

```json
{
  "request_id": "req_content_updates_001",
  "data": [
    {
      "content_package_id": "pkg_chapter_02_ruins_20260629_01",
      "title": "遗迹异变调查",
      "summary": "遗迹区域追加限时探索任务与阵营事件。",
      "published_at": "2026-06-29T10:00:00Z",
      "affected_regions": ["region_ruins_02"],
      "gray_visible": true,
      "created_at": "2026-06-28T18:00:00Z",
      "updated_at": "2026-06-29T10:00:00Z",
      "created_by": "system_content_pipeline",
      "updated_by": "ops_001"
    }
  ],
  "meta": {
    "resource_type": "content_package",
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
  "request_id": "req_content_updates_002",
  "data": [],
  "meta": {
    "resource_type": "content_package",
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
  "request_id": "req_content_updates_003",
  "data": [],
  "meta": {
    "resource_type": "content_package",
    "page": 3,
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

服务暂不可用：

```json
{
  "code": "CONTENT_UPDATES_UNAVAILABLE",
  "message": "内容更新列表暂不可用",
  "request_id": "req_content_updates_503"
}
```

## `GET /api/v1/content/packages/{content_package_id}`

### 作用

- 获取单个内容包详情摘要
- 返回当前状态、灰度范围和统一审计字段

### 请求示例

```http
GET /api/v1/content/packages/pkg_chapter_02_ruins_20260629_01 HTTP/1.1
Authorization: Bearer <player_token>
Accept: application/json
```

### 成功响应示例

```json
{
  "request_id": "req_content_package_001",
  "data": {
    "content_package_id": "pkg_chapter_02_ruins_20260629_01",
    "title": "遗迹异变调查",
    "summary": "遗迹区域探索线扩展包。",
    "status": "gray",
    "published_at": "2026-06-29T10:00:00Z",
    "affected_regions": ["region_ruins_02"],
    "gray_scope": {
      "region_ids": ["region_ruins_02"],
      "player_percent": 10
    },
    "created_at": "2026-06-28T18:00:00Z",
    "updated_at": "2026-06-29T10:00:00Z",
    "created_by": "system_content_pipeline",
    "updated_by": "ops_001"
  },
  "meta": {
    "resource_type": "content_package"
  }
}
```

### 常见错误

内容包 ID 格式非法：

```json
{
  "code": "INVALID_ARGUMENT",
  "message": "内容包 ID 格式不合法",
  "request_id": "req_content_package_id_400",
  "details": [
    {
      "location": "path",
      "field": "content_package_id",
      "issue": "pattern_mismatch",
      "rejected_value": "package-001"
    }
  ]
}
```

内容包不可见：

```json
{
  "code": "CONTENT_PACKAGE_NOT_VISIBLE",
  "message": "内容包对当前玩家不可见",
  "request_id": "req_content_package_403"
}
```

内容包不存在：

```json
{
  "code": "CONTENT_PACKAGE_NOT_FOUND",
  "message": "内容包不存在",
  "request_id": "req_content_package_404"
}
```

## `POST /api/v1/ops/content-packages/{id}/release`

### 作用

- 发起内容包发布
- 支持灰度发布范围
- 返回统一幂等与审计信息

### 请求示例

```http
POST /api/v1/ops/content-packages/pkg_chapter_02_ruins_20260629_01/release HTTP/1.1
Authorization: Bearer <ops_token>
Content-Type: application/json
Accept: application/json
Idempotency-Key: 92461d46-4423-4690-9170-682ee23f0ef1
X-Trace-Id: trace_release_001
```

```json
{
  "gray_scope": {
    "region_ids": ["region_ruins_02"],
    "player_percent": 10
  },
  "reason": "首轮灰度发布"
}
```

### 成功响应示例

```json
{
  "request_id": "req_release_001",
  "trace_id": "trace_release_001",
  "data": {
    "content_package_id": "pkg_chapter_02_ruins_20260629_01",
    "status": "gray",
    "release_mode": "gray",
    "released_at": "2026-06-29T10:05:00Z"
  },
  "meta": {
    "resource_type": "content_package_release",
    "idempotent_replay": false,
    "accepted_at": "2026-06-29T10:05:00Z",
    "audit_record_id": "audit_release_001"
  },
  "audit": {
    "audit_record_id": "audit_release_001",
    "operator_id": "ops_001",
    "operator_role": "ops",
    "action": "content_package.release",
    "target_id": "pkg_chapter_02_ruins_20260629_01",
    "reason": "首轮灰度发布",
    "result": "accepted",
    "occurred_at": "2026-06-29T10:05:00Z",
    "trace_id": "trace_release_001"
  }
}
```

### 幂等重复提交响应示例

```json
{
  "request_id": "req_release_002",
  "trace_id": "trace_release_001",
  "data": {
    "content_package_id": "pkg_chapter_02_ruins_20260629_01",
    "status": "gray",
    "release_mode": "gray",
    "released_at": "2026-06-29T10:05:00Z"
  },
  "meta": {
    "resource_type": "content_package_release",
    "idempotent_replay": true,
    "accepted_at": "2026-06-29T10:05:00Z",
    "audit_record_id": "audit_release_001"
  },
  "audit": {
    "audit_record_id": "audit_release_001",
    "operator_id": "ops_001",
    "operator_role": "ops",
    "action": "content_package.release",
    "target_id": "pkg_chapter_02_ruins_20260629_01",
    "reason": "首轮灰度发布",
    "result": "accepted",
    "occurred_at": "2026-06-29T10:05:00Z",
    "trace_id": "trace_release_001"
  }
}
```

### 常见错误

缺少原因字段：

```json
{
  "code": "REASON_REQUIRED",
  "message": "敏感操作缺少原因字段",
  "request_id": "req_reason_required_400",
  "details": [
    {
      "location": "body",
      "field": "reason",
      "issue": "required"
    }
  ]
}
```

灰度范围非法：

```json
{
  "code": "INVALID_ARGUMENT",
  "message": "灰度范围参数不合法",
  "request_id": "req_release_gray_scope_400",
  "details": [
    {
      "location": "body",
      "field": "gray_scope.player_percent",
      "issue": "must_be_between_1_and_100",
      "rejected_value": "0"
    }
  ]
}
```

无发布权限：

```json
{
  "code": "CONTENT_RELEASE_FORBIDDEN",
  "message": "当前角色无内容发布权限",
  "request_id": "req_release_forbidden_403"
}
```

内容包不存在：

```json
{
  "code": "CONTENT_PACKAGE_NOT_FOUND",
  "message": "内容包不存在",
  "request_id": "req_content_package_404"
}
```

内容包状态不满足发布条件：

```json
{
  "code": "CONTENT_PACKAGE_NOT_RELEASABLE",
  "message": "内容包不满足发布前置条件",
  "request_id": "req_release_conflict_409"
}
```

内容包已正式生效：

```json
{
  "code": "CONTENT_PACKAGE_ALREADY_LIVE",
  "message": "内容包已处于正式生效状态",
  "request_id": "req_release_already_live_409"
}
```

发布与回滚需要串行执行：

```json
{
  "code": "PACKAGE_SERIALIZATION_REQUIRED",
  "message": "当前已有发布或回滚流程在执行",
  "request_id": "req_package_serial_409"
}
```

## `POST /api/v1/ops/content-packages/{id}/rollback`

### 作用

- 发起内容包回滚
- 返回统一幂等与审计信息
- 明确目标版本和排队状态

### 请求示例

```http
POST /api/v1/ops/content-packages/pkg_chapter_02_ruins_20260629_01/rollback HTTP/1.1
Authorization: Bearer <ops_token>
Content-Type: application/json
Accept: application/json
Idempotency-Key: 7db2ba7d-cbe5-49a2-9237-9e2cc7190e1d
X-Trace-Id: trace_rollback_001
```

```json
{
  "target_version": "v2026.06.28",
  "reason": "灰度后出现区域任务异常，回滚到上一个稳定版本"
}
```

### 成功响应示例

```json
{
  "request_id": "req_rollback_001",
  "trace_id": "trace_rollback_001",
  "data": {
    "rollback_id": "rollback_001",
    "content_package_id": "pkg_chapter_02_ruins_20260629_01",
    "target_version": "v2026.06.28",
    "status": "queued",
    "rolled_back_at": "2026-06-29T11:30:00Z"
  },
  "meta": {
    "resource_type": "content_package_rollback",
    "idempotent_replay": false,
    "accepted_at": "2026-06-29T11:30:00Z",
    "audit_record_id": "audit_rollback_001"
  },
  "audit": {
    "audit_record_id": "audit_rollback_001",
    "operator_id": "ops_001",
    "operator_role": "ops",
    "action": "content_package.rollback",
    "target_id": "pkg_chapter_02_ruins_20260629_01",
    "reason": "灰度后出现区域任务异常，回滚到上一个稳定版本",
    "result": "queued",
    "occurred_at": "2026-06-29T11:30:00Z",
    "trace_id": "trace_rollback_001"
  }
}
```

### 幂等重复提交响应示例

```json
{
  "request_id": "req_rollback_002",
  "trace_id": "trace_rollback_001",
  "data": {
    "rollback_id": "rollback_001",
    "content_package_id": "pkg_chapter_02_ruins_20260629_01",
    "target_version": "v2026.06.28",
    "status": "queued",
    "rolled_back_at": "2026-06-29T11:30:00Z"
  },
  "meta": {
    "resource_type": "content_package_rollback",
    "idempotent_replay": true,
    "accepted_at": "2026-06-29T11:30:00Z",
    "audit_record_id": "audit_rollback_001"
  },
  "audit": {
    "audit_record_id": "audit_rollback_001",
    "operator_id": "ops_001",
    "operator_role": "ops",
    "action": "content_package.rollback",
    "target_id": "pkg_chapter_02_ruins_20260629_01",
    "reason": "灰度后出现区域任务异常，回滚到上一个稳定版本",
    "result": "queued",
    "occurred_at": "2026-06-29T11:30:00Z",
    "trace_id": "trace_rollback_001"
  }
}
```

### 常见错误

回滚目标非法：

```json
{
  "code": "ROLLBACK_TARGET_INVALID",
  "message": "回滚目标版本非法",
  "request_id": "req_rollback_invalid_400"
}
```

缺少原因字段：

```json
{
  "code": "REASON_REQUIRED",
  "message": "敏感操作缺少原因字段",
  "request_id": "req_reason_required_400",
  "details": [
    {
      "location": "body",
      "field": "reason",
      "issue": "required"
    }
  ]
}
```

无回滚权限：

```json
{
  "code": "CONTENT_ROLLBACK_FORBIDDEN",
  "message": "当前角色无内容回滚权限",
  "request_id": "req_rollback_forbidden_403"
}
```

内容包不存在：

```json
{
  "code": "CONTENT_PACKAGE_NOT_FOUND",
  "message": "内容包不存在",
  "request_id": "req_content_package_404"
}
```

当前内容包不可回滚：

```json
{
  "code": "CONTENT_PACKAGE_NOT_ROLLBACKABLE",
  "message": "内容包当前不可回滚",
  "request_id": "req_rollback_not_allowed_409"
}
```

发布与回滚需要串行执行：

```json
{
  "code": "PACKAGE_SERIALIZATION_REQUIRED",
  "message": "当前已有发布或回滚流程在执行",
  "request_id": "req_package_serial_409"
}
```

## 审计与实现建议

### `GET /api/v1/content/updates`

- 列表响应应统一返回 `meta.page/page_size/total/returned/has_more`
- 内容包摘要应保留最小可评审字段，不提前虚构完整业务对象
- `gray_visible` 只表达当前调用方是否可见，不替代完整投放策略

### `GET /api/v1/content/packages/{content_package_id}`

- 详情响应应统一返回 `request_id + data + meta`
- `gray_scope` 仅在灰度或已配置灰度时返回
- 审计字段应与主草案中的 `created_at/updated_at/created_by/updated_by` 保持一致

### `POST /api/v1/ops/content-packages/{id}/release`

- 应支持 `Idempotency-Key`
- 应返回统一 `audit` 字段，记录操作者、原因和目标对象
- 发布前应确认对象已通过审核且满足状态前置条件

### `POST /api/v1/ops/content-packages/{id}/rollback`

- 应支持 `Idempotency-Key`
- 回滚最小单位必须是 `content_package_id`
- 发布与回滚必须串行执行

## 建议下一步

1. 继续补第三批世界、任务与运营审核接口的独立样例文档
2. 再把样例文档与 `docs/30-api/openapi-v1-draft.yaml` 的复用层进一步抽象对齐
3. 最后评估是否按服务拆分更细的接口文档

## 与其他文档的关系

- `docs/30-api/api-overview.md`
  - 作为内容接口的上游总览，定义接口入口、职责和服务归属
- `docs/30-api/api-permissions.md`
  - 定义内容查询、发布与回滚接口的角色边界和审计要求
- `docs/30-api/api-error-codes.md`
  - 定义本文件中成功与失败样例所对应的错误码语义
- `docs/20-specs/backend-data-spec.md`
  - 作为更高权威的执行规范，约束内容生命周期、审计字段和接口实现边界
- `docs/30-api/openapi-draft.md`
  - 作为本文件后续下沉到 OpenAPI 草案的汇总入口
- `docs/30-api/openapi-v1-draft.yaml`
  - 当前单文件 OpenAPI 草案输出，是本文件样例结构的直接契约来源

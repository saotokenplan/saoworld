# 生成接口样例

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本文档用于补充生成请求创建、查询以及生成对象查询链路的请求响应样例，帮助后续服务端实现、客户端接入以及 OpenAPI 草案下沉时保持一致的契约形态。

## 适用范围

- 适用于 `POST /api/v1/ops/generation/requests`
- 适用于 `GET /api/v1/ops/generation/requests`
- 适用于 `GET /api/v1/ops/generation/requests/{request_id}`
- 适用于 `GET /api/v1/ops/generation/objects`
- 适用于 `GET /api/v1/ops/generation/objects/{object_id}`
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

## `POST /api/v1/ops/generation/requests`

### 作用

- 创建内容生成请求（运营接口）
- 返回统一幂等与审计信息
- 创建前自动校验世界骨架快照

### 请求示例

```http
POST /api/v1/ops/generation/requests HTTP/1.1
Authorization: Bearer <ops_token>
Content-Type: application/json
Accept: application/json
Idempotency-Key: 8dbdfe06-6c75-49f2-a177-bf6d3d7a85d1
X-Trace-Id: trace_generation_001
```

```json
{
  "chapter_id": "chapter_02",
  "region_id": "region_ruins_02",
  "generation_type": "npc",
  "count": 3,
  "params": {
    "faction": "shadow_veil",
    "role": "scout",
    "personality_tags": ["cunning", "mysterious"]
  },
  "reason": "投票结果触发：暗影面纱阵营新增侦察兵 NPC"
}
```

### 成功响应示例

```json
{
  "request_id": "req_generation_create_001",
  "trace_id": "trace_generation_001",
  "data": {
    "generation_request_id": "gen_20260629_001",
    "status": "pending",
    "chapter_id": "chapter_02",
    "region_id": "region_ruins_02",
    "generation_type": "npc",
    "count": 3
  },
  "meta": {
    "resource_type": "generation_request",
    "idempotent_replay": false,
    "accepted_at": "2026-06-29T14:00:00Z",
    "audit_record_id": "audit_generation_create_001"
  },
  "audit": {
    "audit_record_id": "audit_generation_create_001",
    "operator_id": "ops_001",
    "operator_role": "ops",
    "action": "generation_request.create",
    "target_id": "gen_20260629_001",
    "reason": "投票结果触发：暗影面纱阵营新增侦察兵 NPC",
    "result": "accepted",
    "occurred_at": "2026-06-29T14:00:00Z",
    "trace_id": "trace_generation_001"
  }
}
```

### 常见错误

世界骨架快照不存在：

```json
{
  "code": "SKELETON_NOT_FOUND",
  "message": "当前活跃世界骨架快照不存在",
  "request_id": "req_generation_skeleton_404"
}
```

forbidden_tags 为空：

```json
{
  "code": "FORBIDDEN_TAGS_EMPTY",
  "message": "世界骨架快照的 forbidden_tags 不能为空",
  "request_id": "req_generation_forbidden_tags_400"
}
```

章节ID无效：

```json
{
  "code": "INVALID_CHAPTER_ID",
  "message": "章节ID无效或不在世界骨架快照中",
  "request_id": "req_generation_chapter_400"
}
```

区域ID无效：

```json
{
  "code": "INVALID_REGION_ID",
  "message": "区域ID无效或不在世界骨架快照中",
  "request_id": "req_generation_region_400"
}
```

## `GET /api/v1/ops/generation/requests`

### 作用

- 获取生成请求列表（运营接口）
- 返回生成请求摘要和统一分页 `meta`
- 支持按状态、类型筛选

### 请求示例

```http
GET /api/v1/ops/generation/requests?page=1&page_size=20&status=processing&generation_type=npc HTTP/1.1
Authorization: Bearer <ops_token>
Accept: application/json
```

### 成功响应示例

```json
{
  "request_id": "req_generation_list_001",
  "data": [
    {
      "generation_request_id": "gen_20260629_001",
      "chapter_id": "chapter_02",
      "region_id": "region_ruins_02",
      "generation_type": "npc",
      "status": "processing",
      "count": 3,
      "progress": 66,
      "created_at": "2026-06-29T14:00:00Z",
      "updated_at": "2026-06-29T14:30:00Z"
    }
  ],
  "meta": {
    "resource_type": "generation_request",
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
  "request_id": "req_generation_list_002",
  "data": [],
  "meta": {
    "resource_type": "generation_request",
    "page": 1,
    "page_size": 20,
    "total": 0,
    "returned": 0,
    "has_more": false
  }
}
```

## `GET /api/v1/ops/generation/requests/{request_id}`

### 作用

- 获取生成请求详情（运营接口）
- 返回生成请求完整信息和审计字段

### 请求示例

```http
GET /api/v1/ops/generation/requests/gen_20260629_001 HTTP/1.1
Authorization: Bearer <ops_token>
Accept: application/json
```

### 成功响应示例

```json
{
  "request_id": "req_generation_detail_001",
  "data": {
    "generation_request_id": "gen_20260629_001",
    "chapter_id": "chapter_02",
    "region_id": "region_ruins_02",
    "generation_type": "npc",
    "status": "succeeded",
    "count": 3,
    "progress": 100,
    "params": {
      "faction": "shadow_veil",
      "role": "scout",
      "personality_tags": ["cunning", "mysterious"]
    },
    "generated_object_ids": ["object_npc_001", "object_npc_002", "object_npc_003"],
    "error_message": null,
    "created_at": "2026-06-29T14:00:00Z",
    "updated_at": "2026-06-29T14:45:00Z",
    "created_by": "ops_001",
    "updated_by": "system_generation_pipeline"
  },
  "meta": {
    "resource_type": "generation_request"
  }
}
```

### 失败请求响应示例

```json
{
  "request_id": "req_generation_detail_002",
  "data": {
    "generation_request_id": "gen_20260629_002",
    "chapter_id": "chapter_02",
    "region_id": "region_ruins_02",
    "generation_type": "quest",
    "status": "failed_permanent",
    "count": 5,
    "progress": 40,
    "params": {},
    "generated_object_ids": ["object_quest_001", "object_quest_002"],
    "error_message": "内容安全检查未通过，生成中止",
    "created_at": "2026-06-29T15:00:00Z",
    "updated_at": "2026-06-29T15:20:00Z",
    "created_by": "ops_001",
    "updated_by": "system_generation_pipeline"
  },
  "meta": {
    "resource_type": "generation_request"
  }
}
```

### 常见错误

生成请求不存在：

```json
{
  "code": "GENERATION_REQUEST_NOT_FOUND",
  "message": "生成请求不存在",
  "request_id": "req_generation_detail_404"
}
```

## `GET /api/v1/ops/generation/objects`

### 作用

- 获取生成对象列表（运营接口）
- 返回生成对象摘要和统一分页 `meta`
- 支持按状态、类型筛选

### 请求示例

```http
GET /api/v1/ops/generation/objects?page=1&page_size=20&status=pending_review&object_type=npc HTTP/1.1
Authorization: Bearer <ops_token>
Accept: application/json
```

### 成功响应示例

```json
{
  "request_id": "req_generated_objects_001",
  "data": [
    {
      "generated_object_id": "object_npc_001",
      "generation_request_id": "gen_20260629_001",
      "object_type": "npc",
      "object_title": "露娜·暗星",
      "status": "pending_review",
      "quality_score": 0.88,
      "created_at": "2026-06-29T14:10:00Z",
      "updated_at": "2026-06-29T14:10:00Z"
    },
    {
      "generated_object_id": "object_npc_002",
      "generation_request_id": "gen_20260629_001",
      "object_type": "npc",
      "object_title": "暗影侦察兵",
      "status": "pending_review",
      "quality_score": 0.79,
      "created_at": "2026-06-29T14:15:00Z",
      "updated_at": "2026-06-29T14:15:00Z"
    }
  ],
  "meta": {
    "resource_type": "generated_object",
    "page": 1,
    "page_size": 20,
    "total": 2,
    "returned": 2,
    "has_more": false
  }
}
```

## `GET /api/v1/ops/generation/objects/{object_id}`

### 作用

- 获取生成对象详情（运营接口）
- 返回生成对象完整信息和审计字段

### 请求示例

```http
GET /api/v1/ops/generation/objects/object_npc_001 HTTP/1.1
Authorization: Bearer <ops_token>
Accept: application/json
```

### 成功响应示例

```json
{
  "request_id": "req_generated_object_detail_001",
  "data": {
    "generated_object_id": "object_npc_001",
    "generation_request_id": "gen_20260629_001",
    "object_type": "npc",
    "object_title": "露娜·暗星",
    "status": "pending_review",
    "quality_score": 0.88,
    "content_payload": {
      "name": "露娜·暗星",
      "faction": "shadow_veil",
      "role": "scout",
      "personality": ["cunning", "mysterious"],
      "backstory": "来自暗影面纱的精英侦察兵，擅长在废墟中潜行...",
      "dialogues": ["你是谁？...", "小心点..."]
    },
    "review_score": null,
    "review_comments": [],
    "created_at": "2026-06-29T14:10:00Z",
    "updated_at": "2026-06-29T14:10:00Z",
    "created_by": "system_generation_pipeline",
    "updated_by": "system_generation_pipeline"
  },
  "meta": {
    "resource_type": "generated_object"
  }
}
```

### 常见错误

生成对象不存在：

```json
{
  "code": "GENERATED_OBJECT_NOT_FOUND",
  "message": "生成对象不存在",
  "request_id": "req_generated_object_404"
}
```

## 审计与实现建议

### `POST /api/v1/ops/generation/requests`

- 应支持 `Idempotency-Key`
- 创建前必须校验世界骨架快照存在且 `forbidden_tags` 非空
- 应返回统一 `audit` 字段，记录操作者、原因和目标对象

### `GET /api/v1/ops/generation/requests`

- 列表响应应统一返回 `meta.page/page_size/total/returned/has_more`
- 支持按状态、类型、章节、区域筛选

### `GET /api/v1/ops/generation/requests/{request_id}`

- 详情响应应统一返回 `request_id + data + meta`
- 失败请求应包含错误信息

### `GET /api/v1/ops/generation/objects`

- 列表响应应统一返回 `meta.page/page_size/total/returned/has_more`
- 支持按状态、类型、生成请求筛选

## 与其他文档的关系

- `docs/30-api/api-overview.md`
  - 作为生成接口的上游总览，定义接口入口、职责和服务归属
- `docs/30-api/api-permissions.md`
  - 定义生成接口的角色边界和审计要求
- `docs/30-api/api-error-codes.md`
  - 定义本文件中成功与失败样例所对应的错误码语义
- `docs/20-specs/backend-data-spec.md`
  - 作为更高权威的执行规范，约束生成数据模型和接口实现边界
- `docs/30-api/openapi-draft.md`
  - 作为本文件后续下沉到 OpenAPI 草案的汇总入口
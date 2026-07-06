# 玩家接口样例

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本文档用于补充玩家信息、任务列表、区域状态以及运营玩家管理链路的请求响应样例，帮助后续服务端实现、客户端接入以及 OpenAPI 草案下沉时保持一致的契约形态。

## 适用范围

- 适用于 `GET /api/v1/player/info`
- 适用于 `GET /api/v1/player/quests`
- 适用于 `GET /api/v1/player/regions`
- 适用于 `POST /api/v1/ops/players`
- 适用于 `GET /api/v1/ops/players`
- 适用于 `GET /api/v1/ops/players/{player_id}`
- 适用于 `PUT /api/v1/ops/players/{player_id}`
- 适用于 `POST /api/v1/ops/players/{player_id}/regions/{region_id}/unlock`
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

## `GET /api/v1/player/info`

### 作用

- 获取当前玩家基本信息
- 返回玩家身份、章节进度、声望等摘要信息

### 请求示例

```http
GET /api/v1/player/info HTTP/1.1
Authorization: Bearer <player_token>
Accept: application/json
```

### 成功响应示例

```json
{
  "request_id": "req_player_info_001",
  "data": {
    "player_id": "player_001",
    "player_name": "艾瑞尔",
    "chapter_id": "chapter_02",
    "chapter_progress": 65,
    "level": 12,
    "experience": 3450,
    "reputation": {
      "ironward_alliance": 1200,
      "free_territory": 850,
      "shadow_veil": -200,
      "harvest_guild": 500
    },
    "created_at": "2026-06-01T08:00:00Z",
    "updated_at": "2026-06-29T10:00:00Z"
  },
  "meta": {
    "resource_type": "player"
  }
}
```

### 常见错误

玩家不存在：

```json
{
  "code": "PLAYER_NOT_FOUND",
  "message": "玩家不存在",
  "request_id": "req_player_info_404"
}
```

认证失败：

```json
{
  "code": "AUTHENTICATION_FAILED",
  "message": "认证失败",
  "request_id": "req_player_auth_401"
}
```

## `GET /api/v1/player/quests`

### 作用

- 获取当前玩家任务列表
- 返回任务摘要和统一分页 `meta`

### 请求示例

```http
GET /api/v1/player/quests?page=1&page_size=20 HTTP/1.1
Authorization: Bearer <player_token>
Accept: application/json
```

### 成功响应示例

```json
{
  "request_id": "req_player_quests_001",
  "data": [
    {
      "quest_id": "quest_ruins_scan_01",
      "chapter_id": "chapter_02",
      "active_region_id": "region_ruins_02",
      "title": "调查遗迹异变",
      "summary": "进入遗迹深处并完成三处异常点扫描。",
      "status": "active",
      "progress": 66,
      "objectives": [
        {
          "id": "obj_001",
          "description": "扫描遗迹入口异常点",
          "completed": true
        },
        {
          "id": "obj_002",
          "description": "扫描遗迹中心异常点",
          "completed": true
        },
        {
          "id": "obj_003",
          "description": "扫描遗迹深处异常点",
          "completed": false
        }
      ],
      "rewards": {
        "experience": 500,
        "gold": 200,
        "reputation": {
          "ironward_alliance": 100
        }
      },
      "created_at": "2026-06-29T09:05:00Z",
      "updated_at": "2026-06-29T10:00:00Z"
    }
  ],
  "meta": {
    "resource_type": "player_quest",
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
  "request_id": "req_player_quests_002",
  "data": [],
  "meta": {
    "resource_type": "player_quest",
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

## `GET /api/v1/player/regions`

### 作用

- 获取当前玩家已解锁区域列表
- 返回区域状态和解锁时间

### 请求示例

```http
GET /api/v1/player/regions?page=1&page_size=20 HTTP/1.1
Authorization: Bearer <player_token>
Accept: application/json
```

### 成功响应示例

```json
{
  "request_id": "req_player_regions_001",
  "data": [
    {
      "region_id": "region_wasteland_01",
      "chapter_id": "chapter_02",
      "title": "荒原边境",
      "summary": "玩家已解锁的荒原外围区域。",
      "status": "active",
      "unlocked_at": "2026-06-05T08:00:00Z",
      "exploration_progress": 75,
      "created_at": "2026-06-01T08:00:00Z",
      "updated_at": "2026-06-29T10:00:00Z"
    },
    {
      "region_id": "region_ruins_02",
      "chapter_id": "chapter_02",
      "title": "遗迹深处",
      "summary": "当前章节主线推进后的新探索区域。",
      "status": "unstable",
      "unlocked_at": "2026-06-28T08:00:00Z",
      "exploration_progress": 15,
      "created_at": "2026-06-01T08:00:00Z",
      "updated_at": "2026-06-29T10:00:00Z"
    }
  ],
  "meta": {
    "resource_type": "player_region",
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
  "request_id": "req_player_regions_002",
  "data": [],
  "meta": {
    "resource_type": "player_region",
    "page": 1,
    "page_size": 20,
    "total": 0,
    "returned": 0,
    "has_more": false
  }
}
```

## `POST /api/v1/ops/players`

### 作用

- 创建玩家账号
- 返回统一幂等与审计信息

### 请求示例

```http
POST /api/v1/ops/players HTTP/1.1
Authorization: Bearer <ops_token>
Content-Type: application/json
Accept: application/json
Idempotency-Key: 8dbdfe06-6c75-49f2-a177-bf6d3d7a85d1
X-Trace-Id: trace_player_create_001
```

```json
{
  "player_name": "新玩家",
  "chapter_id": "chapter_01",
  "reason": "新账号创建"
}
```

### 成功响应示例

```json
{
  "request_id": "req_ops_player_create_001",
  "trace_id": "trace_player_create_001",
  "data": {
    "player_id": "player_002",
    "player_name": "新玩家",
    "chapter_id": "chapter_01",
    "status": "active"
  },
  "meta": {
    "resource_type": "player",
    "idempotent_replay": false,
    "accepted_at": "2026-06-29T11:00:00Z",
    "audit_record_id": "audit_player_create_001"
  },
  "audit": {
    "audit_record_id": "audit_player_create_001",
    "operator_id": "ops_001",
    "operator_role": "ops",
    "action": "player.create",
    "target_id": "player_002",
    "reason": "新账号创建",
    "result": "created",
    "occurred_at": "2026-06-29T11:00:00Z",
    "trace_id": "trace_player_create_001"
  }
}
```

### 常见错误

玩家名已存在：

```json
{
  "code": "PLAYER_NAME_EXISTS",
  "message": "玩家名已被使用",
  "request_id": "req_player_create_409"
}
```

## `GET /api/v1/ops/players`

### 作用

- 获取玩家列表（运营接口）
- 返回玩家摘要和统一分页 `meta`

### 请求示例

```http
GET /api/v1/ops/players?page=1&page_size=20&chapter_id=chapter_02 HTTP/1.1
Authorization: Bearer <ops_token>
Accept: application/json
```

### 成功响应示例

```json
{
  "request_id": "req_ops_players_list_001",
  "data": [
    {
      "player_id": "player_001",
      "player_name": "艾瑞尔",
      "chapter_id": "chapter_02",
      "level": 12,
      "status": "active",
      "created_at": "2026-06-01T08:00:00Z",
      "updated_at": "2026-06-29T10:00:00Z"
    }
  ],
  "meta": {
    "resource_type": "player",
    "page": 1,
    "page_size": 20,
    "total": 1,
    "returned": 1,
    "has_more": false
  }
}
```

## `GET /api/v1/ops/players/{player_id}`

### 作用

- 获取玩家详情（运营接口）
- 返回玩家完整信息和审计字段

### 请求示例

```http
GET /api/v1/ops/players/player_001 HTTP/1.1
Authorization: Bearer <ops_token>
Accept: application/json
```

### 成功响应示例

```json
{
  "request_id": "req_ops_player_detail_001",
  "data": {
    "player_id": "player_001",
    "player_name": "艾瑞尔",
    "chapter_id": "chapter_02",
    "chapter_progress": 65,
    "level": 12,
    "experience": 3450,
    "reputation": {
      "ironward_alliance": 1200,
      "free_territory": 850,
      "shadow_veil": -200,
      "harvest_guild": 500
    },
    "status": "active",
    "created_at": "2026-06-01T08:00:00Z",
    "updated_at": "2026-06-29T10:00:00Z",
    "created_by": "system_player_creation",
    "updated_by": "system_player_update"
  },
  "meta": {
    "resource_type": "player"
  }
}
```

### 常见错误

玩家不存在：

```json
{
  "code": "PLAYER_NOT_FOUND",
  "message": "玩家不存在",
  "request_id": "req_ops_player_404"
}
```

## `PUT /api/v1/ops/players/{player_id}`

### 作用

- 更新玩家信息（运营接口）
- 返回统一幂等与审计信息

### 请求示例

```http
PUT /api/v1/ops/players/player_001 HTTP/1.1
Authorization: Bearer <ops_token>
Content-Type: application/json
Accept: application/json
Idempotency-Key: 92461d46-4423-4690-9170-682ee23f0ef1
X-Trace-Id: trace_player_update_001
```

```json
{
  "player_name": "艾瑞尔·铁盾",
  "chapter_id": "chapter_03",
  "reason": "玩家改名并推进章节"
}
```

### 成功响应示例

```json
{
  "request_id": "req_ops_player_update_001",
  "trace_id": "trace_player_update_001",
  "data": {
    "player_id": "player_001",
    "player_name": "艾瑞尔·铁盾",
    "chapter_id": "chapter_03",
    "status": "active"
  },
  "meta": {
    "resource_type": "player",
    "idempotent_replay": false,
    "accepted_at": "2026-06-29T12:00:00Z",
    "audit_record_id": "audit_player_update_001"
  },
  "audit": {
    "audit_record_id": "audit_player_update_001",
    "operator_id": "ops_001",
    "operator_role": "ops",
    "action": "player.update",
    "target_id": "player_001",
    "reason": "玩家改名并推进章节",
    "result": "updated",
    "occurred_at": "2026-06-29T12:00:00Z",
    "trace_id": "trace_player_update_001"
  }
}
```

## `POST /api/v1/ops/players/{player_id}/regions/{region_id}/unlock`

### 作用

- 解锁玩家区域（运营接口）
- 返回统一幂等与审计信息

### 请求示例

```http
POST /api/v1/ops/players/player_001/regions/region_ruins_03/unlock HTTP/1.1
Authorization: Bearer <ops_token>
Content-Type: application/json
Accept: application/json
Idempotency-Key: 62fa9d07-4d29-4cf2-b4bf-61b2e579cc4f
X-Trace-Id: trace_region_unlock_001
```

```json
{
  "reason": "运营手动解锁新区域"
}
```

### 成功响应示例

```json
{
  "request_id": "req_ops_region_unlock_001",
  "trace_id": "trace_region_unlock_001",
  "data": {
    "player_id": "player_001",
    "region_id": "region_ruins_03",
    "unlocked": true,
    "unlocked_at": "2026-06-29T13:00:00Z"
  },
  "meta": {
    "resource_type": "player_region",
    "idempotent_replay": false,
    "accepted_at": "2026-06-29T13:00:00Z",
    "audit_record_id": "audit_region_unlock_001"
  },
  "audit": {
    "audit_record_id": "audit_region_unlock_001",
    "operator_id": "ops_001",
    "operator_role": "ops",
    "action": "player_region.unlock",
    "target_id": "player_001:region_ruins_03",
    "reason": "运营手动解锁新区域",
    "result": "unlocked",
    "occurred_at": "2026-06-29T13:00:00Z",
    "trace_id": "trace_region_unlock_001"
  }
}
```

### 常见错误

区域不存在：

```json
{
  "code": "REGION_NOT_FOUND",
  "message": "区域不存在",
  "request_id": "req_region_unlock_404"
}
```

区域已解锁：

```json
{
  "code": "REGION_ALREADY_UNLOCKED",
  "message": "区域已解锁",
  "request_id": "req_region_unlock_409"
}
```

## 审计与实现建议

### `GET /api/v1/player/info`

- 详情响应应统一返回 `request_id + data + meta`
- 声望字段应保持与世界观设定一致的阵营键名

### `GET /api/v1/player/quests`

- 列表响应应统一返回 `meta.page/page_size/total/returned/has_more`
- 任务进度应明确表达完成百分比

### `GET /api/v1/player/regions`

- 列表响应应统一返回 `meta.page/page_size/total/returned/has_more`
- 探索进度应明确表达完成百分比

### `POST /api/v1/ops/players`

- 应支持 `Idempotency-Key`
- 应返回统一 `audit` 字段，记录操作者、原因和目标对象

### `POST /api/v1/ops/players/{player_id}/regions/{region_id}/unlock`

- 应支持 `Idempotency-Key`
- 解锁前应校验玩家和区域存在性

## 与其他文档的关系

- `docs/30-api/api-overview.md`
  - 作为玩家接口的上游总览，定义接口入口、职责和服务归属
- `docs/30-api/api-permissions.md`
  - 定义玩家接口的角色边界和审计要求
- `docs/30-api/api-error-codes.md`
  - 定义本文件中成功与失败样例所对应的错误码语义
- `docs/20-specs/backend-data-spec.md`
  - 作为更高权威的执行规范，约束玩家数据模型和接口实现边界
- `docs/30-api/openapi-draft.md`
  - 作为本文件后续下沉到 OpenAPI 草案的汇总入口
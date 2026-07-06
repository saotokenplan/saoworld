# 运营接口样例

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本文档用于补充运营后台仪表盘、运营操作记录、系统状态监控链路的请求响应样例，帮助后续服务端实现、客户端接入以及 OpenAPI 草案下沉时保持一致的契约形态。

## 适用范围

- 适用于 `GET /api/v1/ops/dashboard`
- 适用于 `GET /api/v1/ops/dashboard/history`
- 适用于 `GET /api/v1/ops/actions`
- 适用于 `GET /api/v1/ops/actions/{action_id}`
- 适用于 `GET /api/v1/ops/system/status`
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

## `GET /api/v1/ops/dashboard`

### 作用

- 获取运营仪表盘（运营接口）
- 返回关键指标汇总和服务状态概览

### 请求示例

```http
GET /api/v1/ops/dashboard HTTP/1.1
Authorization: Bearer <ops_token>
Accept: application/json
```

### 成功响应示例

```json
{
  "request_id": "req_ops_dashboard_001",
  "data": {
    "overview": {
      "total_players": 128430,
      "active_players": 8520,
      "new_players_today": 120,
      "total_vote_cycles": 15,
      "current_vote_cycle": "cycle_202607",
      "current_vote_status": "open"
    },
    "content_metrics": {
      "total_content_packages": 42,
      "live_packages": 28,
      "gray_packages": 3,
      "archived_packages": 11,
      "rolled_back_packages": 0
    },
    "generation_metrics": {
      "total_generation_requests": 286,
      "pending_requests": 5,
      "processing_requests": 2,
      "succeeded_requests": 275,
      "failed_requests": 4
    },
    "review_metrics": {
      "total_reviews": 1240,
      "pending_reviews": 18,
      "approved_reviews": 1192,
      "rejected_reviews": 30
    },
    "service_status": {
      "vote-service": "ok",
      "world-service": "ok",
      "content-service": "ok",
      "generation-service": "ok",
      "review-service": "ok",
      "player-service": "ok",
      "ops-service": "ok",
      "gateway-service": "ok"
    }
  },
  "meta": {
    "resource_type": "ops_dashboard",
    "generated_at": "2026-06-29T15:00:00Z"
  }
}
```

## `GET /api/v1/ops/dashboard/history`

### 作用

- 获取运营仪表盘历史记录（运营接口）
- 返回关键指标历史趋势和统一分页 `meta`

### 请求示例

```http
GET /api/v1/ops/dashboard/history?page=1&page_size=30&start_date=2026-06-01&end_date=2026-06-29 HTTP/1.1
Authorization: Bearer <ops_token>
Accept: application/json
```

### 成功响应示例

```json
{
  "request_id": "req_ops_dashboard_history_001",
  "data": [
    {
      "timestamp": "2026-06-29T08:00:00Z",
      "total_players": 128430,
      "active_players": 8520,
      "new_players_today": 120,
      "content_packages": 42,
      "generation_requests": 286,
      "reviews": 1240
    },
    {
      "timestamp": "2026-06-28T08:00:00Z",
      "total_players": 127850,
      "active_players": 9200,
      "new_players_today": 150,
      "content_packages": 40,
      "generation_requests": 278,
      "reviews": 1205
    }
  ],
  "meta": {
    "resource_type": "ops_dashboard_history",
    "page": 1,
    "page_size": 30,
    "total": 29,
    "returned": 2,
    "has_more": true
  }
}
```

## `GET /api/v1/ops/actions`

### 作用

- 获取运营操作记录列表（运营接口）
- 返回操作记录摘要和统一分页 `meta`
- 支持按操作类型、操作者筛选

### 请求示例

```http
GET /api/v1/ops/actions?page=1&page_size=20&action_type=content_package.release&operator_id=ops_001 HTTP/1.1
Authorization: Bearer <ops_token>
Accept: application/json
```

### 成功响应示例

```json
{
  "request_id": "req_ops_actions_001",
  "data": [
    {
      "action_id": "action_001",
      "action_type": "content_package.release",
      "operator_id": "ops_001",
      "operator_role": "ops",
      "target_id": "pkg_chapter_02_ruins_20260629_01",
      "target_type": "content_package",
      "result": "completed",
      "reason": "首轮灰度发布",
      "created_at": "2026-06-29T10:05:00Z",
      "trace_id": "trace_release_001"
    },
    {
      "action_id": "action_002",
      "action_type": "vote_cycle.create",
      "operator_id": "ops_001",
      "operator_role": "ops",
      "target_id": "cycle_202607",
      "target_type": "vote_cycle",
      "result": "completed",
      "reason": "第三章主线剧情投票创建",
      "created_at": "2026-06-30T08:00:00Z",
      "trace_id": "trace_vote_cycle_001"
    }
  ],
  "meta": {
    "resource_type": "ops_action",
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
  "request_id": "req_ops_actions_002",
  "data": [],
  "meta": {
    "resource_type": "ops_action",
    "page": 1,
    "page_size": 20,
    "total": 0,
    "returned": 0,
    "has_more": false
  }
}
```

## `GET /api/v1/ops/actions/{action_id}`

### 作用

- 获取运营操作详情（运营接口）
- 返回操作完整信息和审计字段

### 请求示例

```http
GET /api/v1/ops/actions/action_001 HTTP/1.1
Authorization: Bearer <ops_token>
Accept: application/json
```

### 成功响应示例

```json
{
  "request_id": "req_ops_action_detail_001",
  "data": {
    "action_id": "action_001",
    "action_type": "content_package.release",
    "operator_id": "ops_001",
    "operator_role": "ops",
    "target_id": "pkg_chapter_02_ruins_20260629_01",
    "target_type": "content_package",
    "result": "completed",
    "reason": "首轮灰度发布",
    "details": {
      "release_mode": "gray",
      "gray_scope": {
        "region_ids": ["region_ruins_02"],
        "player_percent": 10
      }
    },
    "created_at": "2026-06-29T10:05:00Z",
    "trace_id": "trace_release_001",
    "audit_record_id": "audit_release_001"
  },
  "meta": {
    "resource_type": "ops_action"
  }
}
```

### 常见错误

操作记录不存在：

```json
{
  "code": "OPS_ACTION_NOT_FOUND",
  "message": "操作记录不存在",
  "request_id": "req_ops_action_404"
}
```

## `GET /api/v1/ops/system/status`

### 作用

- 获取系统状态（运营接口）
- 返回所有后端服务的实时健康状态

### 请求示例

```http
GET /api/v1/ops/system/status HTTP/1.1
Authorization: Bearer <ops_token>
Accept: application/json
```

### 成功响应示例

```json
{
  "request_id": "req_ops_system_status_001",
  "data": {
    "overall_status": "healthy",
    "services": [
      {
        "service_name": "vote-service",
        "service_url": "http://vote-service:8001/api/v1/health",
        "status": "ok",
        "response_time_ms": 25,
        "last_checked_at": "2026-06-29T15:00:00Z"
      },
      {
        "service_name": "world-service",
        "service_url": "http://world-service:8002/api/v1/health",
        "status": "ok",
        "response_time_ms": 32,
        "last_checked_at": "2026-06-29T15:00:00Z"
      },
      {
        "service_name": "content-service",
        "service_url": "http://content-service:8003/api/v1/health",
        "status": "ok",
        "response_time_ms": 28,
        "last_checked_at": "2026-06-29T15:00:00Z"
      },
      {
        "service_name": "generation-service",
        "service_url": "http://generation-service:8004/api/v1/health",
        "status": "ok",
        "response_time_ms": 45,
        "last_checked_at": "2026-06-29T15:00:00Z"
      },
      {
        "service_name": "review-service",
        "service_url": "http://review-service:8005/api/v1/health",
        "status": "ok",
        "response_time_ms": 22,
        "last_checked_at": "2026-06-29T15:00:00Z"
      },
      {
        "service_name": "player-service",
        "service_url": "http://player-service:8006/api/v1/health",
        "status": "ok",
        "response_time_ms": 30,
        "last_checked_at": "2026-06-29T15:00:00Z"
      },
      {
        "service_name": "ops-service",
        "service_url": "http://ops-service:8007/api/v1/health",
        "status": "ok",
        "response_time_ms": 15,
        "last_checked_at": "2026-06-29T15:00:00Z"
      },
      {
        "service_name": "gateway-service",
        "service_url": "http://gateway-service:8000/api/v1/health",
        "status": "ok",
        "response_time_ms": 20,
        "last_checked_at": "2026-06-29T15:00:00Z"
      }
    ],
    "database": {
      "status": "ok",
      "connection_pool": "healthy"
    },
    "redis": {
      "status": "ok",
      "connected": true
    }
  },
  "meta": {
    "resource_type": "system_status",
    "checked_at": "2026-06-29T15:00:00Z"
  }
}
```

### 部分服务异常响应示例

```json
{
  "request_id": "req_ops_system_status_002",
  "data": {
    "overall_status": "degraded",
    "services": [
      {
        "service_name": "generation-service",
        "service_url": "http://generation-service:8004/api/v1/health",
        "status": "unavailable",
        "response_time_ms": 30000,
        "last_checked_at": "2026-06-29T15:00:00Z",
        "error": "连接超时"
      }
    ],
    "database": {
      "status": "ok",
      "connection_pool": "healthy"
    },
    "redis": {
      "status": "ok",
      "connected": true
    }
  },
  "meta": {
    "resource_type": "system_status",
    "checked_at": "2026-06-29T15:00:00Z"
  }
}
```

## 审计与实现建议

### `GET /api/v1/ops/dashboard`

- 详情响应应统一返回 `request_id + data + meta`
- 服务状态应通过实际 HTTP 调用获取，而非硬编码

### `GET /api/v1/ops/dashboard/history`

- 列表响应应统一返回 `meta.page/page_size/total/returned/has_more`
- 支持按日期范围筛选

### `GET /api/v1/ops/actions`

- 列表响应应统一返回 `meta.page/page_size/total/returned/has_more`
- 支持按操作类型、操作者、时间范围筛选

### `GET /api/v1/ops/actions/{action_id}`

- 详情响应应统一返回 `request_id + data + meta`
- 操作详情应包含完整的操作参数

### `GET /api/v1/ops/system/status`

- 应实际调用各服务的健康检查接口
- 应设置合理的超时时间
- 应返回响应时间用于性能监控

## 与其他文档的关系

- `docs/30-api/api-overview.md`
  - 作为运营接口的上游总览，定义接口入口、职责和服务归属
- `docs/30-api/api-permissions.md`
  - 定义运营接口的角色边界和审计要求
- `docs/30-api/api-error-codes.md`
  - 定义本文件中成功与失败样例所对应的错误码语义
- `docs/20-specs/backend-data-spec.md`
  - 作为更高权威的执行规范，约束运营数据模型和接口实现边界
- `docs/30-api/openapi-draft.md`
  - 作为本文件后续下沉到 OpenAPI 草案的汇总入口
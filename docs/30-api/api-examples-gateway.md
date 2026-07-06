# 网关接口样例

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本文档用于补充 API 网关健康检查、服务状态监控链路的请求响应样例，帮助后续服务端实现、客户端接入以及 OpenAPI 草案下沉时保持一致的契约形态。

## 适用范围

- 适用于 `GET /api/v1/health`
- 适用于 `GET /api/v1/health/services`
- 不替代接口总览、权限矩阵和错误码文档，而是作为具体接口层面的补充样例

## 当前定位

- 本文档是接口样例，不替代详细规范
- 接口边界以 `docs/30-api/api-overview.md` 为准
- 权限与审计要求以 `docs/30-api/api-permissions.md` 为准
- 错误码以 `docs/30-api/api-error-codes.md` 为准

## 通用约定

- 协议：`HTTPS + JSON`
- 认证：OIDC 签发的 JWT Bearer Token（`Authorization: Bearer <token>`），健康检查接口公开
- 时间格式：ISO 8601
- 响应统一使用 `request_id + data + meta`

## `GET /api/v1/health`

### 作用

- 服务健康检查（公开接口）
- 返回网关服务状态和基本信息

### 请求示例

```http
GET /api/v1/health HTTP/1.1
Accept: application/json
```

### 成功响应示例

```json
{
  "request_id": "req_health_001",
  "data": {
    "status": "healthy",
    "service_name": "gateway-service",
    "app_version": "0.1.0",
    "environment": "production",
    "timestamp": "2026-06-29T15:00:00Z"
  },
  "meta": {
    "resource_type": "health"
  }
}
```

### 服务异常响应示例

```json
{
  "request_id": "req_health_002",
  "data": {
    "status": "unhealthy",
    "service_name": "gateway-service",
    "app_version": "0.1.0",
    "environment": "production",
    "timestamp": "2026-06-29T15:00:00Z",
    "errors": [
      {
        "service": "redis",
        "status": "unavailable",
        "message": "Redis 连接失败"
      }
    ]
  },
  "meta": {
    "resource_type": "health"
  }
}
```

## `GET /api/v1/health/services`

### 作用

- 获取所有后端服务健康状态（公开接口）
- 返回各服务的实时状态和响应时间

### 请求示例

```http
GET /api/v1/health/services HTTP/1.1
Accept: application/json
```

### 成功响应示例

```json
{
  "request_id": "req_health_services_001",
  "data": {
    "gateway": {
      "status": "healthy",
      "app_version": "0.1.0",
      "timestamp": "2026-06-29T15:00:00Z"
    },
    "services": [
      {
        "name": "vote-service",
        "route": "/api/v1/votes",
        "status": "healthy",
        "response_time_ms": 25,
        "last_checked": "2026-06-29T15:00:00Z"
      },
      {
        "name": "world-service",
        "route": "/api/v1/world",
        "status": "healthy",
        "response_time_ms": 32,
        "last_checked": "2026-06-29T15:00:00Z"
      },
      {
        "name": "content-service",
        "route": "/api/v1/content",
        "status": "healthy",
        "response_time_ms": 28,
        "last_checked": "2026-06-29T15:00:00Z"
      },
      {
        "name": "generation-service",
        "route": "/api/v1/generation",
        "status": "healthy",
        "response_time_ms": 45,
        "last_checked": "2026-06-29T15:00:00Z"
      },
      {
        "name": "review-service",
        "route": "/api/v1/review",
        "status": "healthy",
        "response_time_ms": 22,
        "last_checked": "2026-06-29T15:00:00Z"
      },
      {
        "name": "player-service",
        "route": "/api/v1/player",
        "status": "healthy",
        "response_time_ms": 30,
        "last_checked": "2026-06-29T15:00:00Z"
      },
      {
        "name": "ops-service",
        "route": "/api/v1/ops",
        "status": "healthy",
        "response_time_ms": 15,
        "last_checked": "2026-06-29T15:00:00Z"
      }
    ],
    "overall_status": "healthy",
    "total_services": 7,
    "healthy_services": 7,
    "unhealthy_services": 0
  },
  "meta": {
    "resource_type": "health_services",
    "checked_at": "2026-06-29T15:00:00Z"
  }
}
```

### 部分服务异常响应示例

```json
{
  "request_id": "req_health_services_002",
  "data": {
    "gateway": {
      "status": "healthy",
      "app_version": "0.1.0",
      "timestamp": "2026-06-29T15:00:00Z"
    },
    "services": [
      {
        "name": "generation-service",
        "route": "/api/v1/generation",
        "status": "unhealthy",
        "response_time_ms": 30000,
        "last_checked": "2026-06-29T15:00:00Z",
        "error": "连接超时"
      }
    ],
    "overall_status": "degraded",
    "total_services": 7,
    "healthy_services": 6,
    "unhealthy_services": 1
  },
  "meta": {
    "resource_type": "health_services",
    "checked_at": "2026-06-29T15:00:00Z"
  }
}
```

## 审计与实现建议

### `GET /api/v1/health`

- 健康检查接口应公开，无需认证
- 响应应包含服务名称、版本、环境信息
- 异常时应返回具体错误信息

### `GET /api/v1/health/services`

- 应实际调用各服务的健康检查接口
- 应设置合理的超时时间
- 应返回响应时间用于性能监控
- 应统计健康和不健康服务数量

## 与其他文档的关系

- `docs/30-api/api-overview.md`
  - 作为网关接口的上游总览，定义接口入口、职责和服务归属
- `docs/30-api/api-permissions.md`
  - 定义网关接口的角色边界和审计要求
- `docs/30-api/api-error-codes.md`
  - 定义本文件中成功与失败样例所对应的错误码语义
- `docs/20-specs/backend-data-spec.md`
  - 作为更高权威的执行规范，约束网关数据模型和接口实现边界
- `docs/30-api/openapi-draft.md`
  - 作为本文件后续下沉到 OpenAPI 草案的汇总入口
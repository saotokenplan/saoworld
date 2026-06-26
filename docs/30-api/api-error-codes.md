# API 错误码

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本文档统一整理当前接口层的错误码、适用场景和建议 HTTP 状态码，作为 OpenAPI 草案、服务端异常映射和客户端错误处理策略的索引。

## 适用范围

- 适用于 `docs/30-api/` 目录下所有需要统一错误语义、HTTP 状态码和错误返回结构的接口参考文档。
- 适用于玩家接口、运营接口、审核接口以及系统相关接口的异常约束整理。
- 不替代 `docs/20-specs/backend-data-spec.md` 中的上游执行规范。

## 当前定位

- 本文档是错误码索引，不替代详细接口规范。
- 错误返回结构的正式 Schema 定义在 `docs/30-api/openapi-v1-draft.yaml` 的 `components/schemas` 中（`ErrorResponse`、`ErrorDetail` 及其特化类型）。
- 如果本文档与 `docs/20-specs/backend-data-spec.md` 冲突，以后者为准。
- 如果本文档与 `docs/30-api/openapi-v1-draft.yaml` 冲突，以 YAML 为准。

## 通用错误返回结构

所有接口错误响应统一使用以下结构（OpenAPI 中对应 `ErrorResponse` Schema）：

```json
{
  "code": "INVALID_VOTE_STATE",
  "message": "当前投票周期不可投票",
  "request_id": "req_vote_current_409",
  "details": [
    {
      "location": "body",
      "field": "candidate_id",
      "issue": "required"
    }
  ]
}
```

字段说明：

- `code`：稳定的大写下划线错误码，SDK 和客户端应基于此做分支判断
- `message`：面向调用方的可读消息，可直接展示或记录
- `request_id`：服务端请求追踪 ID，用于日志、链路追踪和问题排查，格式 `req_[a-zA-Z0-9_]+`
- `details`：可选的字段级错误细节数组，参数校验和鉴权类错误必须提供

### details.issue 分类

| 类别 | issue 值 | 说明 |
|---|---|---|
| 参数校验 | `required` | 缺少必填字段 |
| 参数校验 | `pattern_mismatch` | 字段格式不匹配正则（如路径参数 ID 格式错误） |
| 参数校验 | `unsupported_enum` | 枚举值不在允许范围内 |
| 参数校验 | `must_be_between_1_and_100` | 数值超出 1-100 范围（如 page_size） |
| 参数校验 | `min_items_2` | 数组元素少于最小数量 |
| 鉴权授权 | `missing_required_scope` | Token 缺少所需 scope |

## 错误码状态说明

- **已落地**：已在 `openapi-v1-draft.yaml` 中定义并被至少一个接口使用
- **预留**：已规划但当前 OpenAPI 草案中尚未被具体接口使用，服务端实现阶段按需启用

## 通用 HTTP 层错误码（已落地）

| 错误码 | HTTP 状态码 | 说明 | 对应 Schema |
|---|---|---|---|
| `INVALID_ARGUMENT` | `400` | 请求参数非法（缺字段、格式错误、枚举非法等） | `ValidationErrorResponse` / `PathParameterErrorResponse` |
| `INVALID_TOKEN` | `401` | Token 格式或签名非法、未认证 | `UnauthorizedErrorResponse` |
| `INSUFFICIENT_SCOPE` | `403` | 访问令牌缺少所需作用域 | `ScopeErrorResponse` |
| `RESOURCE_NOT_FOUND` | `404` | 目标资源不存在 | `NotFoundErrorResponse` |
| `CONFLICT` | `409` | 资源状态冲突（通用） | `ConflictErrorResponse` |
| `RATE_LIMITED` | `429` | 触发限流或频率限制 | `RateLimitedErrorResponse` |
| `SERVICE_UNAVAILABLE` | `503` | 服务暂不可用 | `ServiceUnavailableErrorResponse` |

## 预留错误码（未在当前 OpenAPI 中使用）

| 错误码 | HTTP 状态码 | 说明 | 预计使用阶段 |
|---|---|---|---|
| `TOKEN_EXPIRED` | `401` | Access Token 已过期（与 INVALID_TOKEN 区分，提示刷新） | 接入 Refresh Token 后 |
| `INTERNAL_ERROR` | `500` | 服务内部未知异常 | 服务端实现时 |
| `AUDIT_WRITE_FAILED` | `500` | 审计记录写入失败 | 服务端实现时 |
| `TRACE_ID_MISSING` | `500` | 系统未正确生成链路追踪字段 | 服务端实现时 |
| `TASK_DISPATCH_FAILED` | `503` | 异步任务分发失败 | 接入任务队列后 |
| `DEPENDENCY_UNAVAILABLE` | `503` | 下游依赖或队列不可用 | 接入外部依赖后 |

## 投票接口错误码（已落地）

| 错误码 | HTTP 状态码 | 说明 | 适用接口 |
|---|---|---|---|
| `VOTE_CYCLE_NOT_FOUND` | `404` | 当前不存在有效投票周期 | `GET /votes/current` `POST /votes/submit` |
| `INVALID_VOTE_STATE` | `409` | 当前投票周期不可投票 | `GET /votes/current` |
| `PLAYER_NOT_ELIGIBLE` | `403` | 玩家不满足投票资格 | `POST /votes/submit` |
| `VOTE_RISK_BLOCKED` | `403` | 命中设备或行为风控 | `POST /votes/submit` |
| `CANDIDATE_NOT_FOUND` | `404` | 候选项不存在 | `POST /votes/submit` |
| `VOTE_CYCLE_CLOSED` | `409` | 投票周期已关闭 | `POST /votes/submit` |
| `CANDIDATE_OUT_OF_SCOPE` | `409` | 候选项不属于当前投票周期 | `POST /votes/submit` |
| `DUPLICATE_VOTE` | `409` | 同一玩家在同一周期重复投票 | `POST /votes/submit` |

## 内容查询接口错误码（已落地）

| 错误码 | HTTP 状态码 | 说明 | 适用接口 |
|---|---|---|---|
| `CONTENT_PACKAGE_NOT_FOUND` | `404` | 内容包不存在 | `GET /content/packages/{id}` |
| `CONTENT_PACKAGE_NOT_VISIBLE` | `403` | 内容包对当前玩家不可见 | `GET /content/packages/{id}` |
| `CONTENT_UPDATES_UNAVAILABLE` | `503` | 内容更新列表暂不可用 | `GET /content/updates` |

## 世界与任务接口错误码（已落地）

| 错误码 | HTTP 状态码 | 说明 | 适用接口 |
|---|---|---|---|
| `REGION_NOT_FOUND` | `404` | 区域不存在 | `GET /world/regions/{region_id}` |
| `REGION_NOT_VISIBLE` | `403` | 区域当前对玩家不可见 | `GET /world/regions/{region_id}` |
| `QUEST_LIST_UNAVAILABLE` | `503` | 任务列表暂不可用 | `GET /quests` |

## 运营与审核接口错误码（已落地）

| 错误码 | HTTP 状态码 | 说明 | 适用接口 |
|---|---|---|---|
| `REASON_REQUIRED` | `400` | 敏感操作缺少原因字段 | 所有运营写接口 |
| `CONTENT_RELEASE_FORBIDDEN` | `403` | 无内容发布权限 | `POST /ops/content-packages/{id}/release` |
| `CONTENT_ROLLBACK_FORBIDDEN` | `403` | 无内容回滚权限 | `POST /ops/content-packages/{id}/rollback` |
| `CONTENT_PACKAGE_NOT_RELEASABLE` | `409` | 内容包不满足发布前置条件 | `POST /ops/content-packages/{id}/release` |
| `CONTENT_PACKAGE_ALREADY_LIVE` | `409` | 内容包已处于正式生效状态 | `POST /ops/content-packages/{id}/release` |
| `PACKAGE_SERIALIZATION_REQUIRED` | `409` | 当前已有发布或回滚流程在执行 | release/rollback |
| `CONTENT_PACKAGE_NOT_ROLLBACKABLE` | `409` | 内容包当前不可回滚 | `POST /ops/content-packages/{id}/rollback` |
| `ROLLBACK_TARGET_INVALID` | `400` | 回滚目标版本非法 | `POST /ops/content-packages/{id}/rollback` |
| `VOTE_CYCLE_CONFLICT` | `409` | 投票周期创建冲突 | `POST /ops/vote-cycles` |
| `REVIEW_OBJECT_NOT_FOUND` | `404` | 审核对象不存在 | `POST /ops/review/{object_id}/approve` |
| `REVIEW_APPROVAL_FORBIDDEN` | `403` | 无审核批准权限 | `POST /ops/review/{object_id}/approve` |
| `INVALID_REVIEW_STATE` | `409` | 当前对象不处于可批准状态 | `POST /ops/review/{object_id}/approve` |

## 内容生命周期错误码（预留）

这些错误码在内容状态流更完整（含生成、打包、审核状态机）后启用：

| 错误码 | HTTP 状态码 | 说明 |
|---|---|---|
| `INVALID_OBJECT_STATE` | `409` | 内容对象当前状态不支持本次操作 |
| `OBJECT_NOT_REVIEWED` | `409` | 对象尚未完成审核 |
| `OBJECT_NOT_PACKAGED` | `409` | 对象尚未进入内容包 |
| `PACKAGE_NOT_GRAY_READY` | `409` | 内容包未满足灰度前置条件 |
| `PACKAGE_NOT_LIVE_READY` | `409` | 内容包未满足正式上线前置条件 |

## 使用建议

### 客户端

- 对 `401` 和 `403` 做明确鉴权提示，不要混用。
- 对 `400` 带 `details` 的错误，可按 `field` 和 `issue` 做表单级错误映射。
- 对 `409` 做状态冲突处理，不要直接重试所有请求。
- 对 `429` 做指数退避和频率提示。

### 服务端

- 同一错误语义只使用一个稳定 `code`，不要为同类错误新造近义词。
- 不要把数据库底层异常直接透传给客户端。
- 对运营和审核写接口，错误响应中仍应保留 `request_id` 方便审计。
- 参数校验错误（`INVALID_ARGUMENT`）应尽可能提供 `details` 数组。

### 文档维护

- 新接口上线时，同步在本文件和 OpenAPI 草案中补对应错误码。
- 新状态流引入时，先补错误码定义，再补接口实现。
- 预留错误码进入使用阶段后，将其从"预留"表移到对应域的"已落地"表。
- 若多个服务共用同一错误语义，优先复用已有错误码。

## 与其他文档的关系

- `docs/20-specs/backend-data-spec.md`
  - 定义通用错误返回结构和接口层的上游执行约束。
- `docs/30-api/openapi-v1-draft.yaml`
  - 错误码、错误 Schema 和响应类型的正式规范定义，本文档是其索引和说明。
- `docs/30-api/api-permissions.md`
  - 提供鉴权与权限错误码的业务语境和角色边界。
- `docs/30-api/api-overview.md`
  - 说明哪些接口需要使用本文件中的错误码约束。

# API 错误码

## 目的

本文档用于统一整理当前接口层的错误码、适用场景和建议 HTTP 状态码，作为后续补 OpenAPI、服务端异常映射和客户端错误处理策略的基础文档。

## 当前定位

- 本文档是错误码索引，不替代详细接口规范。
- 通用错误返回结构以 `docs/20-specs/backend-data-spec.md` 为准。
- 如果本文件与 `docs/20-specs/backend-data-spec.md` 冲突，以后者为准。

## 通用错误返回结构

所有接口错误响应统一使用：

```json
{
  "code": "INVALID_VOTE_STATE",
  "message": "当前投票周期不可投票",
  "request_id": "req_001"
}
```

建议：

- `code` 使用稳定的大写下划线命名
- `message` 面向调用方，可直接展示或记录
- `request_id` 用于日志、链路追踪和问题排查

## 通用错误码

| 错误码 | 建议 HTTP 状态码 | 说明 | 常见场景 |
|---|---|---|---|
| `UNAUTHORIZED` | `401` | 未认证或 Token 无效 | 未登录、Token 过期、签名错误 |
| `FORBIDDEN` | `403` | 已认证但无权限 | 玩家调用运营接口、审核员缺少发布权限 |
| `INVALID_ARGUMENT` | `400` | 请求参数非法 | 缺字段、字段格式错误、枚举值非法 |
| `RESOURCE_NOT_FOUND` | `404` | 目标资源不存在 | 区域、内容包、对象 ID 不存在 |
| `CONFLICT` | `409` | 资源状态冲突 | 重复投票、重复发布、重复回滚 |
| `RATE_LIMITED` | `429` | 触发限流或频率限制 | 高频投票、短时间重复请求 |
| `INTERNAL_ERROR` | `500` | 服务内部异常 | 未知错误、未捕获异常 |
| `SERVICE_UNAVAILABLE` | `503` | 服务暂不可用 | 依赖不可达、维护窗口、降级中 |

## 鉴权与权限错误

| 错误码 | 建议 HTTP 状态码 | 说明 | 适用接口 |
|---|---|---|---|
| `TOKEN_EXPIRED` | `401` | 访问令牌已过期 | 所有受保护接口 |
| `INVALID_TOKEN` | `401` | Token 格式或签名非法 | 所有受保护接口 |
| `INSUFFICIENT_SCOPE` | `403` | 角色或作用域不足 | `ops`、`reviewer` 相关接口 |
| `REVIEW_APPROVAL_FORBIDDEN` | `403` | 无审核批准权限 | `POST /api/v1/ops/review/{object_id}/approve` |
| `CONTENT_RELEASE_FORBIDDEN` | `403` | 无内容发布权限 | `POST /api/v1/ops/content-packages/{id}/release` |
| `CONTENT_ROLLBACK_FORBIDDEN` | `403` | 无内容回滚权限 | `POST /api/v1/ops/content-packages/{id}/rollback` |

## 世界与任务接口错误

| 错误码 | 建议 HTTP 状态码 | 说明 | 适用接口 |
|---|---|---|---|
| `REGION_NOT_FOUND` | `404` | 区域不存在 | `GET /api/v1/world/regions/{region_id}` |
| `REGION_NOT_VISIBLE` | `403` | 区域当前对玩家不可见 | `GET /api/v1/world/regions/{region_id}` |
| `QUEST_LIST_UNAVAILABLE` | `503` | 任务列表暂不可用 | `GET /api/v1/quests` |

## 投票接口错误

| 错误码 | 建议 HTTP 状态码 | 说明 | 适用接口 |
|---|---|---|---|
| `INVALID_VOTE_STATE` | `409` | 当前投票周期不可投票 | `GET /api/v1/votes/current` `POST /api/v1/votes/submit` |
| `VOTE_CYCLE_NOT_FOUND` | `404` | 投票周期不存在 | `GET /api/v1/votes/current` `POST /api/v1/votes/submit` |
| `VOTE_CYCLE_CLOSED` | `409` | 投票周期已关闭 | `POST /api/v1/votes/submit` |
| `PLAYER_NOT_ELIGIBLE` | `403` | 玩家不满足投票资格 | `POST /api/v1/votes/submit` |
| `CANDIDATE_NOT_FOUND` | `404` | 候选项不存在 | `POST /api/v1/votes/submit` |
| `CANDIDATE_OUT_OF_SCOPE` | `409` | 候选项不属于当前投票周期 | `POST /api/v1/votes/submit` |
| `DUPLICATE_VOTE` | `409` | 同一玩家在同一周期重复投票 | `POST /api/v1/votes/submit` |
| `VOTE_RISK_BLOCKED` | `403` | 命中设备或行为风控 | `POST /api/v1/votes/submit` |

## 内容查询接口错误

| 错误码 | 建议 HTTP 状态码 | 说明 | 适用接口 |
|---|---|---|---|
| `CONTENT_PACKAGE_NOT_FOUND` | `404` | 内容包不存在 | `GET /api/v1/content/packages/{content_package_id}` |
| `CONTENT_PACKAGE_NOT_VISIBLE` | `403` | 内容包对当前玩家不可见 | `GET /api/v1/content/packages/{content_package_id}` |
| `CONTENT_UPDATES_UNAVAILABLE` | `503` | 内容更新列表暂不可用 | `GET /api/v1/content/updates` |

## 运营与审核接口错误

| 错误码 | 建议 HTTP 状态码 | 说明 | 适用接口 |
|---|---|---|---|
| `INVALID_REVIEW_STATE` | `409` | 当前对象不处于可批准状态 | `POST /api/v1/ops/review/{object_id}/approve` |
| `REVIEW_OBJECT_NOT_FOUND` | `404` | 审核对象不存在 | `POST /api/v1/ops/review/{object_id}/approve` |
| `REASON_REQUIRED` | `400` | 敏感操作缺少原因字段 | 所有运营写接口 |
| `VOTE_CYCLE_CONFLICT` | `409` | 投票周期创建冲突 | `POST /api/v1/ops/vote-cycles` |
| `CONTENT_PACKAGE_NOT_RELEASABLE` | `409` | 内容包不满足发布前置条件 | `POST /api/v1/ops/content-packages/{id}/release` |
| `CONTENT_PACKAGE_ALREADY_LIVE` | `409` | 内容包已处于正式生效状态 | `POST /api/v1/ops/content-packages/{id}/release` |
| `CONTENT_PACKAGE_NOT_ROLLBACKABLE` | `409` | 内容包当前不可回滚 | `POST /api/v1/ops/content-packages/{id}/rollback` |
| `ROLLBACK_TARGET_INVALID` | `400` | 回滚目标版本非法 | `POST /api/v1/ops/content-packages/{id}/rollback` |

## 生命周期与状态流错误

这些错误码用于约束内容对象和内容包的状态迁移：

| 错误码 | 建议 HTTP 状态码 | 说明 |
|---|---|---|
| `INVALID_OBJECT_STATE` | `409` | 内容对象当前状态不支持本次操作 |
| `OBJECT_NOT_REVIEWED` | `409` | 对象尚未完成审核 |
| `OBJECT_NOT_PACKAGED` | `409` | 对象尚未进入内容包 |
| `PACKAGE_NOT_GRAY_READY` | `409` | 内容包未满足灰度前置条件 |
| `PACKAGE_NOT_LIVE_READY` | `409` | 内容包未满足正式上线前置条件 |
| `PACKAGE_SERIALIZATION_REQUIRED` | `409` | 当前已有发布或回滚流程在执行 |

## 审计与系统错误

| 错误码 | 建议 HTTP 状态码 | 说明 |
|---|---|---|
| `AUDIT_WRITE_FAILED` | `500` | 审计记录写入失败 |
| `TRACE_ID_MISSING` | `500` | 系统未正确生成链路追踪字段 |
| `TASK_DISPATCH_FAILED` | `503` | 异步任务分发失败 |
| `DEPENDENCY_UNAVAILABLE` | `503` | 下游依赖或队列不可用 |

## 使用建议

### 客户端

- 对 `401` 和 `403` 做明确鉴权提示。
- 对 `409` 做状态冲突处理，不要直接重试所有请求。
- 对 `429` 做退避和频率提示。

### 服务端

- 保持同一错误语义只使用一个稳定 `code`。
- 不要把数据库底层异常直接透传给客户端。
- 对运营和审核写接口，错误响应中仍应保留 `request_id` 方便审计。

### 文档维护

- 新接口上线时，应同步补对应错误码。
- 新状态流引入时，应先补状态冲突错误，再补接口实现。
- 若多个服务共用同一错误语义，应优先复用已有错误码而不是新造近义词。

## 待补充项

- 接口级错误码到 OpenAPI 的映射
- 客户端是否展示原始 `message` 的规则
- 多语言错误文案策略
- 内部任务错误与对外接口错误的映射关系

## 建议下一步

1. 为投票接口补完整请求响应样例。
2. 为运营接口补请求头、审计字段和幂等策略说明。
3. 再把 `api-overview.md`、`api-permissions.md` 和本文件收敛为统一的 OpenAPI 草案。

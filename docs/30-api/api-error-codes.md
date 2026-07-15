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
| `TOKEN_EXPIRED` | `401` | Access Token 已过期（与 INVALID_TOKEN 区分，提示刷新） | `TokenExpiredErrorResponse` |
| `INSUFFICIENT_SCOPE` | `403` | 访问令牌缺少所需作用域 | `ScopeErrorResponse` |
| `RESOURCE_NOT_FOUND` | `404` | 目标资源不存在 | `NotFoundErrorResponse` |
| `CONFLICT` | `409` | 资源状态冲突（通用） | `ConflictErrorResponse` |
| `RATE_LIMITED` | `429` | 触发限流或频率限制 | `RateLimitedErrorResponse` |
| `INTERNAL_ERROR` | `500` | 服务内部未知异常 | `InternalErrorResponse` |
| `AUDIT_WRITE_FAILED` | `500` | 审计记录写入失败 | `InternalErrorResponse` |
| `TRACE_ID_MISSING` | `500` | 系统未正确生成链路追踪字段 | `InternalErrorResponse` |
| `SERVICE_UNAVAILABLE` | `503` | 服务暂不可用 | `ServiceUnavailableErrorResponse` |
| `TASK_DISPATCH_FAILED` | `503` | 异步任务分发失败 | `ServiceUnavailableErrorResponse` |
| `DEPENDENCY_UNAVAILABLE` | `503` | 下游依赖或队列不可用 | `ServiceUnavailableErrorResponse` |

## 预留错误码（未在当前 OpenAPI 中使用）

当前无预留错误码。

## 投票接口错误码（24 个）

| 错误码 | HTTP 状态码 | 说明 | 适用接口 |
|---|---|---|---|
| `VOTE_CYCLE_NOT_FOUND` | `404` | 投票周期不存在 | 运营接口 |
| `NO_OPEN_VOTE_CYCLE` | `404` | 当前没有开放的投票周期 | `GET /votes/current` |
| `INVALID_VOTE_STATE` | `409` | 投票周期状态不允许当前操作 | `GET /votes/current` `POST /votes/submit` 运营接口 |
| `CANDIDATE_NOT_FOUND` | `404` | 候选项不存在或不属于当前投票周期 | `POST /votes/submit` |
| `CANDIDATE_NOT_ACTIVE` | `409` | 候选项当前不可投票（已撤回/已当选） | `POST /votes/submit` |
| `ALREADY_VOTED` | `409` | 玩家在本周期已投票 | `POST /votes/submit` |
| `DUPLICATE_VOTE` | `409` | 重复投票（幂等键冲突） | `POST /votes/submit` |
| `INVALID_PLAYER_ID` | `400` | 无效的玩家 ID 格式（非UUID） | `POST /votes/submit` `GET /votes/history` |
| `INVALID_ARGUMENT` | `400` | 请求参数非法 | 通用 |
| `VOTE_CYCLE_CONFLICT` | `409` | 同一章节已存在开放中的投票周期 | `POST /ops/vote-cycles` |
| `INSUFFICIENT_CONTRIBUTION` | `403` | 玩家贡献度不足，不具备投票资格 | `POST /votes/submit` |
| `DISCUSSION_NOT_FOUND` | `404` | 讨论不存在 | 讨论区接口 |
| `REPLY_NOT_FOUND` | `404` | 回复不存在 | 讨论区接口 |
| `DISCUSSION_CONTENT_TOO_LONG` | `400` | 讨论内容超过长度限制 | 创建讨论/回复 |
| `DISCUSSION_CONTENT_EMPTY` | `400` | 讨论内容为空 | 创建讨论/回复 |
| `INVALID_VOTE_CYCLE_FOR_DISCUSSION` | `400` | 投票周期不允许讨论操作 | 讨论区接口 |
| `ANOMALY_NOT_FOUND` | `404` | 异常记录不存在 | 异常管理接口 |
| `INVALID_ANOMALY_STATUS` | `409` | 异常记录状态不允许当前操作 | 异常管理接口 |
| `INTERNAL_ERROR` | `500` | 服务内部未知异常 | 通用 |
| `AUDIT_WRITE_FAILED` | `500` | 审计记录写入失败 | 通用 |
| `TRACE_ID_MISSING` | `500` | 系统未正确生成链路追踪字段 | 通用 |
| `TASK_DISPATCH_FAILED` | `503` | 异步任务分发失败 | 通用 |
| `DEPENDENCY_UNAVAILABLE` | `503` | 下游依赖不可用 | 通用 |
| `TOKEN_EXPIRED` | `401` | Access Token 已过期 | 通用 |

## 世界服务错误码（26 个）

| 错误码 | HTTP 状态码 | 说明 | 适用接口 |
|---|---|---|---|
| `REGION_NOT_FOUND` | `404` | 区域不存在 | 区域接口 |
| `INVALID_REGION_STATUS` | `409` | 区域状态不允许当前操作 | `POST /ops/world/regions/{id}/status` |
| `SKELETON_NOT_FOUND` | `404` | 世界骨架快照不存在 | 骨架接口 |
| `SKELETON_VERSION_EXISTS` | `409` | 骨架快照版本已存在 | `POST /ops/world/skeleton` |
| `NPC_NOT_FOUND` | `404` | NPC 不存在 | NPC 接口 |
| `QUEST_NOT_FOUND` | `404` | 任务不存在 | 任务接口 |
| `NPC_KEY_EXISTS` | `409` | NPC Key 已存在 | `POST /ops/world/npcs` |
| `QUEST_KEY_EXISTS` | `409` | 任务 Key 已存在 | `POST /ops/world/quests` |
| `INVALID_NPC_KEY` | `400` | 无效的 NPC Key 格式 | NPC 接口 |
| `INVALID_QUEST_KEY` | `400` | 无效的任务 Key 格式 | 任务接口 |
| `INVALID_QUEST_TYPE` | `400` | 无效的任务类型 | 任务接口 |
| `ITEM_NOT_FOUND` | `404` | 物品定义不存在 | 物品接口 |
| `ITEM_KEY_EXISTS` | `409` | 物品 Key 已存在 | `POST /ops/world/items` |
| `INVALID_ITEM_TYPE` | `400` | 无效的物品类型 | 物品接口 |
| `INVALID_ITEM_SLOT` | `400` | 无效的装备槽位 | 物品接口 |
| `INVALID_ITEM_RARITY` | `400` | 无效的稀有度 | 物品接口 |
| `MONSTER_NOT_FOUND` | `404` | 怪物定义不存在 | 怪物接口 |
| `MONSTER_KEY_EXISTS` | `409` | 怪物 Key 已存在 | `POST /ops/world/monsters` |
| `INVALID_MONSTER_TYPE` | `400` | 无效的怪物类型 | 怪物接口 |
| `INVALID_ARGUMENT` | `400` | 请求参数非法 | 通用 |
| `INTERNAL_ERROR` | `500` | 服务内部未知异常 | 通用 |
| `AUDIT_WRITE_FAILED` | `500` | 审计记录写入失败 | 通用 |
| `TRACE_ID_MISSING` | `500` | 系统未正确生成链路追踪字段 | 通用 |
| `TASK_DISPATCH_FAILED` | `503` | 异步任务分发失败 | 通用 |
| `DEPENDENCY_UNAVAILABLE` | `503` | 下游依赖不可用 | 通用 |
| `TOKEN_EXPIRED` | `401` | Access Token 已过期 | 通用 |

## 内容服务错误码（12 个）

| 错误码 | HTTP 状态码 | 说明 | 适用接口 |
|---|---|---|---|
| `PACKAGE_NOT_FOUND` | `404` | 内容包不存在 | 内容包查询接口 |
| `CONTENT_PACKAGE_NOT_FOUND` | `404` | 内容包不存在（运营） | 运营内容包接口 |
| `INVALID_PACKAGE_STATE` | `409` | 内容包状态不允许当前操作 | 发布/回滚接口 |
| `CONTENT_PACKAGE_NOT_RELEASABLE` | `409` | 内容包不可发布 | 发布接口 |
| `CONTENT_PACKAGE_NOT_ROLLBACKABLE` | `409` | 内容包不可回滚 | 回滚接口 |
| `INVALID_ARGUMENT` | `400` | 请求参数非法 | 通用 |
| `INTERNAL_ERROR` | `500` | 服务内部未知异常 | 通用 |
| `AUDIT_WRITE_FAILED` | `500` | 审计记录写入失败 | 通用 |
| `TRACE_ID_MISSING` | `500` | 系统未正确生成链路追踪字段 | 通用 |
| `TASK_DISPATCH_FAILED` | `503` | 异步任务分发失败 | 通用 |
| `DEPENDENCY_UNAVAILABLE` | `503` | 下游依赖不可用 | 通用 |
| `TOKEN_EXPIRED` | `401` | Access Token 已过期 | 通用 |

## 生成服务错误码（18 个）

| 错误码 | HTTP 状态码 | 说明 | 适用接口 |
|---|---|---|---|
| `REQUEST_NOT_FOUND` | `404` | 生成请求不存在 | 请求查询接口 |
| `GENERATION_REQUEST_NOT_FOUND` | `404` | 生成请求不存在（详细） | 运营接口 |
| `OBJECT_NOT_FOUND` | `404` | 生成对象不存在 | 对象查询接口 |
| `GENERATED_OBJECT_NOT_FOUND` | `404` | 生成对象不存在（详细） | 运营接口 |
| `INVALID_REQUEST_STATUS` | `409` | 生成请求状态不允许当前操作 | 状态更新接口 |
| `INVALID_OBJECT_STATUS` | `409` | 生成对象状态不允许当前操作 | 状态更新接口 |
| `MAX_RETRIES_EXCEEDED` | `409` | 已达到最大重试次数 | 状态更新接口 |
| `SKELETON_NOT_FOUND` | `404` | 世界骨架快照不存在 | 创建请求前校验 |
| `INVALID_CHAPTER_ID` | `400` | 无效的章节 ID | 创建请求 |
| `INVALID_REGION_ID` | `400` | 无效的区域 ID | 创建请求 |
| `FORBIDDEN_TAGS_EMPTY` | `400` | 禁止标签为空 | 创建请求前校验 |
| `INVALID_ARGUMENT` | `400` | 请求参数非法 | 通用 |
| `INTERNAL_ERROR` | `500` | 服务内部未知异常 | 通用 |
| `AUDIT_WRITE_FAILED` | `500` | 审计记录写入失败 | 通用 |
| `TRACE_ID_MISSING` | `500` | 系统未正确生成链路追踪字段 | 通用 |
| `TASK_DISPATCH_FAILED` | `503` | 异步任务分发失败 | 通用 |
| `DEPENDENCY_UNAVAILABLE` | `503` | 下游依赖不可用 | 通用 |
| `TOKEN_EXPIRED` | `401` | Access Token 已过期 | 通用 |

## 审核服务错误码（12 个）

| 错误码 | HTTP 状态码 | 说明 | 适用接口 |
|---|---|---|---|
| `REVIEW_NOT_FOUND` | `404` | 审核记录不存在 | 审核记录接口 |
| `REVIEW_RECORD_NOT_FOUND` | `404` | 审核记录不存在（详细） | 运营接口 |
| `INVALID_REVIEW_STATUS` | `409` | 审核记录状态不允许当前操作 | 审核结果更新接口 |
| `NO_REVIEWS_FOUND` | `404` | 该对象没有审核记录 | 批准/拒绝接口 |
| `REVIEW_OBJECT_NOT_FOUND` | `404` | 审核对象不存在 | 审核接口 |
| `INVALID_ARGUMENT` | `400` | 请求参数非法 | 通用 |
| `INTERNAL_ERROR` | `500` | 服务内部未知异常 | 通用 |
| `AUDIT_WRITE_FAILED` | `500` | 审计记录写入失败 | 通用 |
| `TRACE_ID_MISSING` | `500` | 系统未正确生成链路追踪字段 | 通用 |
| `TASK_DISPATCH_FAILED` | `503` | 异步任务分发失败 | 通用 |
| `DEPENDENCY_UNAVAILABLE` | `503` | 下游依赖不可用 | 通用 |
| `TOKEN_EXPIRED` | `401` | Access Token 已过期 | 通用 |

## 玩家服务错误码（56 个）

| 错误码 | HTTP 状态码 | 说明 | 适用接口 |
|---|---|---|---|
| `PLAYER_NOT_FOUND` | `404` | 玩家不存在 | 玩家查询接口 |
| `INVALID_PLAYER_ID` | `400` | 无效的玩家 ID 格式（非UUID） | 玩家接口 |
| `INVALID_QUEST_STATUS` | `400` | 无效的任务状态 | 任务接口 |
| `REGION_NOT_FOUND` | `404` | 区域不存在 | 区域接口 |
| `QUEST_NOT_FOUND` | `404` | 任务不存在 | 任务接口 |
| `QUEST_ALREADY_ACCEPTED` | `409` | 任务已被接取 | 接取任务 |
| `QUEST_NOT_ACTIVE` | `409` | 任务不在活跃状态 | 任务操作 |
| `QUEST_INVALID_STATE_TRANSITION` | `409` | 任务状态迁移非法 | 任务状态更新 |
| `QUEST_ALREADY_COMPLETED` | `409` | 任务已完成 | 任务操作 |
| `QUEST_OBJECTIVES_INCOMPLETE` | `409` | 任务目标未完成 | 完成任务 |
| `QUEST_REWARD_GRANT_FAILED` | `500` | 任务奖励发放失败 | 完成任务 |
| `ITEM_NOT_FOUND` | `404` | 物品不存在 | 背包接口 |
| `INSUFFICIENT_QUANTITY` | `409` | 物品数量不足 | 使用/移除物品 |
| `INVALID_ITEM_TYPE` | `400` | 无效的物品类型 | 背包接口 |
| `REPUTATION_REGION_NOT_FOUND` | `404` | 声望区域不存在 | 声望接口 |
| `INVALID_REPUTATION_AMOUNT` | `400` | 无效的声望调整量 | 调整声望 |
| `REPUTATION_LOCKED` | `403` | 区域被声望锁定 | 区域解锁 |
| `CONTRIBUTION_PLAYER_NOT_FOUND` | `404` | 贡献度玩家不存在 | 贡献度接口 |
| `INVALID_CONTRIBUTION_AMOUNT` | `400` | 无效的贡献度量 | 增加贡献度 |
| `ACHIEVEMENT_NOT_FOUND` | `404` | 成就不存在 | 成就接口 |
| `ACHIEVEMENT_ALREADY_UNLOCKED` | `409` | 成就已解锁 | 解锁成就 |
| `ACHIEVEMENT_KEY_EXISTS` | `409` | 成就 Key 已存在 | 创建成就 |
| `ACHIEVEMENT_REWARD_ALREADY_CLAIMED` | `409` | 成就奖励已领取 | 领取奖励 |
| `ACHIEVEMENT_NOT_ACTIVE` | `409` | 成就不在活跃状态 | 成就操作 |
| `INVALID_ACHIEVEMENT_RARITY` | `400` | 无效的成就稀有度 | 创建成就 |
| `INVALID_ACHIEVEMENT_CATEGORY` | `400` | 无效的成就分类 | 创建成就 |
| `INVALID_EXPERIENCE_AMOUNT` | `400` | 无效的经验值量 | 增加经验 |
| `MAX_LEVEL_REACHED` | `409` | 已达到最大等级 | 增加经验 |
| `FRIEND_REQUEST_ALREADY_SENT` | `409` | 好友请求已发送 | 发送好友请求 |
| `FRIEND_REQUEST_NOT_FOUND` | `404` | 好友请求不存在 | 接受/拒绝好友请求 |
| `FRIEND_REQUEST_NOT_PENDING` | `409` | 好友请求不在待处理状态 | 接受/拒绝好友请求 |
| `ALREADY_FRIENDS` | `409` | 已经是好友 | 发送好友请求 |
| `CANNOT_FRIEND_SELF` | `400` | 不能添加自己为好友 | 发送好友请求 |
| `FRIEND_NOT_FOUND` | `404` | 好友不存在 | 好友接口 |
| `FRIEND_BLOCKED` | `403` | 已被对方拉黑 | 好友请求 |
| `NOT_FRIENDS` | `403` | 非好友关系 | 私信接口 |
| `MESSAGE_TOO_LONG` | `400` | 消息内容超过长度限制 | 发送消息 |
| `MESSAGE_EMPTY` | `400` | 消息内容为空 | 发送消息 |
| `MESSAGE_NOT_FOUND` | `404` | 消息不存在 | 消息接口 |
| `CANNOT_DELETE_OTHER_MESSAGE` | `403` | 不能删除他人消息 | 删除消息 |
| `GUILD_NAME_EXISTS` | `409` | 公会名称已存在 | 创建公会 |
| `GUILD_NOT_FOUND` | `404` | 公会不存在 | 公会接口 |
| `ALREADY_IN_GUILD` | `409` | 已加入公会 | 加入公会 |
| `NOT_IN_GUILD` | `403` | 未加入公会 | 公会操作 |
| `NOT_GUILD_LEADER` | `403` | 不是公会会长 | 会长操作 |
| `NOT_GUILD_OFFICER` | `403` | 不是公会官员 | 官员操作 |
| `CANNOT_REMOVE_LEADER` | `403` | 不能移除会长 | 移除成员 |
| `GUILD_FULL` | `409` | 公会已满 | 邀请成员 |
| `CANNOT_LEAVE_AS_LEADER` | `409` | 会长不能直接离开 | 离开公会 |
| `INVALID_EQUIPMENT_SLOT` | `400` | 无效的装备槽位 | 装备接口 |
| `EQUIPMENT_SLOT_OCCUPIED` | `409` | 装备槽位已被占用 | 装备物品 |
| `ITEM_NOT_EQUIPPABLE` | `400` | 物品不可装备 | 装备物品 |
| `CANNOT_UNEQUIP_EMPTY_SLOT` | `409` | 不能卸下空槽位 | 卸下装备 |
| `LEVEL_REQUIREMENT_NOT_MET` | `403` | 等级不满足装备要求 | 装备物品 |
| `EQUIPMENT_NOT_FOUND` | `404` | 装备不存在 | 装备接口 |
| `INVALID_ARGUMENT` | `400` | 请求参数非法 | 通用 |
| `INTERNAL_ERROR` | `500` | 服务内部未知异常 | 通用 |

## 运营服务错误码（21 个）

| 错误码 | HTTP 状态码 | 说明 | 适用接口 |
|---|---|---|---|
| `ACTION_NOT_FOUND` | `404` | 运营操作记录不存在 | `GET /ops/actions/{id}` |
| `DASHBOARD_NOT_FOUND` | `404` | 仪表盘不存在 | 仪表盘接口 |
| `INSIGHT_NOT_FOUND` | `404` | 洞察不存在 | 洞察接口 |
| `REQUIREMENT_NOT_FOUND` | `404` | 需求不存在 | 需求接口 |
| `EVENT_NOT_FOUND` | `404` | 运营事件不存在 | 事件接口 |
| `EVENT_NAME_EXISTS` | `409` | 运营事件名称已存在 | 创建事件 |
| `INVALID_EVENT_STATUS` | `409` | 事件状态不允许当前操作 | 事件状态变更 |
| `EVENT_TIME_OVERLAP` | `409` | 事件时间范围重叠 | 创建/更新事件 |
| `INVALID_EVENT_CONFIG` | `400` | 无效的事件配置 | 创建/更新事件 |
| `UPSTREAM_SERVICE_ERROR` | `502` | 上游服务错误 | 代理接口 |
| `VOTE_CYCLE_CREATE_FAILED` | `502` | 投票周期创建失败 | 投票代理接口 |
| `CONTENT_RELEASE_FAILED` | `502` | 内容发布失败 | 内容代理接口 |
| `CONTENT_ROLLBACK_FAILED` | `502` | 内容回滚失败 | 内容代理接口 |
| `REVIEW_APPROVE_FAILED` | `502` | 审核批准失败 | 审核代理接口 |
| `REVIEW_REJECT_FAILED` | `502` | 审核拒绝失败 | 审核代理接口 |
| `INVALID_ARGUMENT` | `400` | 请求参数非法 | 通用 |
| `INTERNAL_ERROR` | `500` | 服务内部未知异常 | 通用 |
| `AUDIT_WRITE_FAILED` | `500` | 审计记录写入失败 | 通用 |
| `TRACE_ID_MISSING` | `500` | 系统未正确生成链路追踪字段 | 通用 |
| `TASK_DISPATCH_FAILED` | `503` | 异步任务分发失败 | 通用 |
| `DEPENDENCY_UNAVAILABLE` | `503` | 下游依赖不可用 | 通用 |

## 网关服务错误码（13 个）

| 错误码 | HTTP 状态码 | 说明 | 适用场景 |
|---|---|---|---|
| `NOT_FOUND` | `404` | 未找到对应的服务 | 路由不匹配 |
| `INVALID_TOKEN` | `401` | Token 格式或签名非法 | 鉴权失败 |
| `TOKEN_EXPIRED` | `401` | Access Token 已过期 | Token 过期 |
| `INSUFFICIENT_SCOPE` | `403` | 访问令牌缺少所需作用域 | 权限不足 |
| `RATE_LIMITED` | `429` | 触发限流 | 频率超限 |
| `SERVICE_UNAVAILABLE` | `503` | 服务暂不可用 | 下游不可达 |
| `GATEWAY_TIMEOUT` | `504` | 网关超时 | 下游超时 |
| `INTERNAL_ERROR` | `500` | 服务内部未知异常 | 通用 |
| `INVALID_ARGUMENT` | `400` | 请求参数非法 | 通用 |
| `AUDIT_WRITE_FAILED` | `500` | 审计记录写入失败 | 通用 |
| `TRACE_ID_MISSING` | `500` | 系统未正确生成链路追踪字段 | 通用 |
| `TASK_DISPATCH_FAILED` | `503` | 异步任务分发失败 | 通用 |
| `DEPENDENCY_UNAVAILABLE` | `503` | 下游依赖不可用 | 通用 |

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

# API 总览

## 目的

本文档用于把 `docs/specs/backend-data-spec.md` 中分散的接口方向整理成一份实施索引，方便后续补 OpenAPI、请求响应样例、错误码表和服务拆分文档。

## 当前定位

- 本文档是接口总览，不替代详细规范。
- 服务边界、数据模型、异步任务、事件流和安全要求以 `docs/specs/backend-data-spec.md` 为准。
- 如果本文件与 `docs/specs/backend-data-spec.md` 冲突，以后者为准。

## 通用约定

- 协议：`HTTPS + JSON`
- 认证：`Bearer Token`
- 版本前缀：`/api/v1`
- 时间格式：ISO 8601
- 错误返回统一使用：

```json
{
  "code": "INVALID_VOTE_STATE",
  "message": "当前投票周期不可投票",
  "request_id": "req_001"
}
```

## 角色与权限

### `player`

- 面向普通玩家
- 可访问世界、任务、投票和内容更新查询接口

### `ops`

- 面向运营和配置角色
- 可创建投票周期、发布内容包、触发回滚

### `reviewer`

- 面向审核角色
- 可批准或处理审核流中的内容对象

### `system`

- 面向 Agent、任务队列和自动化流程
- 主要处理内部任务、事件和审计链路

## 服务边界速览

| 服务 | 主要职责 | 是否直接对客户端开放 |
|---|---|---|
| `gateway-service` | 统一入口、鉴权、限流、会话上下文 | 是 |
| `player-service` | 账号、角色、成长、声望、章节进度 | 是 |
| `world-service` | 区域状态、阵营状态、地图与任务可见性 | 是 |
| `vote-service` | 候选池、投票资格、投票记录、结算 | 是 |
| `generation-service` | 生成请求组织、模板加载、生成结果落库 | 否 |
| `review-service` | 结构化校验、风险判断、人工复核流转 | 否 |
| `content-service` | 内容包、灰度投放、版本归档、回滚 | 部分 |
| `ops-service` | 运营后台入口、指标汇总、Issue 触发 | 否 |

## 当前接口清单

### 世界与任务

| 方法 | 路径 | 角色 | 作用 | 建议归属服务 |
|---|---|---|---|---|
| `GET` | `/api/v1/world/regions` | `player` | 获取当前可见区域列表 | `world-service` |
| `GET` | `/api/v1/world/regions/{region_id}` | `player` | 获取区域详情和状态 | `world-service` |
| `GET` | `/api/v1/quests` | `player` | 获取玩家任务列表 | `player-service` 或 `world-service` |

### 投票

| 方法 | 路径 | 角色 | 作用 | 建议归属服务 |
|---|---|---|---|---|
| `GET` | `/api/v1/votes/current` | `player` | 获取当前投票周期与候选项 | `vote-service` |
| `POST` | `/api/v1/votes/submit` | `player` | 提交投票 | `vote-service` |
| `GET` | `/api/v1/votes/history` | `player` | 获取历史投票结果与落地情况 | `vote-service` |

### 内容更新

| 方法 | 路径 | 角色 | 作用 | 建议归属服务 |
|---|---|---|---|---|
| `GET` | `/api/v1/content/updates` | `player` | 获取当前玩家可见的新内容包 | `content-service` |
| `GET` | `/api/v1/content/packages/{content_package_id}` | `player` | 获取内容包摘要 | `content-service` |

### 运营与审核

| 方法 | 路径 | 角色 | 作用 | 建议归属服务 |
|---|---|---|---|---|
| `POST` | `/api/v1/ops/vote-cycles` | `ops` | 创建投票周期 | `ops-service` |
| `POST` | `/api/v1/ops/review/{object_id}/approve` | `reviewer` 或 `ops` | 批准内容对象 | `review-service` |
| `POST` | `/api/v1/ops/content-packages/{id}/release` | `ops` | 发布内容包 | `content-service` |
| `POST` | `/api/v1/ops/content-packages/{id}/rollback` | `ops` | 回滚内容包 | `content-service` |

## 推荐补齐的请求与响应样例

### `GET /api/v1/votes/current`

- 建议补齐：
  - 当前投票周期元信息
  - 候选项数组
  - 玩家是否有资格投票
  - 投票截止时间

### `POST /api/v1/votes/submit`

- 建议请求体至少包含：

```json
{
  "vote_cycle_id": "cycle_202606",
  "candidate_id": "candidate_03"
}
```

- 建议响应体至少包含：

```json
{
  "vote_id": "vote_001",
  "vote_cycle_id": "cycle_202606",
  "accepted": true,
  "request_id": "req_vote_001"
}
```

### `GET /api/v1/content/updates`

- 建议补齐：
  - 玩家当前可见内容包列表
  - 每个内容包的区域范围
  - 发布时间
  - 是否灰度可见

### `POST /api/v1/ops/content-packages/{id}/release`

- 建议请求体至少包含：

```json
{
  "gray_scope": {
    "region_ids": ["region_wasteland_01"],
    "player_percent": 10
  },
  "reason": "首轮灰度发布"
}
```

## 关键状态关系

### 投票链路

`vote_cycle -> candidate -> vote -> finalized_result`

### 内容链路

`generation_request -> generated_object -> review_record -> content_package -> release_or_rollback`

### 生命周期对齐

- 内容对象状态参考 `docs/specs/content-generation-spec.md`：
  - `draft -> validated -> reviewed -> packaged -> gray -> live -> archived`
- 发布接口只能操作已满足发布前置条件的对象或内容包。

## 异步任务索引

以下能力不应通过同步接口直接执行：

- `generate_content_batch`
- `run_world_consistency_review`
- `run_balance_review`
- `package_content_batch`
- `release_content_package`
- `rollback_content_package`
- `daily_gate_scan`

建议：

- 同步接口只负责接收请求、校验权限、生成 `request_id` 或 `task_id`
- 实际长任务交给队列系统处理
- 所有状态变更写入审计链

## 事件主题索引

建议内部事件总线至少包含：

- `vote.cycle.closed`
- `vote.result.finalized`
- `generation.request.created`
- `generation.batch.completed`
- `review.batch.completed`
- `content.package.released`
- `content.package.rolled_back`

每条事件至少包含：

- `event_id`
- `event_type`
- `occurred_at`
- `trace_id`
- `producer`
- `payload`

## 需要后续补齐的内容

- OpenAPI 文档
- 每个接口的请求响应样例
- 错误码总表
- 权限矩阵
- 幂等策略说明
- 分页、排序和过滤约定
- 审计字段约定
- Webhook 或内部事件消费者清单

## 建议下一步

1. 先补玩家接口和投票接口的请求响应样例。
2. 再补运营接口的权限矩阵和错误码。
3. 最后再把本文件下沉为 OpenAPI 或按服务拆分为更细的接口文档。

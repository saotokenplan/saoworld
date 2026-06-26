# API 总览

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本文档用于把 `docs/20-specs/backend-data-spec.md` 中分散的接口方向整理成一份实施索引，作为 `docs/30-api/` 目录的导航入口。

## 适用范围

- 适用于 `docs/30-api/` 目录下的接口参考导航和总览说明。
- 适用于梳理当前 API 域、服务边界、接口清单和后续补充方向时的统一入口。
- 不替代 `docs/20-specs/` 中的执行规范，也不替代具体接口样例、权限矩阵和错误码细表。

## 当前定位

- 本文档是接口总览，不替代详细规范。
- 服务边界、数据模型、异步任务、事件流和安全要求以 `docs/20-specs/backend-data-spec.md` 为准。
- 如果本文件与 `docs/20-specs/backend-data-spec.md` 冲突，以后者为准。

## 通用约定

- 协议：`HTTPS + JSON`
- 认证：OIDC 签发的 JWT Bearer Token（`Authorization: Bearer <token>`）
- 版本前缀：`/api/v1`
- 时间格式：ISO 8601
- 错误返回统一结构（详见 [api-error-codes.md](file:///workspace/docs/30-api/api-error-codes.md) 和 OpenAPI Schema）：

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

## 请求与响应样例

详细的请求响应样例已在以下文档中定义，并已同步到 OpenAPI 草案的 `components/examples`：

- 投票链路：`docs/30-api/api-examples-vote.md`
- 内容查询/发布/回滚：`docs/30-api/api-examples-content.md`
- 世界/任务/运营审核：`docs/30-api/api-examples-world-ops.md`

## 关键状态关系

### 投票链路

`vote_cycle -> candidate -> vote -> finalized_result`

### 内容链路

`generation_request -> generated_object -> review_record -> content_package -> release_or_rollback`

### 生命周期对齐

- 内容对象状态参考 `docs/20-specs/content-generation-spec.md`：
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

## 文档资产清单

`docs/30-api/` 目录当前包含以下接口参考文档：

| 文档 | 说明 |
|---|---|
| `api-overview.md`（本文档） | 接口总览、服务边界、接口清单 |
| `api-permissions.md` | 角色矩阵、scope 映射、审计要求 |
| `api-error-codes.md` | 错误码索引（已落地 vs 预留）、错误结构说明 |
| `api-examples-vote.md` | 投票链路请求响应样例 |
| `api-examples-content.md` | 内容查询、发布与回滚链路样例 |
| `api-examples-world-ops.md` | 世界、任务查询及运营写接口样例 |
| `openapi-draft.md` | OpenAPI 草案入口、分批次阅读片段 |
| `openapi-v1-draft.yaml` | **权威**单文件 OpenAPI 3.1 草案（12 个接口） |

## 需要后续补齐的内容

- 第二批/第三批接口的字段级校验错误 details 样例
- 成功响应包装的复用层抽象
- 更完整的幂等策略说明（当前 `Idempotency-Key` 头已定义，但冲突响应行为待细化）
- 服务端实现阶段：将预留错误码（如 `INTERNAL_ERROR`、`TOKEN_EXPIRED`）落地
- 仓库策略确认后，决定是否按服务拆分子草案

## 建议下一步

1. 选定首个最小落地目标（建议投票链路），进入服务端工程初始化。
2. 实现过程中根据代码实际约束迭代 OpenAPI 草案。
3. 仓库策略明确后，决定单文件拆分方案。

## 与其他文档的关系

- `docs/20-specs/backend-data-spec.md`
  - 定义服务边界、数据模型和接口约束，是本文件的上游执行规范。
- `docs/30-api/api-permissions.md`
  - 补充接口角色边界、敏感操作约束和审计要求。
- `docs/30-api/api-error-codes.md`
  - 补充接口错误码、HTTP 状态码和异常语义。
- `docs/30-api/api-examples-vote.md`
  - 提供投票链路的请求响应样例，作为本总览中具体接口的下游细化文档。
- `docs/30-api/api-examples-content.md`
  - 提供内容查询、发布与回滚链路的请求响应样例，作为第二批接口的下游细化文档。
- `docs/30-api/api-examples-world-ops.md`
  - 提供世界查询、任务查询和第三批运营写接口的请求响应样例，作为第三批接口的下游细化文档。
- `docs/30-api/openapi-draft.md`
  - 作为本文件、权限矩阵、错误码和接口样例的后续汇总入口，并维护单文件草案的组织说明。
- `docs/30-api/openapi-v1-draft.yaml`
  - 当前首版单文件 OpenAPI 草案输出，供接口评审、实现对齐和后续工具链接入使用。

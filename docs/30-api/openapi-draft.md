# OpenAPI 草案入口

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本文档用于作为 `docs/30-api/` 目录下的 OpenAPI 草案入口，统一说明当前 OpenAPI 草案的覆盖范围、组织方式、来源文档和后续补齐顺序，避免接口信息继续分散在总览、权限矩阵、错误码和样例文档中。

## 适用范围

- 适用于准备把接口总览、权限矩阵、错误码和请求响应样例继续收敛为 OpenAPI 草案的场景。
- 适用于服务端实现、客户端接入、接口评审和后续自动生成 Swagger 文档前的草案整理。
- 不替代 `docs/20-specs/backend-data-spec.md` 中的上游执行规范，也不替代 `docs/30-api/` 下现有专题文档。

## 当前定位

- 本文档是 OpenAPI 草案的入口说明与维护索引，单文件草案见 `docs/30-api/openapi-v1-draft.yaml`。
- 当前接口边界、服务职责和数据约束仍以 `docs/20-specs/backend-data-spec.md` 为准。
- 本文档回答“OpenAPI 草案怎么组织、现阶段已完成到哪里、下一步还缺什么”。

## 当前状态

- 当前已形成首版单文件 OpenAPI 草案：`docs/30-api/openapi-v1-draft.yaml`。
- 当前已经具备的上游输入包括：
  - `docs/30-api/api-overview.md`
  - `docs/30-api/api-permissions.md`
  - `docs/30-api/api-error-codes.md`
  - `docs/30-api/api-examples-vote.md`
- 当前已经完成的草案收敛包括：
  - 第一批（投票链路）、第二批（内容查询与发布回滚）、第三批（世界/任务/运营）共 **12 个接口**的 `paths` 与 schema 草案全部完成
  - 错误层已原子化并特化：原子字段（`GenericErrorCode`、`TraceId`、`RequestId`、`ValidationIssue`、`AuthorizationIssue`、`RejectedValue`、`PathFieldName`/`QueryFieldName`/`BodyFieldPath`/`HeaderFieldName`），特化错误响应（`ValidationErrorResponse`、`NotFoundErrorResponse`、`ScopeErrorResponse`、`PathParameterErrorResponse`、`ReasonRequiredErrorResponse`、`DomainServiceUnavailableErrorResponse`、`OpsWriteValidationErrorResponse`、`RateLimitedErrorResponse`、`UnauthorizedErrorResponse`），复用参数（分页、ID 参数）、复用请求头（`Idempotency-Key`、`X-Trace-Id`、`X-Request-Id`）
  - `components/responses` 已升级为特化类型：`BadRequest`→`ValidationErrorResponse`、`Unauthorized`→`UnauthorizedErrorResponse`、`NotFound`→`NotFoundErrorResponse`、`Forbidden`→`ScopeErrorResponse`、`TooManyRequests`→`RateLimitedErrorResponse`，新增 `InvalidPagination`、`InsufficientScope`、`PathParameterInvalid`、`ReasonRequired` 高频复用响应
  - 成功响应 envelope 已抽象：`RequestScopedResponse`（含 `request_id`）、`TraceableResponse`（含 `trace_id`）、`ListResponseBase`（列表+分页 meta）、`DetailResponseBase`（单对象+meta）、`OperationResponseBase`（写操作+trace）
  - 安全方案已定义：OIDC JWT Bearer Token + 细粒度 scope（10 个 scope），每个接口均声明 `x-roles` 角色集合和所需 scope
  - 请求响应样例已覆盖投票主链路、内容、世界、任务、运营写接口的典型成功样例和主要错误样例
  - 路径端点响应已升级：ops 写接口 400→`OpsWriteValidationErrorResponse`（oneOf: 参数校验+reason缺失），503→`DomainServiceUnavailableErrorResponse`；所有跨端点高频错误均已使用特化 schema
- 当前仍缺少或待细化的内容（按优先级）：
  1. 部分端点边界条件的字段级错误 details 样例（如 `POST /ops/content-packages/{id}/rollback` 的 400 `ROLLBACK_TARGET_INVALID` 是领域语义错误，无 details；其余端点的参数校验样例已覆盖）
  2. 预留错误码落地（如 `INTERNAL_ERROR`、`TOKEN_EXPIRED`），应在服务端实现阶段按需添加
  3. 按服务拆分子草案的评估（当前单文件 2600+ 行、12 个端点，规模尚可控；建议端点超过 25-30 个时再拆分）

## 草案收敛原则

- 先收敛接口入口、角色、错误码和样例，再生成单文件 OpenAPI 结构。
- 若 `docs/30-api/` 与 `docs/20-specs/backend-data-spec.md` 冲突，以后者为准。
- OpenAPI 草案应优先覆盖最小实施路径相关接口，不要求一开始追求全量覆盖。
- 已在其他 API 文档中稳定下来的权限、错误码和样例，应优先下沉到 `docs/30-api/openapi-v1-draft.yaml` 而不是重复维护平行描述。
- 每次新增接口样例、权限约束或错误码后，应判断是否需要同步更新本文档与 `docs/30-api/openapi-v1-draft.yaml`。

## 建议的草案结构

### 顶层信息

- `openapi`
- `info`
- `servers`
- `tags`
- `paths`
- `components`

### `tags` 建议

- `world`
- `quests`
- `votes`
- `content`
- `ops`
- `review`

### `components` 建议

- `securitySchemes`
  - 基于 Bearer Token
- `schemas`
  - 玩家、投票周期、候选项、内容包、审核对象等通用结构
- `responses`
  - 通用错误响应与典型成功响应
- `parameters`
  - 分页、章节、区域、内容包 ID 等复用参数
- `headers`
  - `Idempotency-Key`
  - `X-Request-Id`

## 首批建议实现的接口组

首批建议从投票链路开始实现（MVP 核心闭环）：

- `GET /api/v1/votes/current`
- `POST /api/v1/votes/submit`
- `GET /api/v1/votes/history`

原因：

- 已有较完整样例文档，OpenAPI 定义最成熟。
- 属于首个最小落地目标中最容易收敛的一条主线能力。
- 涉及角色、scope、错误码、幂等和审计要求，可作为服务端实现模板。

## 草案正文

> **注意**：以下分批次的 YAML 片段是草案收敛过程中按批次形成的历史快照，便于按接口组阅读结构。**权威的完整定义以 `docs/30-api/openapi-v1-draft.yaml` 单文件为准**，其中包含最新的错误 Schema 特化、scope 声明、`x-roles` 角色标注和完整 examples。片段中的错误码建议列表已同步为 YAML 中实际使用的 code，但片段中的 Schema 省略了部分特化类型引用（如 `ValidationErrorResponse` 等），以保持片段简洁可读。

### 顶层片段

```yaml
openapi: 3.1.0
info:
  title: AI Game MVP API Draft
  version: 0.1.0-draft
  description: >
    第一批先覆盖投票链路，作为后续扩展世界、内容和运营接口的草案基线。
servers:
  - url: https://api.example.com
    description: production placeholder
security:
  - bearerAuth: []
tags:
  - name: votes
    description: 玩家投票周期、投票提交与历史结果查询
```

### 复用参数与请求头

```yaml
components:
  parameters:
    ChapterId:
      name: chapter_id
      in: query
      required: false
      schema:
        type: string
      description: 按章节过滤历史投票结果
    ContentPackageId:
      name: content_package_id
      in: path
      required: true
      schema:
        type: string
      description: 内容包 ID
    RegionId:
      name: region_id
      in: path
      required: true
      schema:
        type: string
      description: 区域 ID
    ReviewObjectId:
      name: object_id
      in: path
      required: true
      schema:
        type: string
      description: 审核对象 ID
    OpsContentPackageId:
      name: id
      in: path
      required: true
      schema:
        type: string
      description: 运营接口中的内容包 ID
    Page:
      name: page
      in: query
      required: false
      schema:
        type: integer
        minimum: 1
        default: 1
    PageSize:
      name: page_size
      in: query
      required: false
      schema:
        type: integer
        minimum: 1
        maximum: 100
        default: 20
  headers:
    X-Request-Id:
      description: 服务端生成的请求追踪 ID
      schema:
        type: string
    Idempotency-Key:
      description: 提交投票时的幂等键
      schema:
        type: string
  securitySchemes:
    bearerAuth:
      type: openIdConnect
      openIdConnectUrl: https://auth.example.com/.well-known/openid-configuration
      description: OIDC 签发的 JWT Bearer Token
```

### 复用数据结构

```yaml
components:
  schemas:
    ErrorResponse:
      type: object
      required: [code, message, request_id]
      properties:
        code:
          type: string
          example: INVALID_VOTE_STATE
        message:
          type: string
          example: 当前投票周期不可投票
        request_id:
          type: string
          example: req_vote_current_409
        details:
          type: array
          items:
            type: object
            properties:
              location:
                type: string
                enum: [body, query, path, header]
              field:
                type: string
              issue:
                type: string
              rejected_value: {}
            required: [location, field, issue]

    VoteCycle:
      type: object
      required: [vote_cycle_id, chapter_id, status, starts_at, ends_at]
      properties:
        vote_cycle_id:
          type: string
        chapter_id:
          type: string
        status:
          type: string
          enum: [open, closed, finalized]
        starts_at:
          type: string
          format: date-time
        ends_at:
          type: string
          format: date-time

    VotePlayerContext:
      type: object
      required: [player_id, eligible, has_voted, vote_weight]
      properties:
        player_id:
          type: string
        eligible:
          type: boolean
        reason:
          type: string
          nullable: true
        has_voted:
          type: boolean
        vote_weight:
          type: number
          format: float

    VoteCandidate:
      type: object
      required: [candidate_id, title, summary, region_scope, risk_tags]
      properties:
        candidate_id:
          type: string
        title:
          type: string
        summary:
          type: string
        region_scope:
          type: array
          items:
            type: string
        risk_tags:
          type: array
          items:
            type: string

    VoteCurrentResponse:
      type: object
      required: [request_id, vote_cycle, player_context, candidates]
      properties:
        request_id:
          type: string
        vote_cycle:
          $ref: '#/components/schemas/VoteCycle'
        player_context:
          $ref: '#/components/schemas/VotePlayerContext'
        candidates:
          type: array
          items:
            $ref: '#/components/schemas/VoteCandidate'

    VoteSubmitRequest:
      type: object
      required: [vote_cycle_id, candidate_id]
      properties:
        vote_cycle_id:
          type: string
        candidate_id:
          type: string

    VoteSubmitResponse:
      type: object
      required: [request_id, vote_id, vote_cycle_id, candidate_id, accepted, submitted_at]
      properties:
        request_id:
          type: string
        vote_id:
          type: string
        vote_cycle_id:
          type: string
        candidate_id:
          type: string
        accepted:
          type: boolean
        weight:
          type: number
          format: float
        idempotent_replay:
          type: boolean
          default: false
        submitted_at:
          type: string
          format: date-time

    VoteHistoryCandidate:
      type: object
      required: [candidate_id, title, vote_percent]
      properties:
        candidate_id:
          type: string
        title:
          type: string
        vote_percent:
          type: number
          format: float

    VoteHistoryDelivery:
      type: object
      required: [status, content_package_id, affected_regions]
      properties:
        status:
          type: string
          enum: [pending, gray, live, rolled_back]
        content_package_id:
          type: string
        affected_regions:
          type: array
          items:
            type: string

    VoteHistoryItem:
      type: object
      required:
        [vote_cycle_id, chapter_id, closed_at, winner_candidate_id, winner_title, total_votes, candidates, delivery]
      properties:
        vote_cycle_id:
          type: string
        chapter_id:
          type: string
        closed_at:
          type: string
          format: date-time
        winner_candidate_id:
          type: string
        winner_title:
          type: string
        total_votes:
          type: integer
        candidates:
          type: array
          items:
            $ref: '#/components/schemas/VoteHistoryCandidate'
        delivery:
          $ref: '#/components/schemas/VoteHistoryDelivery'

    VoteHistoryResponse:
      type: object
      required: [request_id, page, page_size, total, items]
      properties:
        request_id:
          type: string
        page:
          type: integer
        page_size:
          type: integer
        total:
          type: integer
        items:
          type: array
          items:
            $ref: '#/components/schemas/VoteHistoryItem'

    ContentUpdateItem:
      type: object
      required: [content_package_id, published_at, affected_regions, gray_visible]
      properties:
        content_package_id:
          type: string
        title:
          type: string
        summary:
          type: string
        published_at:
          type: string
          format: date-time
        affected_regions:
          type: array
          items:
            type: string
        gray_visible:
          type: boolean

    ContentUpdatesResponse:
      type: object
      required: [request_id, items]
      properties:
        request_id:
          type: string
        items:
          type: array
          items:
            $ref: '#/components/schemas/ContentUpdateItem'

    ContentPackageSummary:
      type: object
      required: [content_package_id, status, published_at, affected_regions]
      properties:
        content_package_id:
          type: string
        title:
          type: string
        summary:
          type: string
        status:
          type: string
          enum: [packaged, gray, live, archived, rolled_back]
        published_at:
          type: string
          format: date-time
        affected_regions:
          type: array
          items:
            type: string
        gray_scope:
          $ref: '#/components/schemas/GrayScope'

    ContentPackageResponse:
      type: object
      required: [request_id, content_package]
      properties:
        request_id:
          type: string
        content_package:
          $ref: '#/components/schemas/ContentPackageSummary'

    GrayScope:
      type: object
      properties:
        region_ids:
          type: array
          items:
            type: string
        player_percent:
          type: integer
          minimum: 0
          maximum: 100

    ReleaseContentPackageRequest:
      type: object
      required: [gray_scope, reason]
      properties:
        gray_scope:
          $ref: '#/components/schemas/GrayScope'
        reason:
          type: string

    ReleaseContentPackageResponse:
      type: object
      required: [request_id, content_package_id, status, release_mode]
      properties:
        request_id:
          type: string
        content_package_id:
          type: string
        status:
          type: string
          enum: [gray, live]
        release_mode:
          type: string
          enum: [gray, full]
        released_at:
          type: string
          format: date-time

    RollbackContentPackageRequest:
      type: object
      required: [target_version, reason]
      properties:
        target_version:
          type: string
        reason:
          type: string

    RollbackContentPackageResponse:
      type: object
      required: [request_id, rollback_id, content_package_id, target_version, status]
      properties:
        request_id:
          type: string
        rollback_id:
          type: string
        content_package_id:
          type: string
        target_version:
          type: string
        status:
          type: string
          enum: [queued, running, completed]
        rolled_back_at:
          type: string
          format: date-time

    RegionSummary:
      type: object
      required: [region_id, chapter_id, title, status, visible]
      properties:
        region_id:
          type: string
        chapter_id:
          type: string
        title:
          type: string
        summary:
          type: string
        status:
          type: string
          enum: [locked, active, unstable, archived]
        visible:
          type: boolean

    RegionListResponse:
      type: object
      required: [request_id, items]
      properties:
        request_id:
          type: string
        items:
          type: array
          items:
            $ref: '#/components/schemas/RegionSummary'

    RegionDetailResponse:
      type: object
      required: [request_id, region]
      properties:
        request_id:
          type: string
        region:
          $ref: '#/components/schemas/RegionSummary'

    QuestItem:
      type: object
      required: [quest_id, chapter_id, active_region_id, title, status]
      properties:
        quest_id:
          type: string
        chapter_id:
          type: string
        active_region_id:
          type: string
        title:
          type: string
        summary:
          type: string
        status:
          type: string
          enum: [available, active, completed, failed]

    QuestListResponse:
      type: object
      required: [request_id, items]
      properties:
        request_id:
          type: string
        items:
          type: array
          items:
            $ref: '#/components/schemas/QuestItem'

    CreateVoteCycleRequest:
      type: object
      required: [chapter_id, starts_at, ends_at, candidate_ids, reason]
      properties:
        chapter_id:
          type: string
        starts_at:
          type: string
          format: date-time
        ends_at:
          type: string
          format: date-time
        candidate_ids:
          type: array
          minItems: 1
          items:
            type: string
        reason:
          type: string

    CreateVoteCycleResponse:
      type: object
      required: [request_id, vote_cycle_id, status]
      properties:
        request_id:
          type: string
        vote_cycle_id:
          type: string
        status:
          type: string
          enum: [draft, scheduled, open]

    ReviewApproveRequest:
      type: object
      required: [review_result, reason]
      properties:
        review_result:
          type: string
          enum: [approved, manual_review]
        reason:
          type: string

    ReviewApproveResponse:
      type: object
      required: [request_id, review_id, object_id, review_result, reviewed_at]
      properties:
        request_id:
          type: string
        review_id:
          type: string
        object_id:
          type: string
        review_result:
          type: string
        reviewed_at:
          type: string
          format: date-time
```

### `GET /api/v1/votes/current`

```yaml
paths:
  /api/v1/votes/current:
    get:
      tags: [votes]
      summary: 获取当前投票周期和候选项
      operationId: getCurrentVoteCycle
      responses:
        '200':
          description: 返回当前投票周期、候选项和玩家上下文
          headers:
            X-Request-Id:
              $ref: '#/components/headers/X-Request-Id'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/VoteCurrentResponse'
        '401':
          description: 未认证或 Token 无效
        '404':
          description: 当前不存在有效投票周期
        '409':
          description: 当前投票周期状态不可投票
```

对应错误码建议：

- `VOTE_CYCLE_NOT_FOUND`
- `INVALID_VOTE_STATE`
- `INVALID_TOKEN`

### `POST /api/v1/votes/submit`

```yaml
paths:
  /api/v1/votes/submit:
    post:
      tags: [votes]
      summary: 提交玩家投票
      operationId: submitVote
      parameters:
        - name: Idempotency-Key
          in: header
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/VoteSubmitRequest'
      responses:
        '200':
          description: 投票受理成功或命中幂等重放
          headers:
            X-Request-Id:
              $ref: '#/components/headers/X-Request-Id'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/VoteSubmitResponse'
        '401':
          description: 未认证或 Token 无效
        '403':
          description: 玩家无资格或命中风控
        '404':
          description: 投票周期或候选项不存在
        '409':
          description: 已重复投票或投票周期已关闭
```

对应错误码建议：

- `PLAYER_NOT_ELIGIBLE`
- `VOTE_RISK_BLOCKED`
- `VOTE_CYCLE_NOT_FOUND`
- `CANDIDATE_NOT_FOUND`
- `DUPLICATE_VOTE`
- `VOTE_CYCLE_CLOSED`

补充约定：

- `Idempotency-Key` 为必填请求头
- 应保证 `vote_cycle_id + player_id` 的唯一约束
- 命中幂等重放时仍返回 `200`，并带 `idempotent_replay: true`

### `GET /api/v1/votes/history`

```yaml
paths:
  /api/v1/votes/history:
    get:
      tags: [votes]
      summary: 获取历史投票结果与落地情况
      operationId: getVoteHistory
      parameters:
        - $ref: '#/components/parameters/ChapterId'
        - $ref: '#/components/parameters/Page'
        - $ref: '#/components/parameters/PageSize'
      responses:
        '200':
          description: 返回分页历史投票结果
          headers:
            X-Request-Id:
              $ref: '#/components/headers/X-Request-Id'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/VoteHistoryResponse'
        '400':
          description: 分页或过滤参数不合法
        '401':
          description: 未认证或 Token 无效
```

对应错误码建议：

- `INVALID_ARGUMENT`
- `INVALID_TOKEN`

### 第一批实现备注

- 第一批统一使用 `votes` tag，建议归属 `vote-service`
- 第一批现已与后续批次对齐：详情接口使用 `request_id + data + meta`，列表接口使用 `request_id + data + meta`，写接口使用 `request_id + trace_id + data + meta`
- 第一批已补齐接口级 `security` 作用域声明；当前仍先不展开 `oneOf` 与多语言错误文案
- 第二批接口补齐时，优先复用本节的 `ErrorResponse`、分页参数、请求头和响应包装方式

### 第二批

- `GET /api/v1/content/updates`
- `GET /api/v1/content/packages/{content_package_id}`
- `POST /api/v1/ops/content-packages/{id}/release`
- `POST /api/v1/ops/content-packages/{id}/rollback`

## 第二批草案正文

第二批先覆盖内容查询和运营发布回滚链路，目标是把 `content-service` 的对外读取能力和 `ops` 写接口收敛为下一层可实现的接口草案。由于当前还没有独立的内容包样例文档，本节只定义最小可评审字段，不提前虚构完整业务对象。

### `GET /api/v1/content/updates`

```yaml
paths:
  /api/v1/content/updates:
    get:
      tags: [content]
      summary: 获取当前玩家可见的新内容包
      operationId: getContentUpdates
      responses:
        '200':
          description: 返回当前玩家可见的内容更新列表
          headers:
            X-Request-Id:
              $ref: '#/components/headers/X-Request-Id'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ContentUpdatesResponse'
        '401':
          description: 未认证或 Token 无效
        '503':
          description: 内容更新列表暂不可用
```

对应错误码建议：

- `INVALID_TOKEN`
- `CONTENT_UPDATES_UNAVAILABLE`

### `GET /api/v1/content/packages/{content_package_id}`

```yaml
paths:
  /api/v1/content/packages/{content_package_id}:
    get:
      tags: [content]
      summary: 获取内容包摘要
      operationId: getContentPackage
      parameters:
        - $ref: '#/components/parameters/ContentPackageId'
      responses:
        '200':
          description: 返回内容包摘要和当前可见状态
          headers:
            X-Request-Id:
              $ref: '#/components/headers/X-Request-Id'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ContentPackageResponse'
        '401':
          description: 未认证或 Token 无效
        '403':
          description: 内容包对当前角色不可见
        '404':
          description: 内容包不存在
```

对应错误码建议：

- `INVALID_TOKEN`
- `CONTENT_PACKAGE_NOT_VISIBLE`
- `CONTENT_PACKAGE_NOT_FOUND`

### `POST /api/v1/ops/content-packages/{id}/release`

```yaml
paths:
  /api/v1/ops/content-packages/{id}/release:
    post:
      tags: [ops, content]
      summary: 发布内容包
      operationId: releaseContentPackage
      parameters:
        - $ref: '#/components/parameters/OpsContentPackageId'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ReleaseContentPackageRequest'
      responses:
        '200':
          description: 内容包发布请求受理成功
          headers:
            X-Request-Id:
              $ref: '#/components/headers/X-Request-Id'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ReleaseContentPackageResponse'
        '400':
          description: 缺少原因或请求体非法
        '401':
          description: 未认证或 Token 无效
        '403':
          description: 无内容发布权限
        '404':
          description: 内容包不存在
        '409':
          description: 内容包不满足发布前置条件或已处于 live 状态
```

对应错误码建议：

- `REASON_REQUIRED`
- `CONTENT_RELEASE_FORBIDDEN`
- `CONTENT_PACKAGE_NOT_FOUND`
- `CONTENT_PACKAGE_NOT_RELEASABLE`
- `CONTENT_PACKAGE_ALREADY_LIVE`

### `POST /api/v1/ops/content-packages/{id}/rollback`

```yaml
paths:
  /api/v1/ops/content-packages/{id}/rollback:
    post:
      tags: [ops, content]
      summary: 回滚内容包
      operationId: rollbackContentPackage
      parameters:
        - $ref: '#/components/parameters/OpsContentPackageId'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RollbackContentPackageRequest'
      responses:
        '200':
          description: 内容包回滚请求受理成功
          headers:
            X-Request-Id:
              $ref: '#/components/headers/X-Request-Id'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RollbackContentPackageResponse'
        '400':
          description: 回滚目标非法或缺少原因
        '401':
          description: 未认证或 Token 无效
        '403':
          description: 无内容回滚权限
        '404':
          description: 内容包不存在
        '409':
          description: 当前内容包不可回滚
```

对应错误码建议：

- `REASON_REQUIRED`
- `CONTENT_ROLLBACK_FORBIDDEN`
- `CONTENT_PACKAGE_NOT_FOUND`
- `CONTENT_PACKAGE_NOT_ROLLBACKABLE`
- `ROLLBACK_TARGET_INVALID`

### 第二批实现备注

- 第二批查询接口统一使用 `content` tag，建议归属 `content-service`
- 第二批写接口使用 `ops` 与 `content` 双 tag，体现运营权限和内容包生命周期都属于关键上下文
- 发布与回滚必须串行执行，回滚最小单位为 `content_package_id`
- `release` 与 `rollback` 都必须记录 `reason`，并进入审计链
- 当前 `ContentPackageSummary` 只保留最小摘要字段；后续若补了内容包样例文档，再继续扩充版本、作者、审核记录和投放统计等字段

### 第三批

- `GET /api/v1/world/regions`
- `GET /api/v1/world/regions/{region_id}`
- `GET /api/v1/quests`
- `POST /api/v1/ops/vote-cycles`
- `POST /api/v1/ops/review/{object_id}/approve`

## 第三批草案正文

第三批覆盖世界查询、任务查询以及两类运营写接口。由于当前没有独立的世界/任务/审核样例文档，本节继续保持“最小可评审字段”策略，只补足能支撑服务边界、权限和状态约束讨论的核心结构。

### `GET /api/v1/world/regions`

```yaml
paths:
  /api/v1/world/regions:
    get:
      tags: [world]
      summary: 获取当前可见区域列表
      operationId: getVisibleRegions
      responses:
        '200':
          description: 返回当前玩家可见区域列表
          headers:
            X-Request-Id:
              $ref: '#/components/headers/X-Request-Id'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RegionListResponse'
        '401':
          description: 未认证或 Token 无效
```

对应错误码建议：

- `INVALID_TOKEN`

### `GET /api/v1/world/regions/{region_id}`

```yaml
paths:
  /api/v1/world/regions/{region_id}:
    get:
      tags: [world]
      summary: 获取区域详情和状态
      operationId: getRegionDetail
      parameters:
        - $ref: '#/components/parameters/RegionId'
      responses:
        '200':
          description: 返回区域详情和当前状态
          headers:
            X-Request-Id:
              $ref: '#/components/headers/X-Request-Id'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RegionDetailResponse'
        '401':
          description: 未认证或 Token 无效
        '403':
          description: 区域当前对玩家不可见
        '404':
          description: 区域不存在
```

对应错误码建议：

- `INVALID_TOKEN`
- `REGION_NOT_VISIBLE`
- `REGION_NOT_FOUND`

### `GET /api/v1/quests`

```yaml
paths:
  /api/v1/quests:
    get:
      tags: [quests]
      summary: 获取玩家任务列表
      operationId: getQuestList
      responses:
        '200':
          description: 返回玩家任务列表
          headers:
            X-Request-Id:
              $ref: '#/components/headers/X-Request-Id'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/QuestListResponse'
        '401':
          description: 未认证或 Token 无效
        '503':
          description: 任务列表暂不可用
```

对应错误码建议：

- `INVALID_TOKEN`
- `QUEST_LIST_UNAVAILABLE`

### `POST /api/v1/ops/vote-cycles`

```yaml
paths:
  /api/v1/ops/vote-cycles:
    post:
      tags: [ops, votes]
      summary: 创建投票周期
      operationId: createVoteCycle
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateVoteCycleRequest'
      responses:
        '200':
          description: 投票周期创建成功
          headers:
            X-Request-Id:
              $ref: '#/components/headers/X-Request-Id'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CreateVoteCycleResponse'
        '400':
          description: 缺少原因或请求体非法
        '401':
          description: 未认证或 Token 无效
        '403':
          description: 无运营权限
        '409':
          description: 当前投票周期创建冲突
```

对应错误码建议：

- `REASON_REQUIRED`
- `INSUFFICIENT_SCOPE`
- `VOTE_CYCLE_CONFLICT`

### `POST /api/v1/ops/review/{object_id}/approve`

```yaml
paths:
  /api/v1/ops/review/{object_id}/approve:
    post:
      tags: [review, ops]
      summary: 批准内容对象
      operationId: approveReviewObject
      parameters:
        - $ref: '#/components/parameters/ReviewObjectId'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ReviewApproveRequest'
      responses:
        '200':
          description: 审核批准请求受理成功
          headers:
            X-Request-Id:
              $ref: '#/components/headers/X-Request-Id'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ReviewApproveResponse'
        '400':
          description: 缺少原因或审核结果非法
        '401':
          description: 未认证或 Token 无效
        '403':
          description: 无审核批准权限
        '404':
          description: 审核对象不存在
        '409':
          description: 当前对象不处于可批准状态
```

对应错误码建议：

- `REASON_REQUIRED`
- `REVIEW_APPROVAL_FORBIDDEN`
- `REVIEW_OBJECT_NOT_FOUND`
- `INVALID_REVIEW_STATE`

### 第三批实现备注

- 第三批查询接口分别使用 `world` 和 `quests` tag，对应 `world-service` 与 `player-service/world-service`
- 第三批写接口沿用双 tag 风格，把 `ops` 与业务域上下文同时暴露出来
- `POST /api/v1/ops/vote-cycles` 与 `POST /api/v1/ops/review/{object_id}/approve` 都属于敏感操作，必须进入审计链
- 当前 `CreateVoteCycleRequest` 和 `ReviewApproveRequest` 只保留最小字段；后续若补了独立样例文档，再继续扩展操作人上下文、二次确认和附加审核维度

## 来源文档映射

- `docs/20-specs/backend-data-spec.md`
  - 服务边界、数据模型、事件与异步任务的上游约束
- `docs/30-api/api-overview.md`
  - 接口清单、服务归属和总体入口
- `docs/30-api/api-permissions.md`
  - 角色矩阵、敏感操作和安全定义输入
- `docs/30-api/api-error-codes.md`
  - 错误响应与 HTTP 状态码输入
- `docs/30-api/api-examples-vote.md`
  - 第一批接口的请求响应样例输入
- `docs/30-api/api-examples-content.md`
  - 第二批接口的请求响应样例输入
- `docs/30-api/api-examples-world-ops.md`
  - 第三批接口的请求响应样例输入

## 后续补齐顺序

1. ~~抽象成功响应包装复用层~~（已完成：`RequestScopedResponse`、`TraceableResponse`、`ListResponseBase`、`DetailResponseBase`、`OperationResponseBase`）
2. ~~错误层原子化与特化~~（已完成：所有跨端点高频错误响应已有特化 schema）
3. 补齐少数端点边界条件的字段级错误 details 样例（如 `ROLLBACK_TARGET_INVALID` 等领域语义错误的 details 补充说明）
4. 服务端实现阶段，将预留错误码（如 `INTERNAL_ERROR`、`TOKEN_EXPIRED`）按需落地到 OpenAPI
5. 端点数量超过 25-30 个时，评估按服务拆分为多文件草案

## 与其他文档的关系

- `docs/30-api/api-overview.md`
  - 提供接口总入口，本文档负责把这些接口继续收敛为 OpenAPI 草案。
- `docs/30-api/api-permissions.md`
  - 提供安全定义和角色访问边界输入。
- `docs/30-api/api-error-codes.md`
  - 提供错误响应和状态码输入。
- `docs/30-api/api-examples-vote.md`
  - 提供第一批接口样例输入。
- `docs/30-api/api-examples-content.md`
  - 提供第二批接口样例输入。
- `docs/30-api/api-examples-world-ops.md`
  - 提供第三批接口样例输入。
- `docs/30-api/openapi-v1-draft.yaml`
  - 当前单文件 OpenAPI 草案输出。
- `docs/20-specs/backend-data-spec.md`
  - 作为更高权威的执行规范，约束 OpenAPI 草案的最终边界。

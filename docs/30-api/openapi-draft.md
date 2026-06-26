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

- 本文档是 OpenAPI 草案的入口说明，不是已经补齐完成的正式 OpenAPI 成品。
- 当前接口边界、服务职责和数据约束仍以 `docs/20-specs/backend-data-spec.md` 为准。
- 本文档回答“OpenAPI 草案准备怎么组织、现阶段已具备哪些输入、下一步先补什么”。

## 当前状态

- 当前已建立 OpenAPI 草案入口，但尚未形成可直接导入工具链的完整 OpenAPI 文件。
- 当前已经具备的上游输入包括：
  - `docs/30-api/api-overview.md`
  - `docs/30-api/api-permissions.md`
  - `docs/30-api/api-error-codes.md`
  - `docs/30-api/api-examples-vote.md`
- 当前仍缺少的关键内容包括：
  - 第二批和第三批接口组的请求响应草案
  - 更完整的通用 schema 复用层
  - 过滤、排序、审计字段和安全定义细化
  - 按服务拆分后的 path 与 tag 进一步展开

## 草案收敛原则

- 先收敛接口入口、角色、错误码和样例，再生成完整 OpenAPI 结构。
- 若 `docs/30-api/` 与 `docs/20-specs/backend-data-spec.md` 冲突，以后者为准。
- OpenAPI 草案应优先覆盖最小实施路径相关接口，不要求一开始追求全量覆盖。
- 每次新增接口样例、权限约束或错误码后，应判断是否需要同步更新本文档和后续 OpenAPI 结构。

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

## 当前建议优先补齐的接口组

### 第一批

- `GET /api/v1/votes/current`
- `POST /api/v1/votes/submit`
- `GET /api/v1/votes/history`

原因：

- 已有较完整样例文档。
- 属于首个最小落地目标中最容易收敛的一条主线能力。
- 涉及角色、错误码、幂等和审计要求，适合作为 OpenAPI 草案模板。

## 第一批草案正文

以下内容仍是文档级草案，不是已经定稿的单文件 OpenAPI 成品；目的是先把第一批投票链路的 `paths`、`components` 和复用约定收敛出来。

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
      type: http
      scheme: bearer
      bearerFormat: JWT
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
- `UNAUTHORIZED`

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
- `UNAUTHORIZED`

### 第一批实现备注

- 第一批统一使用 `votes` tag，建议归属 `vote-service`
- 第一批成功响应都带 `request_id`，并通过 `X-Request-Id` 响应头暴露链路追踪字段
- 第一批先不展开 `oneOf`、多语言错误文案和完整安全作用域，只保留足够支撑实现与评审的最小结构
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

- `UNAUTHORIZED`
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

- `UNAUTHORIZED`
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

## 后续补齐顺序

1. 先补投票链路以外的内容链路和运营链路样例。
2. 再收敛分页、过滤、审计字段、幂等和通用 schema。
3. 然后把 `docs/30-api/` 下现有专题文档进一步下沉为可复制的 OpenAPI 结构。
4. 最后再决定是否输出单文件 OpenAPI 或按服务拆分草案。

## 与其他文档的关系

- `docs/30-api/api-overview.md`
  - 提供接口总入口，本文档负责把这些接口继续收敛为 OpenAPI 草案。
- `docs/30-api/api-permissions.md`
  - 提供安全定义和角色访问边界输入。
- `docs/30-api/api-error-codes.md`
  - 提供错误响应和状态码输入。
- `docs/30-api/api-examples-vote.md`
  - 提供第一批接口样例输入。
- `docs/20-specs/backend-data-spec.md`
  - 作为更高权威的执行规范，约束 OpenAPI 草案的最终边界。

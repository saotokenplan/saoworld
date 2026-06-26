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
  - 主要链路的完整请求响应样例
  - 统一的 schema 定义
  - 分页、过滤、排序、幂等和审计字段约定
  - 按服务拆分后的 path 与 tag 组织

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

### 第二批

- `GET /api/v1/content/updates`
- `GET /api/v1/content/packages/{content_package_id}`
- `POST /api/v1/ops/content-packages/{id}/release`
- `POST /api/v1/ops/content-packages/{id}/rollback`

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

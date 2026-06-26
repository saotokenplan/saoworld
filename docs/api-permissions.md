# API 权限矩阵

## 目的

本文档用于统一整理当前接口角色、访问范围、敏感操作约束和审计要求，作为后续补 OpenAPI 安全定义、后台权限表和审批链规则的基础文档。

## 当前定位

- 本文档是权限索引，不替代详细规范。
- 权限层级和安全要求以 `docs/specs/backend-data-spec.md` 为准。
- 如果本文件与 `docs/specs/backend-data-spec.md` 冲突，以后者为准。

## 权限角色

### `player`

- 面向普通玩家。
- 允许访问世界、任务、投票和内容更新查询能力。
- 不允许访问运营、审核、生成和发布类接口。

### `ops`

- 面向运营和配置角色。
- 允许创建投票周期、发布内容包、触发回滚和执行运营操作。
- 所有写操作都必须记录操作者和原因。

### `reviewer`

- 面向审核和批准角色。
- 允许处理内容审核流、批准内容对象和触发人工复核结论。
- 不应直接承担内容发布职责，除非额外具备 `ops` 权限。

### `system`

- 面向 Agent、任务队列和自动化流程。
- 主要处理内部长任务、事件消费、状态流转和审计链路。
- 不对外暴露为普通客户端权限。

## 权限原则

- 客户端不得直接访问生成和审核内部接口。
- `vote-service` 只负责投票链路，不直接修改世界状态。
- `generation-service` 只产出草案，不直接上线内容。
- `content-service` 是唯一允许改变内容上线状态的服务。
- 任何敏感操作都必须可追溯到操作者、时间、原因和关联对象。

## 接口权限矩阵

| 方法 | 路径 | 主要角色 | 次要角色 | 说明 |
|---|---|---|---|---|
| `GET` | `/api/v1/world/regions` | `player` | `system` | 查询当前可见区域列表 |
| `GET` | `/api/v1/world/regions/{region_id}` | `player` | `system` | 查询区域详情和状态 |
| `GET` | `/api/v1/quests` | `player` | `system` | 查询玩家任务列表 |
| `GET` | `/api/v1/votes/current` | `player` | `system` | 查询当前投票周期与候选项 |
| `POST` | `/api/v1/votes/submit` | `player` | 无 | 玩家提交投票 |
| `GET` | `/api/v1/votes/history` | `player` | `ops` | 查询历史投票结果与落地情况 |
| `GET` | `/api/v1/content/updates` | `player` | `system` | 查询当前玩家可见的新内容包 |
| `GET` | `/api/v1/content/packages/{content_package_id}` | `player` | `ops` | 查询内容包摘要 |
| `POST` | `/api/v1/ops/vote-cycles` | `ops` | 无 | 创建投票周期 |
| `POST` | `/api/v1/ops/review/{object_id}/approve` | `reviewer` | `ops` | 批准内容对象 |
| `POST` | `/api/v1/ops/content-packages/{id}/release` | `ops` | 无 | 发布内容包 |
| `POST` | `/api/v1/ops/content-packages/{id}/rollback` | `ops` | 无 | 回滚内容包 |

## 按角色划分的访问范围

### `player`

- 允许：
  - 世界查询
  - 任务查询
  - 投票查询与提交
  - 内容更新查询
- 禁止：
  - 创建投票周期
  - 审核批准
  - 发布内容包
  - 回滚内容包

### `ops`

- 允许：
  - 创建投票周期
  - 查看历史投票结果
  - 查询内容包摘要
  - 发布内容包
  - 回滚内容包
- 限制：
  - 不能绕过审核直接发布未通过对象
  - 所有敏感操作都必须带原因

### `reviewer`

- 允许：
  - 审核批准内容对象
  - 输出人工复核结论
- 限制：
  - 不直接进行内容包发布
  - 不直接修改原始生成对象

### `system`

- 允许：
  - 触发长任务
  - 写入状态迁移日志
  - 生产和消费内部事件
  - 执行自动化流程
- 限制：
  - 不直接充当玩家或运营身份调用对外业务接口

## 敏感操作规则

### 投票提交

- 需要玩家身份。
- 需要投票资格校验。
- 必须做设备与行为风控。
- 同一投票周期应保证幂等约束和重复提交保护。

### 审核批准

- 需要 `reviewer` 或具备审核能力的 `ops` 身份。
- 必须记录：
  - `object_id`
  - `review_result`
  - `operator`
  - `reason`
  - `reviewed_at`
- 不允许用主观描述代替结构化审核结论。

### 内容发布

- 只能由 `ops` 触发。
- 必须确认对象已通过审核。
- 必须提供灰度范围或发布策略。
- 必须写入发布摘要和关联原因。

### 内容回滚

- 只能由 `ops` 触发。
- 回滚最小单位必须是 `content_package_id`。
- 必须写明回滚原因、目标版本和操作者。
- 发布与回滚必须串行执行。

## 审计要求

以下接口调用必须进入审计链：

- `POST /api/v1/ops/vote-cycles`
- `POST /api/v1/ops/review/{object_id}/approve`
- `POST /api/v1/ops/content-packages/{id}/release`
- `POST /api/v1/ops/content-packages/{id}/rollback`

每条审计记录至少包含：

- `request_id`
- `trace_id`
- `operator_role`
- `operator_id`
- `action`
- `target_id`
- `reason`
- `result`
- `occurred_at`

## 待补充项

- 更细的接口级权限码定义
- 后台管理系统菜单与接口的映射关系
- 审批链或二次确认规则
- `system` 角色的服务账号模型
- Token 中的角色声明与过期策略

## 建议下一步

1. 把本文件中的角色矩阵下沉到 OpenAPI 安全定义。
2. 为运营和审核接口补请求头、审计字段和错误码要求。
3. 再补一份 `docs/api-error-codes.md`，完善接口实施所需的异常约束。

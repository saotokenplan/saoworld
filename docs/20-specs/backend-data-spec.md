# 后端与数据详细规范

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目标

本规范定义服务边界、核心数据模型、接口契约、异步任务和事件流。目标是让投票、生成、审核、投放、回滚链路形成可追踪、可重试、可审计的后端系统。

## 服务拆分

## 服务列表

- `gateway-service`
  - 客户端统一入口
  - 鉴权、限流、会话上下文
- `player-service`
  - 账号、角色、成长、声望、章节进度
- `world-service`
  - 区域状态、阵营状态、地图与任务可见性
- `vote-service`
  - 候选池、投票资格、投票记录、结算
- `generation-service`
  - 组织生成请求、模板加载、结果落库
- `review-service`
  - 结构化校验、风险判断、人工复核流转
- `content-service`
  - 内容包、灰度投放、版本归档、回滚
- `ops-service`
  - 后台运营入口、指标汇总、Issue 触发

## 服务边界规则

- 客户端不得直接访问生成和审核内部接口
- `vote-service` 不直接修改世界状态，只输出结果
- `generation-service` 不直接上线内容，只产出草案
- `content-service` 是唯一允许改变内容上线状态的服务

## 数据分层

### 业务运行数据

- 玩家账号
- 角色成长
- 区域解锁
- 任务进度
- 声望与阵营关系
- 投票资格与记录

### 世界内容数据

- 区域定义
- NPC 定义
- 任务定义
- 聚落定义
- 事件定义
- 内容包版本

### 审计与回溯数据

- 生成输入快照
- 模型输出快照
- 审核记录
- 人工复核记录
- 上线批次
- 回滚记录

## 核心表结构建议

### `players`

- `player_id`
- `account_id`
- `level`
- `chapter_id`
- `active_region_id`
- `reputation_snapshot`
- `created_at`
- `updated_at`

### `vote_candidates`

- `candidate_id`
- `vote_cycle_id`
- `chapter_id`
- `region_scope`
- `title`
- `description`
- `generated_params`
- `status`

### `votes`

- `vote_id`
- `vote_cycle_id`
- `player_id`
- `candidate_id`
- `weight`
- `device_fingerprint_hash`
- `created_at`

唯一约束建议：

- `vote_cycle_id + player_id` 唯一

### `generation_requests`

- `request_id`
- `vote_cycle_id`
- `source_candidate_id`
- `template_id`
- `input_payload_jsonb`
- `status`
- `created_at`

### `generated_objects`

- `object_id`
- `request_id`
- `object_type`
- `schema_version`
- `object_payload_jsonb`
- `quality_score`
- `status`
- `created_at`

### `review_records`

- `review_id`
- `object_id`
- `review_type`
- `rule_version`
- `result`
- `risk_level`
- `detail_jsonb`
- `reviewed_at`

### `content_packages`

- `content_package_id`
- `chapter_id`
- `region_id`
- `package_version`
- `source_vote_cycle_id`
- `source_request_id`
- `status`
- `gray_scope_jsonb`
- `released_at`

### `rollback_records`

- `rollback_id`
- `content_package_id`
- `rollback_reason`
- `operator_type`
- `target_version`
- `created_at`

## 数据库约束

- 强事务主数据统一进入 PostgreSQL
- 半结构化对象使用 `jsonb`
- 所有内容对象必须带 `schema_version`
- 所有表必须包含 `created_at` 和 `updated_at`
- 关键状态字段必须使用枚举或受控字符串

## API 规范

### 通用约定

- 协议：`HTTPS + JSON`
- 认证：`Bearer Token`
- 时间字段统一使用 ISO 8601
- 接口版本统一前缀 `/api/v1`
- 错误响应统一结构：

```json
{
  "code": "INVALID_VOTE_STATE",
  "message": "当前投票周期不可投票",
  "request_id": "req_001"
}
```

### 玩家与世界接口

- `GET /api/v1/world/regions`
  - 获取当前可见区域列表
- `GET /api/v1/world/regions/{region_id}`
  - 获取区域详情和状态
- `GET /api/v1/quests`
  - 获取玩家任务列表

### 投票接口

- `GET /api/v1/votes/current`
  - 获取当前投票周期与候选项
- `POST /api/v1/votes/submit`
  - 提交投票
- `GET /api/v1/votes/history`
  - 获取历史投票结果与落地情况

### 内容投放接口

- `GET /api/v1/content/updates`
  - 获取当前玩家可见的新内容包
- `GET /api/v1/content/packages/{content_package_id}`
  - 获取内容包摘要

### 运营接口

- `POST /api/v1/ops/vote-cycles`
  - 创建投票周期
- `POST /api/v1/ops/review/{object_id}/approve`
  - 批准内容对象
- `POST /api/v1/ops/content-packages/{id}/release`
  - 发布内容包
- `POST /api/v1/ops/content-packages/{id}/rollback`
  - 回滚内容包

## 异步任务规范

所有长任务必须走任务队列，不允许在同步接口里直接执行。

### 推荐任务

- `generate_content_batch`
- `run_world_consistency_review`
- `run_balance_review`
- `package_content_batch`
- `release_content_package`
- `rollback_content_package`
- `daily_gate_scan`

### 任务要求

- 每个任务必须有 `task_id`
- 支持重试与幂等
- 必须写入状态迁移日志
- 必须区分“可重试失败”和“不可重试失败”

## 事件流规范

建议内部事件总线至少包含以下主题：

- `vote.cycle.closed`
- `vote.result.finalized`
- `generation.request.created`
- `generation.batch.completed`
- `review.batch.completed`
- `content.package.released`
- `content.package.rolled_back`

### 事件消息字段

- `event_id`
- `event_type`
- `occurred_at`
- `trace_id`
- `producer`
- `payload`

## 权限与安全

### 权限层级

- `player`
  - 普通玩家行为
- `ops`
  - 运营和配置行为
- `reviewer`
  - 审核与批准
- `system`
  - Agent 和自动化任务

### 安全要求

- 所有运营接口必须记录操作者和原因
- 敏感操作必须支持二次确认或审批链
- 投票接口必须做设备与行为风控
- 内容管理接口必须审计请求体和结果

## 性能与一致性要求

- 投票提交接口 p95 响应时间应小于 `300ms`
- 当前投票结果查询应支持缓存
- 内容包发布与回滚必须串行执行
- 单个投票周期的结算必须保证幂等
- 所有状态变更必须可根据 `trace_id` 串联追踪

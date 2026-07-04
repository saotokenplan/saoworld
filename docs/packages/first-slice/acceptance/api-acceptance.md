# API 接口验收标准

> 版本：v1.0.0
> 创建时间：2026-07-04

## 概述

API 接口验收标准定义了投票系统各 API 接口的验收要求和测试用例，确保 API 接口的正确性、一致性和可用性。

## 通用接口验收

### 响应格式验收

**验收要求**：
- 所有成功响应必须使用统一 envelope 格式（`request_id`、`data`、`meta`、`trace_id`）
- 所有错误响应必须使用统一错误结构（`code`、`message`、`request_id`、`details`）
- HTTP 状态码与业务场景匹配
- 响应头必须包含 `X-Request-Id`
- 响应头必须包含 `X-Trace-Id`（如果请求携带了）

**测试用例**：
- 成功响应包含 `request_id` 字段 ✓
- 成功响应包含 `data` 字段 ✓
- 列表接口响应包含 `meta` 字段 ✓
- 错误响应包含 `code` 字段 ✓
- 错误响应包含 `message` 字段 ✓
- 错误响应包含 `request_id` 字段 ✓
- 参数校验错误响应包含 `details` 字段 ✓
- 响应头包含 `X-Request-Id` ✓
- 响应头包含 `X-Trace-Id`（请求携带时）✓

### 请求头验收

**验收要求**：
- 玩家接口必须携带 `X-Player-Id` 请求头
- 写接口必须携带 `X-Trace-Id` 请求头
- 运营写接口必须携带 `Idempotency-Key` 请求头
- 认证接口必须携带 `Authorization` 请求头

**测试用例**：
- 玩家接口缺少 `X-Player-Id` 应返回 400 错误 ✓
- 写接口缺少 `X-Trace-Id` 应返回 400 错误 ✓
- 运营写接口缺少 `Idempotency-Key` 应返回 400 错误 ✓
- 认证接口缺少 `Authorization` 应返回 401 错误 ✓

### 时间格式验收

**验收要求**：
- 所有时间字段使用 ISO 8601 / RFC 3339 格式（UTC）
- 响应中的时间字段带时区信息

**测试用例**：
- 响应时间字段格式为 ISO 8601 ✓
- 响应时间字段带时区信息（Z 或 +00:00）✓

### 分页接口验收

**验收要求**：
- 列表接口支持 `limit` 和 `offset` 参数
- `limit` 默认值为 20，范围 1-100
- `offset` 默认值为 0，>= 0
- 响应 `meta` 包含 `total`、`limit`、`offset`

**测试用例**：
- 使用默认参数分页查询 ✓
- 使用自定义 `limit` 参数查询 ✓
- 使用自定义 `offset` 参数查询 ✓
- `limit` 超出范围（> 100）应返回 400 错误 ✓
- `limit` <= 0 应返回 400 错误 ✓
- `offset` < 0 应返回 400 错误 ✓
- 响应 `meta.total` 正确 ✓
- 响应 `meta.limit` 正确 ✓
- 响应 `meta.offset` 正确 ✓

## 玩家接口验收

### 获取当前投票周期

**接口**：`GET /api/v1/votes/current`

**验收要求**：
- 返回当前开放的投票周期信息
- 返回候选项列表
- 当前无开放投票周期时返回 404 错误

**测试用例**：
- 正常查询当前投票周期 ✓
- 当前无开放投票周期时返回 404 错误 ✓
- 返回的候选项列表正确 ✓
- 响应格式符合 envelope 规范 ✓

### 提交投票

**接口**：`POST /api/v1/votes/submit`

**验收要求**：
- 提交投票成功
- 必须提供 `candidate_id` 和 `Idempotency-Key`
- 同一玩家在同一周期内只能投一票

**测试用例**：
- 正常提交投票 ✓
- 缺少 `candidate_id` 应返回 400 错误 ✓
- 缺少 `Idempotency-Key` 应返回 400 错误 ✓
- 同一玩家在同一周期内重复投票应返回 409 错误 ✓
- 使用相同 `Idempotency-Key` 重复提交应返回首次结果 ✓
- 响应格式符合 envelope 规范 ✓

### 获取投票历史

**接口**：`GET /api/v1/votes/history`

**验收要求**：
- 返回历史投票结果列表
- 支持分页查询
- 支持按章节过滤

**测试用例**：
- 正常查询历史投票结果 ✓
- 分页查询正确 ✓
- 按章节过滤正确 ✓
- 响应格式符合 envelope 规范 ✓

## 运营接口验收

### 创建投票周期

**接口**：`POST /api/v1/ops/vote-cycles`

**验收要求**：
- 创建投票周期成功
- 必须提供所有必填字段
- 创建后状态为 draft
- 必须携带 `Idempotency-Key`

**测试用例**：
- 正常创建投票周期 ✓
- 缺少必填字段应返回 400 错误 ✓
- `ends_at` <= `starts_at` 应返回 400 错误 ✓
- 缺少 `Idempotency-Key` 应返回 400 错误 ✓
- 创建成功后状态为 draft ✓
- 响应格式符合 envelope 规范 ✓

### 计划投票周期

**接口**：`POST /api/v1/ops/vote-cycles/{vote_cycle_id}/schedule`

**验收要求**：
- 将 draft 状态的投票周期计划为 scheduled
- 必须携带 `Idempotency-Key` 和 `reason`

**测试用例**：
- 正常计划投票周期 ✓
- 非 draft 状态计划应返回 409 错误 ✓
- 缺少 `Idempotency-Key` 应返回 400 错误 ✓
- 缺少 `reason` 应返回 400 错误 ✓
- 计划成功后状态为 scheduled ✓
- 响应格式符合 envelope 规范 ✓

### 开放投票周期

**接口**：`POST /api/v1/ops/vote-cycles/{vote_cycle_id}/open`

**验收要求**：
- 将 scheduled 状态的投票周期开放为 open
- 同一章节下只能有一个 open 状态的投票周期
- 必须携带 `Idempotency-Key` 和 `reason`

**测试用例**：
- 正常开放投票周期 ✓
- 非 scheduled 状态开放应返回 409 错误 ✓
- 同一章节下已有开放投票周期时开放应返回 409 错误 ✓
- 缺少 `Idempotency-Key` 应返回 400 错误 ✓
- 缺少 `reason` 应返回 400 错误 ✓
- 开放成功后状态为 open ✓
- 响应格式符合 envelope 规范 ✓

### 关闭投票周期

**接口**：`POST /api/v1/ops/vote-cycles/{vote_cycle_id}/close`

**验收要求**：
- 将 open 状态的投票周期关闭为 closed
- 关闭后自动计票
- 必须携带 `Idempotency-Key` 和 `reason`

**测试用例**：
- 正常关闭投票周期 ✓
- 非 open 状态关闭应返回 409 错误 ✓
- 缺少 `Idempotency-Key` 应返回 400 错误 ✓
- 缺少 `reason` 应返回 400 错误 ✓
- 关闭成功后状态为 closed ✓
- 关闭后自动计票 ✓
- 响应格式符合 envelope 规范 ✓

### 结算投票周期

**接口**：`POST /api/v1/ops/vote-cycles/{vote_cycle_id}/finalize`

**验收要求**：
- 将 closed 状态的投票周期结算为 finalized
- 结算时确定获胜候选项并标记为 selected
- 必须携带 `Idempotency-Key` 和 `reason`

**测试用例**：
- 正常结算投票周期 ✓
- 非 closed 状态结算应返回 409 错误 ✓
- 缺少 `Idempotency-Key` 应返回 400 错误 ✓
- 缺少 `reason` 应返回 400 错误 ✓
- 结算成功后状态为 finalized ✓
- 获胜候选项状态为 selected ✓
- 响应格式符合 envelope 规范 ✓

## 错误码验收

### 通用错误码

**验收要求**：
- 未认证请求返回 `INVALID_TOKEN`（401）
- 权限不足请求返回 `INSUFFICIENT_SCOPE`（403）
- 资源不存在返回 `RESOURCE_NOT_FOUND`（404）
- 参数校验错误返回 `INVALID_ARGUMENT`（400）

**测试用例**：
- 未认证请求返回 `INVALID_TOKEN`（401）✓
- 权限不足请求返回 `INSUFFICIENT_SCOPE`（403）✓
- 资源不存在返回 `RESOURCE_NOT_FOUND`（404）✓
- 参数校验错误返回 `INVALID_ARGUMENT`（400）✓

### 投票接口错误码

**验收要求**：
- 当前无开放投票周期返回 `VOTE_CYCLE_NOT_FOUND`（404）
- 投票周期不可投票返回 `INVALID_VOTE_STATE`（409）
- 玩家不满足投票资格返回 `PLAYER_NOT_ELIGIBLE`（403）
- 候选项不存在返回 `CANDIDATE_NOT_FOUND`（404）
- 投票周期已关闭返回 `VOTE_CYCLE_CLOSED`（409）
- 重复投票返回 `DUPLICATE_VOTE`（409）

**测试用例**：
- 当前无开放投票周期返回 `VOTE_CYCLE_NOT_FOUND`（404）✓
- 投票周期不可投票返回 `INVALID_VOTE_STATE`（409）✓
- 玩家不满足投票资格返回 `PLAYER_NOT_ELIGIBLE`（403）✓
- 候选项不存在返回 `CANDIDATE_NOT_FOUND`（404）✓
- 投票周期已关闭返回 `VOTE_CYCLE_CLOSED`（409）✓
- 重复投票返回 `DUPLICATE_VOTE`（409）✓

## 幂等性验收

### Idempotency-Key 处理

**验收要求**：
- 同一 `Idempotency-Key` 重复提交只执行一次
- 不同 `Idempotency-Key` 可以正常提交
- `Idempotency-Key` 全局唯一

**测试用例**：
- 同一 `Idempotency-Key` 重复提交只执行一次 ✓
- 不同 `Idempotency-Key` 可以正常提交 ✓
- 使用已存在的 `Idempotency-Key` 提交应返回首次结果 ✓

## 性能验收

### 响应时间

**验收要求**：
- 投票提交接口 p95 响应时间 < 300ms
- 投票查询接口 p95 响应时间 < 100ms
- 结算操作响应时间 < 5 秒

**测试用例**：
- 投票提交接口响应时间测试 ✓
- 投票查询接口响应时间测试 ✓
- 结算操作响应时间测试 ✓

### 并发处理

**验收要求**：
- 支持高并发投票（建议 > 1000 QPS）
- 大量投票记录时结算性能正常

**测试用例**：
- 高并发投票测试 ✓
- 大量投票记录结算测试 ✓
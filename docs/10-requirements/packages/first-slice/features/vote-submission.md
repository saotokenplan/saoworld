# 投票提交

> 版本：v1.0.0
> 创建时间：2026-07-04

## 功能描述

玩家通过投票提交功能参与投票周期，表达对候选方向的偏好。

## 核心流程

1. 玩家查询当前开放的投票周期
2. 玩家选择一个候选项
3. 玩家提交投票（携带幂等键）
4. 系统校验投票资格和状态
5. 系统记录投票行为
6. 系统返回投票成功确认

## 校验规则

### 投票资格校验

- 玩家必须存在（player_id 有效）
- 玩家必须满足投票资格门槛（章节进度、活跃度或贡献度）
- 玩家必须在允许投票的区域范围内

### 投票周期状态校验

- 投票周期必须存在
- 投票周期状态必须为 open
- 投票周期必须在有效时间范围内

### 候选项校验

- 候选项必须存在
- 候选项必须属于当前投票周期
- 候选项状态必须为 active（未撤回）

### 重复投票校验

- 同一玩家在同一投票周期内只能投一票
- 通过 `UNIQUE (vote_cycle_id, player_id)` 约束保证

### 幂等性校验

- 客户端必须提供 `Idempotency-Key` 请求头
- 服务端通过 `UNIQUE (idempotency_key)` 约束保证幂等
- 重复使用同一幂等键时，直接返回首次处理结果

### 风控校验

- 设备指纹哈希校验（device_fingerprint_hash）
- 行为聚类分析
- 频率限制

## 投票权重

- 基础投票权重为 1.0
- 允许根据贡献度进行修正，修正倍率不得超过 1.2
- 权重范围：0 < weight <= 10.0

## 请求结构

```json
{
  "vote_cycle_id": "uuid-string",
  "candidate_id": "uuid-string",
  "player_id": "uuid-string",
  "weight": 1.0,
  "device_fingerprint_hash": "string-hash",
  "reason": "可选，投票原因"
}
```

## 请求头要求

| 请求头 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 是 | Bearer Token |
| X-Trace-Id | string | 是 | 全链路追踪ID |
| Idempotency-Key | string | 是 | 幂等键，防止重复提交 |
| X-Player-Id | string | 是 | 玩家ID |

## 响应结构

成功响应：
```json
{
  "request_id": "req_vote_submit_xxx",
  "data": {
    "vote_id": "uuid-string",
    "vote_cycle_id": "uuid-string",
    "candidate_id": "uuid-string",
    "player_id": "uuid-string",
    "weight": 1.0,
    "created_at": "2026-07-04T10:30:00Z"
  },
  "trace_id": "trace_xxx"
}
```

## 错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|------------|------|
| VOTE_CYCLE_NOT_FOUND | 404 | 当前不存在有效投票周期 |
| INVALID_VOTE_STATE | 409 | 当前投票周期不可投票 |
| PLAYER_NOT_ELIGIBLE | 403 | 玩家不满足投票资格 |
| VOTE_RISK_BLOCKED | 403 | 命中设备或行为风控 |
| CANDIDATE_NOT_FOUND | 404 | 候选项不存在 |
| VOTE_CYCLE_CLOSED | 409 | 投票周期已关闭 |
| CANDIDATE_OUT_OF_SCOPE | 409 | 候选项不属于当前投票周期 |
| DUPLICATE_VOTE | 409 | 同一玩家在同一周期重复投票 |

## 审计要求

投票提交操作必须记录审计日志，包含：
- operator_id：玩家ID
- operator_role：player
- action：vote_submit
- resource_type：vote
- resource_id：vote_id
- request_payload_jsonb：请求体快照
- trace_id：追踪ID

## 接口定义

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| POST | `/api/v1/votes/submit` | votes:submit | 玩家提交投票 |
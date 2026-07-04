# 投票结算

> 版本：v1.0.0
> 创建时间：2026-07-04

## 功能描述

投票结算是投票周期关闭后自动执行的计票流程，根据玩家投票结果确定获胜候选项。

## 触发时机

- 投票周期自动关闭（达到 ends_at 时间）
- 运营手动关闭投票周期

## 结算流程

1. 投票周期关闭（状态变为 closed）
2. 系统查询该周期下所有有效的投票记录
3. 系统按候选项分组统计投票（考虑权重）
4. 系统计算每个候选项的加权总分
5. 系统确定加权总分最高的候选项为获胜者
6. 系统更新获胜候选项状态为 selected
7. 系统更新投票周期状态为 finalized
8. 系统记录结算审计日志

## 计票规则

### 投票有效性判断

- 投票记录必须存在
- 投票记录的 vote_cycle_id 必须匹配当前周期
- 投票记录的 candidate_id 必须存在且状态为 active
- 投票记录的 player_id 必须有效

### 权重计算

每个候选项的总票数 = Σ(投票记录.weight)

### 获胜判定

- 加权总分最高的候选项为获胜者
- 若前两名差值小于阈值，则触发剧情一致性裁决
- 获胜候选项状态更新为 selected

## 结算结果

### 投票周期更新

- status：closed → finalized
- finalized_at：记录结算时间
- winning_candidate_id：记录获胜候选项ID

### 候选项更新

- 获胜候选项：status = selected
- 其他候选项：保持原有状态（active 或 withdrawn）

### 投票记录

- votes 表为 append-only，不做更新
- 每个投票记录的权重已在提交时确定

## 幂等性保障

- 结算操作必须保证幂等
- 同一投票周期多次调用结算接口只执行一次
- 通过状态校验（必须为 closed 状态）保证幂等

## 审计要求

结算操作必须记录审计日志，包含：
- operator_id：系统或运营ID
- operator_role：system 或 ops
- action：vote_cycle_finalized
- resource_type：vote_cycle
- resource_id：vote_cycle_id
- reason：结算原因
- request_payload_jsonb：结算结果快照（各候选项票数、获胜者）
- trace_id：追踪ID

## 接口定义

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| POST | `/api/v1/ops/vote-cycles/{vote_cycle_id}/finalize` | ops:vote-cycles:write | 结算投票 |

## 错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|------------|------|
| VOTE_CYCLE_NOT_FOUND | 404 | 投票周期不存在 |
| INVALID_VOTE_STATE | 409 | 投票周期状态不允许结算（非 closed） |
| NO_CANDIDATES_FOUND | 409 | 投票周期下无有效候选项 |

## 性能要求

- 投票提交接口 p95 响应时间 < 300ms
- 结算操作应在合理时间内完成（建议 < 5 秒）
- 大量投票记录时应考虑分批处理
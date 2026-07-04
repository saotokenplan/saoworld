# 投票结算流程

> 版本：v1.0.0
> 创建时间：2026-07-04

## 概述

投票结算流程描述了投票周期关闭后，系统如何计算投票结果并确定获胜候选项的完整过程。

## 触发条件

### 自动触发

- 投票周期达到结束时间（ends_at）
- 系统定时任务检测到 open 状态的投票周期已过期

### 手动触发

- 运营在后台手动关闭投票周期
- 运营点击"结算"按钮

## 结算流程

### 阶段 1：关闭投票周期

**触发条件**：达到结束时间或运营手动关闭

**操作步骤**：
1. 系统查询 open 状态的投票周期
2. 系统检查当前时间是否 >= ends_at
3. 系统更新投票周期状态为 closed
4. 系统记录审计日志（action: vote_cycle_closed）

**输出**：
- 投票周期状态更新为 closed
- 玩家不可再提交投票

### 阶段 2：计票

**触发条件**：投票周期状态为 closed

**操作步骤**：
1. 系统查询该投票周期下所有有效投票记录
2. 系统按候选项分组统计投票
3. 系统计算每个候选项的加权总分

**计票规则**：
- 投票记录的 vote_cycle_id 必须匹配当前周期
- 投票记录的 candidate_id 必须存在且状态为 active
- 每个候选项的总票数 = Σ(投票记录.weight)

### 阶段 3：确定获胜者

**操作步骤**：
1. 系统比较各候选项的加权总分
2. 系统确定加权总分最高的候选项为获胜者
3. 系统检查前两名差值是否小于阈值

**获胜判定规则**：
- 加权总分最高的候选项为获胜者
- 若前两名差值小于阈值（建议 5%），触发剧情一致性裁决
- 剧情一致性裁决由运营或系统规则决定

### 阶段 4：更新状态

**操作步骤**：
1. 系统更新获胜候选项状态为 selected
2. 系统更新投票周期状态为 finalized
3. 系统记录结算时间（finalized_at）
4. 系统记录获胜候选项（winning_candidate_id）
5. 系统更新候选项的 vote_count

**输出**：
- 获胜候选项状态更新为 selected
- 投票周期状态更新为 finalized
- 获胜候选项的 vote_count 更新

### 阶段 5：记录审计日志

**操作步骤**：
1. 系统写入审计日志到 audit_logs 表
2. action: vote_cycle_finalized
3. operator_role: system 或 ops
4. resource_type: vote_cycle
5. resource_id: vote_cycle_id
6. request_payload_jsonb: 结算结果快照

**结算结果快照内容**：
```json
{
  "total_votes": 1000,
  "candidate_results": [
    {
      "candidate_id": "uuid-string",
      "title": "候选项A",
      "vote_count": 600,
      "vote_percentage": 60.0
    },
    {
      "candidate_id": "uuid-string",
      "title": "候选项B",
      "vote_count": 400,
      "vote_percentage": 40.0
    }
  ],
  "winning_candidate_id": "uuid-string",
  "winning_candidate_title": "候选项A"
}
```

### 阶段 6：通知相关系统

**操作步骤**：
1. 系统生成投票结果事件（vote.result.finalized）
2. 系统通知 generation-service 创建生成请求
3. 系统通知 content-service 准备内容包

**事件内容**：
```json
{
  "event_id": "event_xxx",
  "event_type": "vote.result.finalized",
  "occurred_at": "2026-07-04T00:05:00Z",
  "trace_id": "trace_xxx",
  "producer": "vote-service",
  "payload": {
    "vote_cycle_id": "uuid-string",
    "winning_candidate_id": "uuid-string",
    "winning_candidate_title": "候选项A",
    "total_votes": 1000,
    "chapter_id": "chapter_01",
    "region_scope": ["region_id_1"]
  }
}
```

## 运营手动结算流程

### 步骤 1：查看投票周期

**操作**：运营在后台查看 closed 状态的投票周期

**界面展示**：
- 投票周期信息
- 候选项列表及当前票数（实时统计）
- 投票统计摘要

### 步骤 2：确认结算

**操作**：运营点击"结算"按钮

**确认信息**：
- 总票数
- 各候选项票数
- 预计获胜者

### 步骤 3：执行结算

**系统行为**：
- 执行计票流程
- 更新状态
- 记录审计日志

### 步骤 4：查看结算结果

**界面展示**：
- 结算结果统计
- 获胜候选项
- 各候选项票数和占比
- 结算时间

## 幂等性保障

### 结算操作幂等

- 通过状态校验保证幂等（必须为 closed 状态）
- 同一投票周期多次调用结算接口只执行一次
- 若已为 finalized 状态，直接返回已有结果

### 计票结果幂等

- 计票逻辑基于 append-only 的 votes 表
- 每次计票结果一致
- 不受调用次数影响

## 性能要求

- 结算操作应在合理时间内完成（建议 < 5 秒）
- 支持大量投票记录的快速统计（建议 > 100000 条）
- 可考虑使用数据库聚合查询优化计票性能

## 异常处理

### 投票记录为空

**处理**：
- 检查投票周期下是否有有效候选项
- 若有候选项但无投票，随机选择或由运营决定
- 记录异常日志

### 票数相同

**处理**：
- 触发剧情一致性裁决
- 由运营或系统规则决定获胜者
- 记录裁决原因

### 数据库写入失败

**处理**：
- 回滚所有状态更新
- 记录错误日志
- 允许重试

## 结算结果查询

### 查询接口

**接口**：`GET /api/v1/votes/history`

**响应内容**：
- 投票周期信息
- 获胜候选项
- 各候选项票数和占比
- 结算时间
- 内容包关联信息

## 客户端展示要求

投票结算后客户端必须展示：
- 总票数与各候选项占比
- 最终采用方向
- 预计影响区域
- 预计上线周期
- 上一轮投票结果的实际落地情况
# 投票周期管理

> 版本：v1.0.0
> 创建时间：2026-07-04

## 功能描述

投票周期是投票系统的核心时间窗口，运营人员通过管理投票周期来控制投票活动的节奏和流程。

## 状态机

投票周期状态迁移必须遵循以下路径：

```
draft → scheduled → open → closed → finalized
                             ↑
                             └── 管理员可重新开放（需审计）
```

### 状态说明

| 状态 | 说明 | 允许操作 |
|------|------|----------|
| `draft` | 草稿状态，正在配置投票周期 | 编辑、计划（scheduled） |
| `scheduled` | 已计划，等待开放时间 | 取消、开放（open） |
| `open` | 开放投票，玩家可提交投票 | 关闭（closed） |
| `closed` | 已关闭，正在计票 | 重新开放、结算（finalized） |
| `finalized` | 已结算，结果已确认 | 查看结果 |

### 状态迁移规则

1. **draft → scheduled**
   - 前置条件：投票周期配置完整（章节、开始时间、结束时间、候选项）
   - 操作：运营调用计划接口
   - 后置：状态变为 scheduled

2. **scheduled → open**
   - 前置条件：当前时间 >= starts_at
   - 操作：自动触发或运营手动开放
   - 后置：状态变为 open
   - 约束：同一章节下只能有一个 open 状态的投票周期

3. **open → closed**
   - 前置条件：当前时间 >= ends_at
   - 操作：自动触发或运营手动关闭
   - 后置：状态变为 closed，触发计票流程

4. **closed → finalized**
   - 前置条件：计票完成
   - 操作：运营确认结果或自动结算
   - 后置：状态变为 finalized，winning_candidate_id 写入

5. **closed → open（重新开放）**
   - 前置条件：运营审核通过
   - 操作：运营手动重新开放
   - 后置：状态变为 open
   - 约束：必须记录审计日志，说明重新开放原因

## 核心功能

### 创建投票周期

- 运营创建投票周期草稿
- 必须指定所属章节（chapter_id）
- 必须指定开始时间（starts_at）和结束时间（ends_at）
- 必须指定创建者和创建原因
- 初始状态为 draft

### 编辑投票周期

- 仅 draft 状态可编辑
- 可修改开始时间、结束时间、候选项配置
- 每次修改记录审计日志

### 计划投票周期

- 将投票周期从 draft 状态转换为 scheduled 状态
- 计划后等待开放时间自动开放

### 开放投票

- 将投票周期从 scheduled 状态转换为 open 状态
- 玩家可开始提交投票
- 同一章节下只能有一个开放的投票周期

### 关闭投票

- 将投票周期从 open 状态转换为 closed 状态
- 触发自动计票流程
- 玩家不可再提交投票

### 结算投票

- 将投票周期从 closed 状态转换为 finalized 状态
- 根据加权总分确定获胜候选项
- 标记获胜候选项为 selected
- 记录结算结果到审计日志

## 约束条件

### 唯一性约束
- 同一章节下同时只能有一个状态为 open 的投票周期

### 时间约束
- ends_at 必须大于 starts_at
- 开放操作只能在 starts_at 之后执行
- 关闭操作只能在 ends_at 之后执行或由运营手动触发

### 完整性约束
- 创建时必须包含 chapter_id、starts_at、ends_at、created_by、created_reason
- 开放前必须至少有一个 active 状态的候选项

### 审计约束
- 所有状态迁移操作必须记录审计日志
- 重新开放操作必须提供原因说明

## 运营接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/ops/vote-cycles` | 创建投票周期 |
| POST | `/api/v1/ops/vote-cycles/{vote_cycle_id}/schedule` | 计划投票周期 |
| POST | `/api/v1/ops/vote-cycles/{vote_cycle_id}/open` | 开放投票 |
| POST | `/api/v1/ops/vote-cycles/{vote_cycle_id}/close` | 关闭投票 |
| POST | `/api/v1/ops/vote-cycles/{vote_cycle_id}/finalize` | 结算投票 |

## 玩家接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/votes/current` | 获取当前开放的投票周期与候选项 |
| GET | `/api/v1/votes/history` | 获取历史投票结果 |
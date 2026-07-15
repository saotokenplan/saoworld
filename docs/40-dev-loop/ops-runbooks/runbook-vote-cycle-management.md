# 投票周期管理操作手册

> 文档版本：v1.0
> 创建时间：2026-07-15
> 适用角色：运营人员

## 概述

本文档描述投票周期的完整管理流程，包括创建、调度、开放、关闭和结算的操作步骤。

## 投票周期状态机

```
draft → scheduled → open → closed → finalized
                             ↑
                             └── 管理员可重新开放（需审计）
```

| 状态 | 说明 | 允许操作 |
|------|------|----------|
| `draft` | 草稿状态，可编辑 | 更新、调度 |
| `scheduled` | 已调度，等待开放 | 更新、取消调度 |
| `open` | 开放投票中 | 关闭 |
| `closed` | 已关闭，待结算 | 重新开放、结算 |
| `finalized` | 已结算，不可更改 | 无 |

## 操作流程

### 1. 创建投票周期

**API 调用**：
```bash
POST /api/v1/ops/vote-cycles
Authorization: Bearer <token>
Idempotency-Key: <uuid>
Content-Type: application/json

{
  "chapter_id": "chapter_02",
  "status": "draft",
  "starts_at": "2026-07-16T00:00:00Z",
  "ends_at": "2026-07-23T00:00:00Z",
  "title": "第二章发展方向投票",
  "description": "决定第二章的主要发展方向",
  "candidates": [
    {
      "title": "探索幽光森林深处",
      "summary": "玩家深入幽光森林深处",
      "description": "探索向主线，新增森林深处区域",
      "region_scope": ["region_west_forest"],
      "risk_tags": ["content_risk"],
      "generated_params": {
        "template_type": "quest",
        "template_id": "quest_main",
        "count": 3,
        "region_id": "region_west_forest",
        "chapter_id": "chapter_02",
        "theme": "exploration",
        "difficulty": "medium"
      }
    }
  ],
  "created_by": "ops",
  "created_reason": "Public beta vote cycle"
}
```

**响应**：
```json
{
  "request_id": "req_xxx",
  "data": {
    "vote_cycle_id": "vc_xxx",
    "status": "draft",
    "candidates": [...]
  }
}
```

### 2. 调度投票周期

**API 调用**：
```bash
PUT /api/v1/ops/vote-cycles/{vote_cycle_id}/schedule
Authorization: Bearer <token>
Idempotency-Key: <uuid>
```

**响应**：状态变更为 `scheduled`

### 3. 开放投票周期

**API 调用**：
```bash
PUT /api/v1/ops/vote-cycles/{vote_cycle_id}/open
Authorization: Bearer <token>
Idempotency-Key: <uuid>
```

**前置条件**：
- 当前时间 >= `starts_at`
- 同一 `chapter_id` 下没有其他 `open` 状态的周期

### 4. 关闭投票周期

**API 调用**：
```bash
PUT /api/v1/ops/vote-cycles/{vote_cycle_id}/close
Authorization: Bearer <token>
Idempotency-Key: <uuid>
```

**响应**：状态变更为 `closed`，触发投票结算

### 5. 结算投票周期

**API 调用**：
```bash
PUT /api/v1/ops/vote-cycles/{vote_cycle_id}/finalize
Authorization: Bearer <token>
Idempotency-Key: <uuid>
```

**响应**：状态变更为 `finalized`，计算获胜候选

## 运营检查清单

- [ ] 投票周期创建前：确认候选人生成参数完整
- [ ] 投票周期开放前：确认时间设置合理（建议 7 天）
- [ ] 投票周期关闭前：通知玩家即将结束
- [ ] 投票结算后：验证获胜候选与生成参数对应

## 常见错误码

| 错误码 | 说明 | 处理方式 |
|--------|------|----------|
| `VOTE_CYCLE_NOT_FOUND` | 投票周期不存在 | 检查 vote_cycle_id |
| `INVALID_VOTE_STATE` | 状态不允许当前操作 | 检查状态机 |
| `DUPLICATE_OPEN_CYCLE` | 同一章节已有开放周期 | 先关闭现有周期 |
| `INVALID_TIME_RANGE` | 时间范围无效 | 检查 starts_at 和 ends_at |

## 监控指标

- `vote_cycles_created_total`：投票周期创建总数
- `vote_cycles_open_total`：投票周期开放总数
- `vote_submissions_total`：投票提交总数
- `vote_anomalies_detected_total`：异常检测总数

## 审计日志

所有操作均记录审计日志，包含：
- 操作人（`operator_id`、`operator_role`）
- 操作类型（`vote_cycle_create`、`vote_cycle_schedule`、`vote_cycle_open`、`vote_cycle_close`、`vote_cycle_finalize`）
- 资源 ID（`resource_id`）
- 操作时间（`created_at`）
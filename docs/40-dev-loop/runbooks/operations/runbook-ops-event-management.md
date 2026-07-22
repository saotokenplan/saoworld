# 运营事件配置操作手册

> 文档版本：v1.0
> 创建时间：2026-07-15
> 适用角色：运营人员

## 概述

本文档描述运营事件的完整管理流程，包括创建、激活、暂停、结束和删除的操作步骤。

## 事件类型

| 类型 | 说明 | 配置要点 |
|------|------|----------|
| `double_reward` | 双倍奖励 | multiplier_config_jsonb 配置倍率 |
| `login_bonus` | 登录礼包 | reward_config_jsonb 配置每日奖励 |
| `limited_time` | 限时活动 | start_at/end_at 配置时间范围 |
| `special_drop` | 特殊掉落 | reward_config_jsonb 配置掉落表 |

## 事件状态机

| 状态 | 说明 | 允许操作 |
|------|------|----------|
| `draft` | 草稿状态，可编辑 | 更新、激活 |
| `active` | 活动进行中 | 暂停、结束 |
| `paused` | 已暂停 | 激活、结束 |
| `ended` | 已结束 | 无 |
| `deleted` | 已删除 | 无 |

## 操作流程

### 1. 创建运营事件

**API 调用**：
```bash
POST /api/v1/ops/events
Authorization: Bearer <token>
Idempotency-Key: <uuid>
Content-Type: application/json

{
  "event_name": "公测双倍经验",
  "event_type": "double_reward",
  "status": "draft",
  "start_at": "2026-07-16T00:00:00Z",
  "end_at": "2026-07-30T00:00:00Z",
  "target_scope": "all",
  "target_scope_jsonb": {},
  "reward_config_jsonb": {
    "reward_type": "experience",
    "multiplier": 2.0,
    "description": "公测期间所有任务经验双倍"
  },
  "multiplier_config_jsonb": {
    "experience_multiplier": 2.0
  },
  "description": "公测期间，玩家完成任务获得双倍经验值",
  "rules_jsonb": {
    "valid_quest_types": ["main", "side", "daily"],
    "minimum_player_level": 1
  },
  "created_by": "ops"
}
```

**响应**：
```json
{
  "request_id": "req_xxx",
  "data": {
    "event_id": "evt_xxx",
    "status": "draft"
  }
}
```

### 2. 激活运营事件

**API 调用**：
```bash
PUT /api/v1/ops/events/{event_id}/activate
Authorization: Bearer <token>
Idempotency-Key: <uuid>
```

**前置条件**：
- 当前时间 >= `start_at`
- 无时间重叠的同类型活动

### 3. 暂停运营事件

**API 调用**：
```bash
PUT /api/v1/ops/events/{event_id}/pause
Authorization: Bearer <token>
Idempotency-Key: <uuid>
```

### 4. 结束运营事件

**API 调用**：
```bash
PUT /api/v1/ops/events/{event_id}/end
Authorization: Bearer <token>
Idempotency-Key: <uuid>
```

### 5. 删除运营事件

**API 调用**：
```bash
DELETE /api/v1/ops/events/{event_id}
Authorization: Bearer <token>
Idempotency-Key: <uuid>
```

## 公测活动配置示例

### 双倍经验活动

```json
{
  "event_name": "公测双倍经验",
  "event_type": "double_reward",
  "status": "active",
  "start_at": "<当前时间>",
  "end_at": "<当前时间+14天>",
  "target_scope": "all",
  "reward_config_jsonb": {
    "reward_type": "experience",
    "multiplier": 2.0
  },
  "multiplier_config_jsonb": {
    "experience_multiplier": 2.0
  },
  "rules_jsonb": {
    "valid_quest_types": ["main", "side", "daily"]
  }
}
```

### 双倍贡献度活动

```json
{
  "event_name": "公测双倍贡献度",
  "event_type": "double_reward",
  "status": "active",
  "start_at": "<当前时间>",
  "end_at": "<当前时间+14天>",
  "target_scope": "all",
  "reward_config_jsonb": {
    "reward_type": "contribution",
    "multiplier": 2.0
  },
  "multiplier_config_jsonb": {
    "contribution_multiplier": 2.0
  },
  "rules_jsonb": {
    "valid_actions": ["quest_complete", "vote_submit", "npc_interact"]
  }
}
```

### 登录礼包活动

```json
{
  "event_name": "公测登录礼包",
  "event_type": "login_bonus",
  "status": "active",
  "start_at": "<当前时间>",
  "end_at": "<当前时间+7天>",
  "target_scope": "all",
  "reward_config_jsonb": {
    "reward_type": "login_bonus",
    "daily_rewards": [
      {"day": 1, "items": [{"item_key": "gold", "quantity": 100}]},
      {"day": 2, "items": [{"item_key": "gold", "quantity": 200}]},
      {"day": 3, "items": [{"item_key": "experience_potion", "quantity": 1}]},
      {"day": 4, "items": [{"item_key": "gold", "quantity": 300}]},
      {"day": 5, "items": [{"item_key": "contribution_token", "quantity": 50}]},
      {"day": 6, "items": [{"item_key": "gold", "quantity": 500}]},
      {"day": 7, "items": [{"item_key": "rare_equipment_box", "quantity": 1}]}
    ]
  },
  "rules_jsonb": {
    "requirement": "daily_login",
    "consecutive_days": true,
    "reset_on_miss": false
  }
}
```

## 运营检查清单

- [ ] 活动创建前：确认时间范围合理
- [ ] 活动激活前：确认奖励配置完整
- [ ] 活动进行中：监控参与人数和奖励发放
- [ ] 活动结束后：统计活动效果

## 常见错误码

| 错误码 | 说明 | 处理方式 |
|--------|------|----------|
| `EVENT_NOT_FOUND` | 事件不存在 | 检查 event_id |
| `EVENT_NAME_EXISTS` | 事件名称已存在 | 修改名称 |
| `INVALID_EVENT_STATUS` | 状态不允许当前操作 | 检查状态机 |
| `EVENT_TIME_OVERLAP` | 时间重叠 | 调整时间或结束已有活动 |
| `INVALID_EVENT_CONFIG` | 配置无效 | 检查 JSONB 配置格式 |

## 监控指标

- `ops_events_created_total`：事件创建总数
- `ops_events_active_count`：当前活跃事件数
- `ops_event_triggers_total`：事件触发次数

## 审计日志

所有操作均记录审计日志，包含：
- 操作人（`operator_id`、`operator_role`）
- 操作类型（`event_create`、`event_update`、`event_activate`、`event_pause`、`event_end`、`event_delete`）
- 资源 ID（`resource_id`）
- 操作时间（`created_at`）
# 投票结果展示

> 版本：v1.0.0
> 创建时间：2026-07-04

## 功能描述

投票结果展示功能为玩家和运营提供投票周期状态、候选项信息、投票统计和历史结果查询能力。

## 客户端展示要求

投票结算后客户端必须展示：

- 总票数与各候选项占比
- 最终采用方向
- 预计影响区域
- 预计上线周期
- 上一轮投票结果的实际落地情况

## 查询接口

### 获取当前投票周期

**接口**：`GET /api/v1/votes/current`

**说明**：获取当前开放的投票周期及其候选项信息

**Scope**：`votes:read`

**响应结构**：
```json
{
  "request_id": "req_vote_current_xxx",
  "data": {
    "vote_cycle_id": "uuid-string",
    "chapter_id": "chapter_01",
    "status": "open",
    "starts_at": "2026-07-04T00:00:00Z",
    "ends_at": "2026-07-11T00:00:00Z",
    "candidates": [
      {
        "candidate_id": "uuid-string",
        "title": "候选项标题",
        "summary": "候选项描述摘要",
        "description": "详细描述",
        "region_scope": ["region_id_1"],
        "risk_tags": ["risk_tag_1"],
        "status": "active",
        "vote_count": 0
      }
    ],
    "winning_candidate_id": null,
    "finalized_at": null
  },
  "meta": {
    "total": 1,
    "limit": 20,
    "offset": 0
  }
}
```

### 获取历史投票结果

**接口**：`GET /api/v1/votes/history`

**说明**：获取历史投票周期及其结果

**Scope**：`votes:history:read`

**查询参数**：
- `limit`：每页数量，默认 20
- `offset`：偏移量，默认 0
- `chapter_id`：可选，按章节过滤

**响应结构**：
```json
{
  "request_id": "req_vote_history_xxx",
  "data": [
    {
      "vote_cycle_id": "uuid-string",
      "chapter_id": "chapter_01",
      "status": "finalized",
      "starts_at": "2026-06-27T00:00:00Z",
      "ends_at": "2026-07-04T00:00:00Z",
      "winning_candidate_id": "uuid-string",
      "winning_candidate": {
        "title": "获胜候选项",
        "region_scope": ["region_id_1"]
      },
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
      "finalized_at": "2026-07-04T00:05:00Z",
      "content_package_id": "pkg_xxx"
    }
  ],
  "meta": {
    "total": 10,
    "limit": 20,
    "offset": 0
  },
  "trace_id": "trace_xxx"
}
```

## 结果统计

### 总票数

所有有效投票记录的数量之和。

### 各候选项占比

每个候选项的投票数占总票数的百分比。

### 获胜判定

加权总分最高的候选项为获胜者。

## 历史落地情况

查询历史投票结果时，应关联展示对应的内容包信息，说明投票结果的实际落地情况：

- 内容包 ID
- 内容包标题
- 发布状态（gray/live/archived）
- 影响区域
- 上线时间

## 错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|------------|------|
| VOTE_CYCLE_NOT_FOUND | 404 | 当前不存在有效投票周期 |
| INVALID_VOTE_STATE | 409 | 当前投票周期不可投票 |

## 权限要求

| 接口 | 角色 | Scope |
|------|------|-------|
| GET /api/v1/votes/current | player, system | votes:read |
| GET /api/v1/votes/history | player, ops, system | votes:history:read |

## 缓存策略

- 当前投票周期信息可缓存，缓存时间建议 5 分钟
- 历史投票结果可缓存，缓存时间建议 1 小时
- 投票状态变更时应主动失效缓存
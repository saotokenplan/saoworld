# 事件消息 Schema

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 适用范围

本文档定义内部事件总线的事件主题、消息格式、触发时机和消费者列表。所有服务间异步通信必须严格遵循本规范。

## 事件消息通用结构

所有事件消息必须包含以下通用字段：

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `event_id` | string | 是 | 事件唯一 ID，格式：`evt_<uuid>` | `evt_a1b2c3d4e5f6` |
| `event_type` | string | 是 | 事件类型，与主题一致 | `vote.cycle.closed` |
| `occurred_at` | string | 是 | 事件发生时间（ISO 8601 UTC） | `2026-07-04T10:30:00Z` |
| `trace_id` | string | 是 | 全链路追踪 ID | `trace_abc123def456` |
| `producer` | string | 是 | 生产者服务名 | `vote-service` |
| `payload` | object | 是 | 事件业务数据 | 见各事件定义 |

### 通用消息示例

```json
{
  "event_id": "evt_a1b2c3d4e5f6",
  "event_type": "vote.cycle.closed",
  "occurred_at": "2026-07-04T10:30:00Z",
  "trace_id": "trace_vote_001",
  "producer": "vote-service",
  "payload": {
    "vote_cycle_id": "vc_202607_01",
    "chapter_id": "chapter_02",
    "closed_at": "2026-07-04T10:30:00Z"
  }
}
```

---

## 1. vote.cycle.closed（投票周期关闭）

### 事件信息

| 属性 | 值 |
|------|-----|
| 主题 | `vote.cycle.closed` |
| 触发时机 | 投票周期从 `open` 状态迁移到 `closed` 时 |
| 生产者 | vote-service |
| 消费者 | generation-service、ops-service |

### Payload 字段

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `vote_cycle_id` | string | 是 | 投票周期 ID | `vc_202607_01` |
| `chapter_id` | string | 是 | 章节 ID | `chapter_02` |
| `region_id` | string | 否 | 关联区域 ID | `region_wasteland_01` |
| `closed_at` | string | 是 | 关闭时间（ISO 8601 UTC） | `2026-07-04T10:30:00Z` |
| `total_votes` | int | 是 | 总投票数 | `1523` |
| `candidate_count` | int | 是 | 候选项数量 | `3` |

### Payload 示例

```json
{
  "vote_cycle_id": "vc_202607_01",
  "chapter_id": "chapter_02",
  "region_id": "region_wasteland_01",
  "closed_at": "2026-07-04T10:30:00Z",
  "total_votes": 1523,
  "candidate_count": 3
}
```

### 消费者处理逻辑

- **generation-service**：触发内容生成准备，加载世界骨架快照
- **ops-service**：记录运营仪表盘数据，通知相关人员

---

## 2. vote.result.finalized（投票结果确认）

### 事件信息

| 属性 | 值 |
|------|-----|
| 主题 | `vote.result.finalized` |
| 触发时机 | 投票周期从 `closed` 状态迁移到 `finalized` 时 |
| 生产者 | vote-service |
| 消费者 | generation-service、content-service、ops-service |

### Payload 字段

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `vote_cycle_id` | string | 是 | 投票周期 ID | `vc_202607_01` |
| `chapter_id` | string | 是 | 章节 ID | `chapter_02` |
| `region_id` | string | 否 | 关联区域 ID | `region_wasteland_01` |
| `finalized_at` | string | 是 | 确认时间（ISO 8601 UTC） | `2026-07-04T11:00:00Z` |
| `winning_candidate_id` | string | 是 | 获胜候选项 ID | `cand_001` |
| `winning_candidate_title` | string | 是 | 获胜候选项标题 | "机械教团扩张" |
| `total_votes` | int | 是 | 总投票数 | `1523` |
| `vote_result_summary` | object | 否 | 投票结果摘要 | 见下方 |

### vote_result_summary 结构

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `candidates` | list[object] | 各候选项得票情况 | 见示例 |

### Payload 示例

```json
{
  "vote_cycle_id": "vc_202607_01",
  "chapter_id": "chapter_02",
  "region_id": "region_wasteland_01",
  "finalized_at": "2026-07-04T11:00:00Z",
  "winning_candidate_id": "cand_001",
  "winning_candidate_title": "机械教团扩张",
  "total_votes": 1523,
  "vote_result_summary": {
    "candidates": [
      {
        "candidate_id": "cand_001",
        "title": "机械教团扩张",
        "votes": 680,
        "weighted_score": 720.5,
        "percentage": 44.6
      },
      {
        "candidate_id": "cand_002",
        "title": "流亡者营地建设",
        "votes": 520,
        "weighted_score": 548.0,
        "percentage": 34.1
      },
      {
        "candidate_id": "cand_003",
        "title": "中立贸易区开放",
        "votes": 323,
        "weighted_score": 345.2,
        "percentage": 21.2
      }
    ]
  }
}
```

### 消费者处理逻辑

- **generation-service**：根据投票结果创建生成请求，触发内容生成
- **content-service**：准备内容包框架，等待生成结果
- **ops-service**：更新运营仪表盘，生成投票结果报告

---

## 3. generation.request.created（生成请求创建）

### 事件信息

| 属性 | 值 |
|------|-----|
| 主题 | `generation.request.created` |
| 触发时机 | 创建新的生成请求时 |
| 生产者 | generation-service |
| 消费者 | ops-service |

### Payload 字段

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `request_id` | string | 是 | 生成请求 ID | `gen_20260704_001` |
| `template_type` | string | 是 | 模板类型 | `npc` |
| `count` | int | 是 | 生成数量 | `5` |
| `chapter_id` | string | 是 | 章节 ID | `chapter_02` |
| `region_id` | string | 否 | 区域 ID | `region_wasteland_01` |
| `vote_cycle_id` | string | 否 | 关联投票周期 ID | `vc_202607_01` |
| `created_at` | string | 是 | 创建时间 | `2026-07-04T11:05:00Z` |
| `source` | string | 是 | 请求来源：`vote` / `manual` / `scheduled` | `vote` |

### Payload 示例

```json
{
  "request_id": "gen_20260704_001",
  "template_type": "npc",
  "count": 5,
  "chapter_id": "chapter_02",
  "region_id": "region_wasteland_01",
  "vote_cycle_id": "vc_202607_01",
  "created_at": "2026-07-04T11:05:00Z",
  "source": "vote"
}
```

---

## 4. generation.batch.completed（批量生成完成）

### 事件信息

| 属性 | 值 |
|------|-----|
| 主题 | `generation.batch.completed` |
| 触发时机 | 批量生成任务完成（成功或失败）时 |
| 生产者 | generation-service |
| 消费者 | review-service、content-service、ops-service |

### Payload 字段

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `request_id` | string | 是 | 生成请求 ID | `gen_20260704_001` |
| `status` | string | 是 | 状态：`succeeded` / `failed_permanent` | `succeeded` |
| `chapter_id` | string | 是 | 章节 ID | `chapter_02` |
| `region_id` | string | 否 | 区域 ID | `region_wasteland_01` |
| `completed_at` | string | 是 | 完成时间 | `2026-07-04T11:30:00Z` |
| `total_count` | int | 是 | 总生成数量 | `5` |
| `succeeded_count` | int | 是 | 成功数量 | `5` |
| `failed_count` | int | 是 | 失败数量 | `0` |
| `generated_object_ids` | list[string] | 否 | 生成的对象 ID 列表 | `["obj_001", "obj_002"]` |
| `error_message` | string | 否 | 失败时的错误信息 | `null` |

### Payload 示例

```json
{
  "request_id": "gen_20260704_001",
  "status": "succeeded",
  "chapter_id": "chapter_02",
  "region_id": "region_wasteland_01",
  "completed_at": "2026-07-04T11:30:00Z",
  "total_count": 5,
  "succeeded_count": 5,
  "failed_count": 0,
  "generated_object_ids": ["obj_npc_001", "obj_npc_002", "obj_npc_003"],
  "error_message": null
}
```

### 消费者处理逻辑

- **review-service**：触发内容审核流程（一致性、平衡、安全、重复度）
- **content-service**：准备内容包，等待审核通过后打包
- **ops-service**：更新生成进度，通知审核人员

---

## 5. review.batch.completed（批量审核完成）

### 事件信息

| 属性 | 值 |
|------|-----|
| 主题 | `review.batch.completed` |
| 触发时机 | 批量审核任务完成时 |
| 生产者 | review-service |
| 消费者 | content-service、ops-service |

### Payload 字段

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `review_batch_id` | string | 是 | 审核批次 ID | `rev_20260704_001` |
| `content_package_id` | string | 否 | 关联内容包 ID | `pkg_ch02_waste_20260701_01` |
| `request_id` | string | 否 | 关联生成请求 ID | `gen_20260704_001` |
| `completed_at` | string | 是 | 完成时间 | `2026-07-04T12:00:00Z` |
| `overall_result` | string | 是 | 总体结果：`approved` / `rejected` / `needs_revision` | `approved` |
| `overall_score` | int | 是 | 综合评分（0-100） | `88` |
| `total_checks` | int | 是 | 总检查项数 | `20` |
| `passed_checks` | int | 是 | 通过项数 | `18` |
| `failed_checks` | int | 是 | 失败项数 | `2` |
| `review_types` | list[string] | 是 | 审核类型列表 | `["consistency", "balance", "safety", "duplication"]` |

### Payload 示例

```json
{
  "review_batch_id": "rev_20260704_001",
  "content_package_id": "pkg_ch02_waste_20260701_01",
  "request_id": "gen_20260704_001",
  "completed_at": "2026-07-04T12:00:00Z",
  "overall_result": "approved",
  "overall_score": 88,
  "total_checks": 20,
  "passed_checks": 18,
  "failed_checks": 2,
  "review_types": ["consistency", "balance", "safety", "duplication"]
}
```

### 消费者处理逻辑

- **content-service**：审核通过则触发内容打包，审核不通过则打回
- **ops-service**：更新审核仪表盘，通知运营人员

---

## 6. content.package.released（内容包发布）

### 事件信息

| 属性 | 值 |
|------|-----|
| 主题 | `content.package.released` |
| 触发时机 | 内容包发布（灰度或全量）时 |
| 生产者 | content-service |
| 消费者 | ops-service、world-service、player-service |

### Payload 字段

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `content_package_id` | string | 是 | 内容包 ID | `pkg_ch02_waste_20260701_01` |
| `release_mode` | string | 是 | 发布模式：`gray` / `full` | `gray` |
| `status` | string | 是 | 内容包状态：`gray` / `live` | `gray` |
| `chapter_id` | string | 是 | 章节 ID | `chapter_02` |
| `region_ids` | list[string] | 是 | 影响区域 ID 列表 | `["region_wasteland_01"]` |
| `released_at` | string | 是 | 发布时间 | `2026-07-04T14:00:00Z` |
| `gray_scope` | object | 否 | 灰度范围（灰度发布时） | 见下方 |
| `operator_id` | string | 否 | 操作人 ID | `ops_001` |

### gray_scope 结构

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `region_ids` | list[string] | 灰度区域 | `["region_wasteland_01"]` |
| `player_percent` | int | 灰度玩家百分比 | `10` |
| `player_ids` | list[string] | 指定灰度玩家 | `[]` |

### Payload 示例

```json
{
  "content_package_id": "pkg_ch02_waste_20260701_01",
  "release_mode": "gray",
  "status": "gray",
  "chapter_id": "chapter_02",
  "region_ids": ["region_wasteland_01"],
  "released_at": "2026-07-04T14:00:00Z",
  "gray_scope": {
    "region_ids": ["region_wasteland_01"],
    "player_percent": 10,
    "player_ids": []
  },
  "operator_id": "ops_001"
}
```

### 消费者处理逻辑

- **world-service**：更新区域状态，使新内容对玩家可见
- **player-service**：更新玩家内容可见性
- **ops-service**：记录发布事件，监控灰度指标

---

## 7. content.package.rolled_back（内容包回滚）

### 事件信息

| 属性 | 值 |
|------|-----|
| 主题 | `content.package.rolled_back` |
| 触发时机 | 内容包回滚时 |
| 生产者 | content-service |
| 消费者 | ops-service、world-service、player-service |

### Payload 字段

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `content_package_id` | string | 是 | 内容包 ID | `pkg_ch02_waste_20260701_01` |
| `status` | string | 是 | 内容包状态：`rolled_back` | `rolled_back` |
| `chapter_id` | string | 是 | 章节 ID | `chapter_02` |
| `region_ids` | list[string] | 是 | 影响区域 ID 列表 | `["region_wasteland_01"]` |
| `rolled_back_at` | string | 是 | 回滚时间 | `2026-07-04T16:00:00Z` |
| `reason` | string | 是 | 回滚原因 | "发现严重世界观冲突" |
| `operator_id` | string | 否 | 操作人 ID | `ops_001` |
| `rollback_from_status` | string | 是 | 回滚前状态：`gray` / `live` | `gray` |

### Payload 示例

```json
{
  "content_package_id": "pkg_ch02_waste_20260701_01",
  "status": "rolled_back",
  "chapter_id": "chapter_02",
  "region_ids": ["region_wasteland_01"],
  "rolled_back_at": "2026-07-04T16:00:00Z",
  "reason": "发现严重世界观冲突，NPC 阵营关系与骨架设定不符",
  "operator_id": "ops_001",
  "rollback_from_status": "gray"
}
```

### 消费者处理逻辑

- **world-service**：撤销内容变更，恢复区域状态
- **player-service**：撤销玩家内容可见性
- **ops-service**：记录回滚事件，触发复盘流程

---

## 事件传递规范

### 投递保证

- **至少一次投递（at-least-once）**：事件总线保证事件至少被投递一次
- **消费者必须幂等**：同一事件可能被消费多次，消费者必须保证幂等
- **事件去重**：消费者可使用 `event_id` 进行幂等判断

### 顺序保证

- 同一主题的事件不保证严格顺序
- 如需顺序保证，应在业务层面通过版本号或时间戳判断

### 重试策略

- 消费失败时自动重试，最多 3 次
- 重试间隔采用指数退避
- 重试耗尽后进入死信队列（DLQ）

---

## 与其他文档的关系

- [README.md](./README.md) - 规范总览
- [task-payloads.md](./task-payloads.md) - 异步任务 payload
- [retry-and-dlq.md](./retry-and-dlq.md) - 重试与死信队列
- [trace-and-audit.md](./trace-and-audit.md) - 追踪与审计

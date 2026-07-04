# 异步任务 Payload Schema

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 适用范围

本文档定义 7 个核心异步任务的输入输出 schema，包括字段名称、类型、必填项、说明和示例。所有任务实现必须严格遵循本规范。

## 通用字段

所有任务输入必须包含以下通用字段：

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `trace_id` | string | 否 | 全链路追踪 ID，不传则自动生成 | `trace_abc123def456` |

所有任务输出必须包含以下通用字段：

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `status` | string | 任务执行状态：`started` / `succeeded` / `failed` | `succeeded` |

---

## 1. generate_content_batch（内容生成批量任务）

### 任务信息

| 属性 | 值 |
|------|-----|
| 任务名称 | `workers.tasks.content_generation.generate_content_batch` |
| 队列 | `generation` |
| 最大重试次数 | 3 |
| 退避策略 | 指数退避，基数 2 秒 |
| 调用服务 | generation-service |

### 输入参数

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `template_type` | string | 是 | 模板类型：`npc` / `quest` / `settlement` / `event` | `npc` |
| `count` | int | 否 | 生成数量，默认 1 | `5` |
| `region_id` | string | 否 | 区域 ID | `region_wasteland_01` |
| `chapter_id` | string | 否 | 章节 ID | `chapter_02` |
| `trace_id` | string | 否 | 全链路追踪 ID | `trace_abc123` |

### 输入示例

```json
{
  "template_type": "npc",
  "count": 3,
  "region_id": "region_wasteland_01",
  "chapter_id": "chapter_02",
  "trace_id": "trace_gen_001"
}
```

### 输出结果

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `request_id` | string | 生成请求 ID | `gen_20260704_001` |
| `status` | string | 任务状态：`started` | `started` |

### 输出示例

```json
{
  "request_id": "gen_20260704_001",
  "status": "started"
}
```

### 错误类型

| 错误类型 | 重试策略 | 说明 |
|----------|----------|------|
| 网络超时 | 可重试 | generation-service 连接超时 |
| 5xx 错误 | 可重试 | 服务端内部错误 |
| 4xx 错误 | 不可重试 | 请求参数错误 |
| 模板不存在 | 不可重试 | template_type 无效 |

---

## 2. run_world_consistency_review（世界一致性审核）

### 任务信息

| 属性 | 值 |
|------|-----|
| 任务名称 | `workers.tasks.content_review.run_world_consistency_review` |
| 队列 | `review` |
| 最大重试次数 | 3 |
| 退避策略 | 指数退避，基数 2 秒 |
| 调用服务 | world-service + review-service |

### 输入参数

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `content_package_id` | string | 是 | 内容包 ID | `pkg_ch02_waste_20260701_01` |
| `trace_id` | string | 否 | 全链路追踪 ID | `trace_review_001` |

### 输入示例

```json
{
  "content_package_id": "pkg_ch02_waste_20260701_01",
  "trace_id": "trace_review_001"
}
```

### 输出结果

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `content_package_id` | string | 内容包 ID | `pkg_ch02_waste_20260701_01` |
| `result` | string | 审核结果：`approved` / `rejected` / `needs_revision` | `approved` |
| `score` | int | 一致性评分（0-100） | `90` |
| `issues_count` | int | 发现的问题数量 | `1` |

### 输出示例

```json
{
  "content_package_id": "pkg_ch02_waste_20260701_01",
  "result": "approved",
  "score": 90,
  "issues_count": 1
}
```

### 检查维度

- 阵营关系不与骨架快照冲突
- NPC 身份不越过章节认知边界
- 聚落资源与地貌和势力匹配
- 事件影响不直接改写主线终局

---

## 3. run_balance_review（数值平衡审核）

### 任务信息

| 属性 | 值 |
|------|-----|
| 任务名称 | `workers.tasks.content_review.run_balance_review` |
| 队列 | `review` |
| 最大重试次数 | 3 |
| 退避策略 | 指数退避，基数 2 秒 |
| 调用服务 | review-service |

### 输入参数

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `content_package_id` | string | 是 | 内容包 ID | `pkg_ch02_waste_20260701_01` |
| `trace_id` | string | 否 | 全链路追踪 ID | `trace_balance_001` |

### 输入示例

```json
{
  "content_package_id": "pkg_ch02_waste_20260701_01",
  "trace_id": "trace_balance_001"
}
```

### 输出结果

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `content_package_id` | string | 内容包 ID | `pkg_ch02_waste_20260701_01` |
| `result` | string | 审核结果：`approved` / `rejected` / `needs_revision` | `approved` |
| `score` | int | 平衡评分（0-100） | `100` |
| `issues_count` | int | 发现的问题数量 | `0` |

### 检查维度

- 奖励不突破章节上限
- 敌人强度不超出区域允许区间
- 重复支线累计收益不形成刷取漏洞
- 资源刷新在服务器配置区间内

---

## 4. package_content_batch（内容打包）

### 任务信息

| 属性 | 值 |
|------|-----|
| 任务名称 | `workers.tasks.content_packaging.package_content_batch` |
| 队列 | `packaging` |
| 最大重试次数 | 3 |
| 退避策略 | 指数退避，基数 2 秒 |
| 调用服务 | content-service |

### 输入参数

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `package_id` | string | 是 | 内容包 ID | `pkg_ch02_waste_20260701_01` |
| `object_ids` | list[string] | 是 | 生成对象 ID 列表 | `["obj_001", "obj_002"]` |
| `trace_id` | string | 否 | 全链路追踪 ID | `trace_pkg_001` |

### 输入示例

```json
{
  "package_id": "pkg_ch02_waste_20260701_01",
  "object_ids": ["obj_npc_001", "obj_npc_002", "obj_quest_001"],
  "trace_id": "trace_pkg_001"
}
```

### 输出结果

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `package_id` | string | 内容包 ID | `pkg_ch02_waste_20260701_01` |
| `status` | string | 打包状态：`packaged` | `packaged` |
| `object_count` | int | 打包的对象数量 | `3` |

---

## 5. release_content_package（内容发布）

### 任务信息

| 属性 | 值 |
|------|-----|
| 任务名称 | `workers.tasks.content_release.release_content_package` |
| 队列 | `release` |
| 最大重试次数 | 3 |
| 退避策略 | 指数退避，基数 2 秒 |
| 调用服务 | content-service |

### 输入参数

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `content_package_id` | string | 是 | 内容包 ID | `pkg_ch02_waste_20260701_01` |
| `release_mode` | string | 否 | 发布模式：`gray` / `full`，默认 `gray` | `gray` |
| `gray_scope_jsonb` | object | 否 | 灰度范围配置 | 见下方示例 |
| `trace_id` | string | 否 | 全链路追踪 ID | `trace_release_001` |

### gray_scope_jsonb 结构

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `region_ids` | list[string] | 灰度区域 ID 列表 | `["region_wasteland_01"]` |
| `player_percent` | int | 灰度玩家百分比（1-100） | `10` |
| `player_ids` | list[string] | 指定灰度玩家 ID 列表 | `["player_xxx"]` |

### 输入示例

```json
{
  "content_package_id": "pkg_ch02_waste_20260701_01",
  "release_mode": "gray",
  "gray_scope_jsonb": {
    "region_ids": ["region_wasteland_01"],
    "player_percent": 10
  },
  "trace_id": "trace_release_001"
}
```

### 输出结果

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `content_package_id` | string | 内容包 ID | `pkg_ch02_waste_20260701_01` |
| `release_mode` | string | 发布模式：`gray` / `full` | `gray` |
| `status` | string | 内容包状态：`gray` / `live` | `gray` |

---

## 6. rollback_content_package（内容回滚）

### 任务信息

| 属性 | 值 |
|------|-----|
| 任务名称 | `workers.tasks.content_release.rollback_content_package` |
| 队列 | `release` |
| 最大重试次数 | 3 |
| 退避策略 | 指数退避，基数 2 秒 |
| 调用服务 | content-service |

### 输入参数

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `content_package_id` | string | 是 | 内容包 ID | `pkg_ch02_waste_20260701_01` |
| `reason` | string | 是 | 回滚原因 | "世界观冲突严重" |
| `trace_id` | string | 否 | 全链路追踪 ID | `trace_rollback_001` |

### 输入示例

```json
{
  "content_package_id": "pkg_ch02_waste_20260701_01",
  "reason": "发现严重世界观冲突，NPC 阵营关系与骨架设定不符",
  "trace_id": "trace_rollback_001"
}
```

### 输出结果

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `content_package_id` | string | 内容包 ID | `pkg_ch02_waste_20260701_01` |
| `status` | string | 内容包状态：`rolled_back` | `rolled_back` |
| `reason` | string | 回滚原因 | "世界观冲突严重" |

### 注意事项

- `rolled_back` 是终态，不可再向 `live` / `gray` 迁移
- 回滚后必须记录完整的审计日志
- 同类内容连续回滚超过 2 次时，暂停对应模板使用

---

## 7. daily_gate_scan（每日门禁扫描）

### 任务信息

| 属性 | 值 |
|------|-----|
| 任务名称 | `workers.tasks.gate_scan.daily_gate_scan` |
| 队列 | `gate` |
| 最大重试次数 | 3 |
| 退避策略 | 指数退避，基数 2 秒 |
| 调用服务 | 多服务联合 |

### 输入参数

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `scan_date` | string | 否 | 扫描日期（YYYY-MM-DD），默认当天 | `2026-07-04` |
| `scan_scope` | list[string] | 否 | 扫描范围，默认全部 | `["consistency", "balance"]` |
| `trace_id` | string | 否 | 全链路追踪 ID | `trace_gate_001` |

### 输入示例

```json
{
  "scan_date": "2026-07-04",
  "scan_scope": ["consistency", "balance", "safety", "duplication"],
  "trace_id": "trace_gate_001"
}
```

### 输出结果

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `scan_id` | string | 扫描 ID | `scan_20260704_001` |
| `total_checks` | int | 总检查项数 | `100` |
| `passed_count` | int | 通过项数 | `95` |
| `failed_count` | int | 失败项数 | `5` |

### 扫描维度

- **世界一致性检查**：阵营关系、NPC 身份、聚落资源、事件影响
- **数值平衡检查**：奖励上限、敌人强度、收益漏洞、资源刷新
- **内容安全检查**：敏感词、高风险主题、年龄适配
- **重复度检查**：NPC 相似度、支线复用率、文案重复率

---

## 与其他文档的关系

- [README.md](./README.md) - 规范总览
- [event-schemas.md](./event-schemas.md) - 事件消息格式
- [retry-and-dlq.md](./retry-and-dlq.md) - 重试与死信队列
- [trace-and-audit.md](./trace-and-audit.md) - 追踪与审计

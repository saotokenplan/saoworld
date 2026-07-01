# 51 - AI 内容生成工程约束

> 适用角色：内容开发、AI 开发、后端开发
> 本文件定义 AI 内容生成边界、质量门槛、审核流程、生命周期约束。

---

## AI 职责边界原则

项目核心原则：**结构化约束优先，生成润色其次**。AI 负责可变内容生成，不负责核心规则。

### 禁止 AI 自由生成的内容（红线）

以下内容**绝对禁止**交给 AI 自由生成，只能通过正式版本更新修改：

- 主线终局节点
- 核心经济参数
- 高价值奖励上限
- 战斗底层规则
- 世界观根设定
- 文明来源与历史主线
- 核心阵营定义
- 经济与成长大边界

### 允许 AI 生成的内容（需审核后上线）

以下内容允许 AI 生成，但必须经过审核流程：

- NPC 定义（身份、阵营、个性、语气、位置）
- 聚落定义（类型、风格、居民、资源、势力、冲突）
- 支线任务（触发条件、目标、敌人、奖励）
- 局部世界事件（触发时机、影响范围、参与条件）
- 遭遇配置描述
- 区域叙事文本

---

## 世界骨架强制约束

AI 生成**必须先载入世界骨架快照**，没有骨架快照的生成请求必须直接拒绝。

骨架快照至少包含：
- `world_version`：世界版本
- 当前章节与阶段
- 阵营定义与敌对关系
- 区域目录
- 角色保留名单
- 禁用主题（`forbidden_tags` 不能为空）
- 奖励与强度上限

---

## 生成输入规范

### 输入来源

生成输入只能来自以下五类信息：
1. 投票结果
2. 当前章节与区域上下文
3. 玩家行为摘要
4. 内容模板
5. 规则边界

### 标准输入结构

```json
{
  "request_id": "gen_20260701_001",
  "chapter_id": "chapter_02",
  "region_id": "region_wasteland_01",
  "vote_result": {
    "theme": "荒原废墟",
    "faction_conflict": "机械教团_vs_流亡者",
    "npc_fate": "流亡者首领幸存",
    "event_direction": "资源争夺升级"
  },
  "player_summary": {
    "preferred_activity": ["探索", "支线", "阵营任务"],
    "avg_power_band": "mid",
    "popular_enemy_type": ["机械体", "掠夺者"]
  },
  "constraints": {
    "danger_level": 4,
    "reward_tier_cap": "mid",
    "allowed_tags": ["废墟", "求生", "压抑"],
    "forbidden_tags": ["现代政治映射", "极端暴力", "现实宗教影射"]
  },
  "template_id": "wasteland_branch_pack_v2"
}
```

### 输入校验规则

生成请求提交前必须校验：
- 必须包含 `chapter_id`、`region_id`、`constraints`
- `danger_level` 只能取 `1-5`
- `reward_tier_cap` 必须落在当前章节允许区间
- `forbidden_tags` 不能为空
- `template_id` 必须可追溯到模板仓库版本

---

## 生成输出结构规范

所有 AI 生成的内容对象必须满足对应的结构化字段要求，禁止只生成纯文本。

### NPC 输出必填字段

| 字段 | 说明 |
|------|------|
| `npc_id` | NPC 唯一标识 |
| `name` | 名称 |
| `identity` | 身份 |
| `faction` | 所属阵营 |
| `occupation` | 职业 |
| `personality_tags` | 个性标签，3-5 个 |
| `tone_tags` | 语气标签，1-3 个 |
| `home_region` | 常驻区域 |
| `relation_refs` | 关系引用 |
| `spawn_condition` | 出现条件 |

### 任务输出必填字段

| 字段 | 说明 |
|------|------|
| `quest_id` | 任务 ID |
| `quest_type` | 任务类型（main/side/event） |
| `trigger_condition` | 触发条件 |
| `objectives` | 目标列表 |
| `location` | 地点 |
| `enemies_or_interactables` | 敌人或交互对象 |
| `recommended_power` | 推荐强度 |
| `rewards` | 奖励表 |
| `fail_handling` | 失败处理 |
| `plot_impact_tags` | 剧情影响标签 |

### 聚落输出必填字段

| 字段 | 说明 |
|------|------|
| `settlement_id` | 聚落 ID |
| `settlement_type` | 聚落类型 |
| `style_tags` | 外观风格标签 |
| `population` | 居民构成 |
| `main_resource` | 主资源 |
| `controlling_faction` | 管理势力 |
| `main_conflict` | 主要冲突 |
| `interaction_points` | 交互点列表 |

### 事件输出必填字段

| 字段 | 说明 |
|------|------|
| `event_id` | 事件 ID |
| `trigger_timing` | 触发时机 |
| `impact_scope` | 影响范围 |
| `participation_condition` | 参与条件 |
| `success_condition` | 成功条件 |
| `end_condition` | 结束条件 |
| `region_state_impact` | 对区域状态的影响 |

---

## 模板机制

### 模板层级

- **世界模板**：约束章节、阵营、区域类型和禁用主题
- **区域模板**：约束地貌、资源、敌人池和聚落风格
- **任务模板**：约束任务骨架、目标类型和奖励槽位
- **文案模板**：约束语气、词汇和叙事风格

### 模板使用规则

- **所有生成都必须先匹配模板，再做填充和润色**，禁止无模板自由生成
- 模板版本（`tpl_<domain>_v<major>.<minor>`）必须写入最终审计记录
- 模板升级后不能自动覆盖已上线内容，必须走内容包新版本发布

---

## 质量评分与门槛

每个生成对象在进入审核前必须先获得 AI 自评质量分。

### 质量分维度

| 维度 | 说明 | 分值范围 |
|------|------|----------|
| 结构完整度 | 必填字段是否齐全 | 0.0-1.0 |
| 世界一致性 | 是否与阵营、区域、章节冲突 | 0.0-1.0 |
| 数值合理性 | 强度、奖励、资源是否在边界内 | 0.0-1.0 |
| 文本质量 | 是否通顺、是否过度重复 | 0.0-1.0 |
| 差异性 | 与历史内容重复度是否过高 | 0.0-1.0 |

质量分存储在 `generated_objects.quality_score REAL CHECK (quality_score >= 0 AND quality_score <= 1)`。

### 质量门槛

- 总分 **< 0.75**（百分制 75 分）：**不得进入打包**，直接打回修改或废弃
- 总分 **0.75 - 0.85**（75-85 分临界区间）：**必须触发人工复核**
- 总分 **≥ 0.85**：可进入自动审核流程

### 重复度阈值

- 同章节 NPC 设定相似度 ≤ 0.8
- 同区域支线骨架复用比例 ≤ 0.6
- 文案段落重复率 ≤ 0.3

---

## 审核规则

### 世界一致性审核

- 阵营关系不能与骨架快照冲突
- NPC 身份不能越过章节认知边界
- 聚落资源必须与地貌和势力匹配
- 事件影响不能直接改写主线终局

### 数值审核

- 奖励不得突破章节上限
- 敌人强度不得超出区域允许区间
- 重复支线累计收益不得形成刷取漏洞
- 资源刷新必须落在服务器配置区间

### 内容安全审核

- 命中敏感词直接驳回
- 涉及高风险主题进入人工复核
- 不符合目标年龄层表达直接驳回
- `forbidden_tags` 中标记的主题绝对禁止出现

### 重复度审核

按上述重复度阈值执行检查。

---

## 人工复核触发条件

以下任一情况必须触发人工复核：

1. 质量总分处于 0.75-0.85 临界区间
2. 命中高风险主题词
3. 新模板首次上线
4. 奖励或剧情影响接近边界阈值
5. 生成对象关联核心阵营或关键角色

---

## 内容生命周期与状态机

内容对象从生成到上线跨两张表管理：

```
（generated_objects 表）              （content_packages 表）
pending_review → approved → 打包 → packaged → gray → live → archived
                       ↓             ↓
                    rejected      rolled_back
                ↓
            needs_revision
```

### 状态映射

| 概念状态 | 数据库表 | 字段值 |
|---|---|---|
| 模型刚生成，待校验 | `generated_objects` | `pending_review` |
| 自动审核通过 | `generated_objects` | `approved` |
| 审核不通过 | `generated_objects` | `rejected`（终态） |
| 需要修改后重审 | `generated_objects` | `needs_revision` |
| 已打入内容包 | `content_packages` | `packaged` |
| 灰度上线 | `content_packages` | `gray` |
| 正式生效 | `content_packages` | `live` |
| 下线归档 | `content_packages` | `archived`（终态） |
| 已回滚 | `content_packages` | `rolled_back`（终态） |

状态迁移约束详见 [11-database.md](./11-database.md) 中的状态机章节。

---

## 可追溯性要求

每个上线内容必须能完整追溯到：
1. 投票周期（`vote_cycle_id`）
2. 生成请求（`generation_request_id`）
3. 使用的模板版本（`template_id`）
4. 生成输入快照（`input_payload_jsonb`）
5. 生成输出快照（`object_payload_jsonb`）
6. 审核记录（`review_records`）
7. 发布/回滚记录（`release_records`/`rollback_records`）
8. 内容包版本（`content_package_id`）

---

## 相关规则

- 数据库状态机设计 → [11-database.md](./11-database.md)
- 发布与回滚 → [42-release-rollback.md](./42-release-rollback.md)
- 内容测试 → [41-testing.md](./41-testing.md)

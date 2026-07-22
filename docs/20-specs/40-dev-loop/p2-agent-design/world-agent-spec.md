# World Agent 技术规范

> 文档状态：active
> 适用阶段：P2（多代理协同期）
> 维护要求：持续维护

## 职责定义

World Agent 负责生成 NPC、区域、事件、任务和世界描述配置。它将投票结果和世界规则转化为结构化的游戏内容。

## 输入

| 输入来源 | 格式 | 说明 |
|---------|------|------|
| 世界规则 | yaml/json | 世界观和约束 |
| 投票结果 | JSON | 玩家投票数据 |
| 模板 | yaml/json | NPC、任务、区域模板 |
| 骨架快照 | JSON | 当前世界骨架 |
| design-note.md | markdown | 技术设计文档（内容部分） |

### 输入数据结构

**世界规则输入**：
```json
{
  "world_version": "1.0",
  "chapter_id": "chapter_01",
  "regions": [
    {"region_id": "region_core", "name": "铁卫城周边", "status": "active"},
    {"region_id": "region_expansion", "name": "灰谷废墟", "status": "active"}
  ],
  "factions": [
    {"faction_id": "faction_iron", "name": "铁卫联盟", "alignment": "lawful"},
    {"faction_id": "faction_free", "name": "自由领地", "alignment": "neutral"}
  ],
  "forbidden_tags": ["adult", "violence", "political"],
  "reserved_characters": ["主角", "国王"],
  "reward_limits": {"gold": {"min": 10, "max": 1000}, "exp": {"min": 50, "max": 5000}}
}
```

**投票结果输入**：
```json
{
  "vote_cycle_id": "vc_20260701",
  "winning_candidate_id": "candidate_003",
  "winning_direction": "新增迷雾森林区域",
  "voter_count": 500,
  "winning_percentage": 40
}
```

**模板输入**：
```json
{
  "template_id": "tpl_npc_blacksmith",
  "type": "npc",
  "schema_version": 2,
  "fields": {
    "name": "string",
    "title": "string",
    "faction_id": "string",
    "personality": ["friendly", "neutral", "grumpy"],
    "skills": ["crafting", "trading"],
    "dialog_templates": ["greeting", "quest_offer", "farewell"]
  }
}
```

**骨架快照输入**：
```json
{
  "skeleton_id": "skel_20260701",
  "world_version": "1.0",
  "chapter_id": "chapter_01",
  "regions": [...],
  "factions": [...],
  "forbidden_tags": [...],
  "timestamp": "2026-07-01T00:00:00Z",
  "status": "active"
}
```

## 输出

| 输出产物 | 格式 | 说明 |
|---------|------|------|
| NPC 配置 | JSON | NPC 定义数据 |
| 任务配置 | JSON | 任务定义数据 |
| 区域配置 | JSON | 区域定义数据 |
| 事件配置 | JSON | 事件定义数据 |
| 内容包 | JSON | 打包的内容配置 |
| 审核请求 | JSON | 提交给 review-service 的审核请求 |

### 输出数据结构

**NPC 配置输出**：
```json
{
  "npc_id": "npc_fog_forest_001",
  "name": "艾琳·迷雾",
  "title": "森林守护者",
  "faction_id": "faction_free",
  "region_id": "region_fog_forest",
  "personality": "mysterious",
  "skills": ["nature", "healing"],
  "dialogs": {
    "greeting": "欢迎来到迷雾森林，冒险者...",
    "quest_offer": "森林深处出现了异常，你愿意帮忙调查吗？",
    "farewell": "小心前行，迷雾中藏着许多秘密..."
  },
  "schema_version": 1,
  "generated_at": "2026-07-07T14:00:00Z"
}
```

**任务配置输出**：
```json
{
  "quest_id": "quest_fog_forest_investigation",
  "name": "迷雾调查",
  "type": "main",
  "region_id": "region_fog_forest",
  "npc_id": "npc_fog_forest_001",
  "objectives": [
    {"type": "explore", "target": "迷雾森林深处"},
    {"type": "defeat", "target": "森林守护者", "count": 3}
  ],
  "rewards": {"gold": 500, "exp": 2000, "items": ["forest_key"]},
  "prerequisites": [],
  "schema_version": 1,
  "generated_at": "2026-07-07T14:00:00Z"
}
```

**区域配置输出**：
```json
{
  "region_id": "region_fog_forest",
  "name": "迷雾森林",
  "description": "一片被永恒迷雾笼罩的古老森林，传说中隐藏着失落的宝藏...",
  "status": "locked",
  "level_range": {"min": 5, "max": 10},
  "region_scope": {
    "biome": "forest",
    "climate": "misty",
    "resources": ["wood", "herbs", "rare_mushrooms"],
    "dangers": ["wild_beasts", "traps", "fog_walkers"]
  },
  "schema_version": 1,
  "generated_at": "2026-07-07T14:00:00Z"
}
```

**内容包输出**：
```json
{
  "content_package_id": "pkg_fog_forest_20260707_01",
  "version": "1.0",
  "chapter_id": "chapter_01",
  "region_id": "region_fog_forest",
  "type": "region",
  "content": {
    "npcs": [...],
    "quests": [...],
    "events": [...],
    "description": "迷雾森林区域内容包"
  },
  "schema_version": 1,
  "generated_at": "2026-07-07T14:00:00Z"
}
```

**审核请求输出**：
```json
{
  "request_id": "gen_20260707_001",
  "content_package_id": "pkg_fog_forest_20260707_01",
  "type": "content_review",
  "checks": ["world_consistency", "reward_boundary", "content_safety", "duplication"],
  "priority": "high"
}
```

## 核心流程

### 步骤 1：读取输入数据
- 读取世界规则和约束
- 获取最新投票结果
- 加载内容模板
- 获取当前世界骨架快照

### 步骤 2：校验输入
- 校验骨架快照存在且有效
- 校验 forbidden_tags 非空
- 校验 chapter_id 和 region_id 有效
- 校验模板版本兼容性

### 步骤 3：匹配模板
- 根据投票结果选择合适的内容模板
- 填充模板参数
- 生成结构化中间稿

### 步骤 4：生成内容
- AI 生成 NPC 设定和对话
- AI 生成任务目标和描述
- AI 生成区域描述和事件
- 确保内容符合世界观约束

### 步骤 5：应用规则约束
- 检查世界观一致性（阵营关系、认知边界）
- 检查数值平衡（奖励不突破章节上限）
- 检查内容安全（敏感词检测）
- 检查重复度（NPC 相似度、支线复用比例）

### 步骤 6：生成文本润色
- 生成 NPC 对话和描述
- 生成任务文本和目标描述
- 生成区域背景故事
- 生成事件描述

### 步骤 7：打包内容
- 将生成的内容组织成内容包
- 添加版本元数据
- 添加 schema_version
- 生成审核请求

### 步骤 8：提交审核
- 将审核请求提交给 review-service
- 等待审核结果

### 步骤 9：处理审核结果
- 如果通过：通知 Build Agent 打包发布
- 如果拒绝：分析原因，重新生成
- 如果需要修改：根据反馈调整内容

## 关键能力

- 内容生成和模板匹配
- 世界观一致性检查
- 对话和描述生成
- 内容包打包
- 规则约束应用

## 协作机制

### 与 System Designer Agent
- **输入**：design-note.md（内容部分）、规则约束
- **输出**：内容生成反馈、规则冲突
- **触发条件**：内容设计完成后

### 与 Gameplay Agent
- **输出**：区域配置、NPC 配置、任务配置
- **输入**：内容反馈、配置问题
- **触发条件**：内容配置更新后

### 与 Generation Service
- **输入**：生成结果、状态更新
- **输出**：生成请求、模板参数
- **触发条件**：需要 AI 生成内容时

### 与 Review Service
- **输出**：审核请求、内容包
- **输入**：审核结果、修改建议
- **触发条件**：内容生成完成后

### 与 Build Agent
- **输出**：审核通过的内容包
- **输入**：打包结果
- **触发条件**：审核通过后

## 错误处理和异常情况

### 骨架快照缺失
- **检测**：当前没有活跃的世界骨架快照
- **处理**：等待骨架快照创建或使用默认值
- **通知**：记录警告日志，通知 Ops Agent

### 模板不匹配
- **检测**：找不到合适的内容模板
- **处理**：使用通用模板或创建新模板
- **通知**：记录模板缺失日志

### 内容违规
- **检测**：内容包含 forbidden_tags 或敏感词
- **处理**：重新生成内容，避免违规元素
- **通知**：记录内容违规日志

### 审核失败
- **检测**：内容未通过审核
- **处理**：分析失败原因，修改内容后重新提交
- **通知**：记录审核失败日志，包含失败原因

### 重复度过高
- **检测**：生成的内容与现有内容相似度超过阈值
- **处理**：重新生成，增加多样性
- **通知**：记录重复度警告日志

## 约束条件

- 内容必须符合世界观约束
- 奖励必须符合数值边界
- 必须通过内容安全检查
- 必须通过重复度检查
- NPC 相似度阈值 ≤ 0.8
- 支线骨架复用比例 ≤ 0.6
- 文案段落重复率 ≤ 0.3
- 内容包必须带 schema_version 字段

## 验收标准

- 世界一致性检查通过
- 数值边界检查通过
- 内容安全检查通过
- 重复度检查通过
- 内容包结构完整，包含所有必要字段
- schema_version 字段正确设置
- 审核请求格式正确，可被 review-service 处理
- 输出格式符合规范，可被其他代理直接使用
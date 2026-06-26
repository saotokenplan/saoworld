# world-content-generator

## 目标

根据投票结果、章节状态、区域上下文和模板边界，生成结构化的 NPC、任务、聚落和事件草案。核心要求是“结构化、可审核、可追溯”，不是追求文学化自由发挥。

## 适用场景

- 新投票周期结束后生成候选内容
- 新区域扩展包的支线、NPC 和聚落草案生成
- 局部世界事件和遭遇内容生成

## 规范来源

- 主要来源：
  - `docs/20-specs/content-generation-spec.md`
  - `docs/20-specs/product-spec.md`
- 次要来源：
  - `docs/20-specs/backend-data-spec.md`
- 说明：
  - 生成对象字段、模板机制和生命周期以 `content-generation-spec.md` 为准
  - 世界骨架、可变范围和不可突破边界以 `product-spec.md` 为准
  - 请求追踪、对象存储和状态字段参考 `backend-data-spec.md`

## 输入

- 世界骨架快照
- 投票结果
- 区域上下文
- 玩家行为摘要
- 模板版本
- 风险与边界约束

## 输出

- `npc.json`
- `quests.json`
- `settlements.json`
- `events.json`
- `generation-summary.md`

## 生成原则

- 先套模板，再填参数，最后做生成润色
- 先保证结构可用，再追求文案质量
- 生成结果必须能映射到内容生命周期状态
- 所有对象必须能追溯到 `request_id` 和 `template_id`

## 输出对象要求

### NPC

必须包含：

- `npc_id`
- 姓名
- 身份
- 阵营
- 职业
- 个性标签
- 语气标签
- 常驻区域
- 关系引用

### Quest

必须包含：

- `quest_id`
- 触发条件
- 目标列表
- 地点
- 交互对象或敌人
- 推荐强度
- 奖励表
- 失败处理

### Settlement

必须包含：

- `settlement_id`
- 聚落类型
- 外观风格
- 居民构成
- 主资源
- 管理势力
- 主要冲突

### Event

必须包含：

- `event_id`
- 触发时机
- 参与条件
- 成功条件
- 结束条件
- 影响范围

## 硬约束

- 不允许生成主线终局节点
- 不允许生成核心经济参数
- 不允许突破章节奖励上限
- 不允许改写世界骨架
- 没有世界骨架快照就拒绝生成

## 自检要求

生成后必须先自检：

- 字段完整度
- 与章节和阵营是否冲突
- 奖励和强度是否越界
- 是否出现高重复表达

## 不该做的事

- 不直接宣布内容可上线
- 不把玩家自由文本直接当提示词主输入
- 不省略 `template_id`、`request_id`、`schema_version`

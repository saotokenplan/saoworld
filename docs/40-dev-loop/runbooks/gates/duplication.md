# 重复度检查 (G-CONTENT-004)

## 门禁概述

| 项目 | 说明 |
|------|------|
| 门禁名称 | 重复度检查 |
| 门禁 ID | G-CONTENT-004 |
| 类型 | content |
| 触发条件 | 内容 PR 提交时，路径匹配 `game/data/**` 或 `tools/content_check/**` |
| 覆盖风险类型 | duplication, regression |

本门禁验证 AI 生成内容与已有内容的重复程度，确保 NPC 设定、支线任务骨架、文案描述具有足够的多样性，避免玩家体验同质化。

---

## 常见失败原因

按出现频率从高到低排序：

### 1. NPC 设定相似

同章节内 NPC 设定相似度过高（超过 0.8），包括背景故事、性格特征、说话方式、外观描述等维度高度雷同，玩家难以区分不同角色。

### 2. 支线骨架复用过高

同区域内支线任务骨架复用比例过高（超过 0.6），任务结构、目标类型、流程步骤过于相似，玩家产生"换皮任务"的感受。

### 3. 文案重复

文案段落重复率过高（超过 0.3），大量句式、词汇、描述方式重复出现，影响阅读体验和内容新鲜感。

---

## 解决方案

### 1. NPC 设定相似

```bash
# 第一步：查看重复度详情，定位相似的 NPC
python tools/content_check/duplication.py --input <content_dir> --existing <existing_dir> --verbose

# 第二步：分析相似维度
# 查看是背景相似、性格相似、还是说话方式相似
# 找出相似度最高的几个维度

# 第三步：增加差异化
# - 背景：调整出身、经历、阵营关系
# - 性格：调整核心性格特质、行为模式
# - 说话方式：调整语气、口头禅、用词习惯
# - 外观：调整外貌特征、服饰风格
```

### 2. 支线骨架复用过高

```bash
# 第一步：查看支线骨架复用详情
python tools/content_check/duplication.py --input <content_dir> --existing <existing_dir> --verbose

# 第二步：分析任务结构相似度
# 查看是目标类型相似、流程步骤相似、还是反转点相似

# 第三步：调整任务结构
# - 改变任务目标：收集 → 护送 → 调查 → 解谜
# - 调整流程顺序：线性流程 → 分支选择 → 多结局
# - 增加独特机制：限时、潜行、QTE、多阶段 Boss
# - 反转剧情：好人变坏人、目标是陷阱、NPC 另有目的
```

### 3. 文案重复

```bash
# 第一步：查看文案重复详情
python tools/content_check/duplication.py --input <content_dir> --existing <existing_dir> --verbose

# 第二步：定位重复段落
# 找出重复率最高的段落和句子

# 第三步：改写文案
# - 改变叙事视角：第三人称 → 第一人称 → 对话体
# - 调整句式结构：长句拆短、短句拉长、调整语序
# - 替换词汇：使用不同的形容词、动词、比喻
# - 增加细节：补充感官描述、环境氛围、人物心理
```

---

## 手动执行

```bash
# 基本执行方式
python tools/content_check/duplication.py --input <content_dir> --existing <existing_dir>

# 查看详细输出
python tools/content_check/duplication.py --input <content_dir> --existing <existing_dir> --verbose

# 仅检查 NPC 重复度
python tools/content_check/duplication.py --input <content_dir> --existing <existing_dir> --check npc

# 仅检查任务骨架重复度
python tools/content_check/duplication.py --input <content_dir> --existing <existing_dir> --check quest

# 生成 JSON 格式报告
python tools/content_check/duplication.py --input <content_dir> --existing <existing_dir> --report report.json

# 调整相似度阈值（默认 NPC 0.8，任务 0.6，文案 0.3）
python tools/content_check/duplication.py --input <content_dir> --existing <existing_dir> --threshold npc=0.75
```

---

## 升级路径

| 级别 | 处理方式 | 联系人 |
|------|----------|--------|
| 一级 | 按上述方案自行修改内容 | 内容生成 Agent |
| 二级 | 修改后仍不通过，怀疑相似度算法有误 | Rule Engine 负责人 |
| 三级 | 阈值设置不合理，需要调整 | 内容策划 |
| 四级 | 内容池过小，不可避免重复 | 项目主策 |

**升级流程：**
1. 先尝试自行修改内容，增加多样性，重新跑门禁
2. 连续 2 次不通过且怀疑算法问题，联系 Rule Engine 负责人确认相似度计算逻辑
3. 确认是阈值设置不合理，提交内容策划评审调整阈值
4. 内容池过小导致不可避免重复，上报项目主策决策是否扩充内容或放宽限制

# 世界一致性检查 (G-CONTENT-001)

## 门禁概述

| 项目 | 说明 |
|------|------|
| 门禁名称 | 世界一致性检查 |
| 门禁 ID | G-CONTENT-001 |
| 类型 | content |
| 触发条件 | 内容 PR 提交时，路径匹配 `game/data/**` 或 `tools/content_check/**` |
| 覆盖风险类型 | world-consistency, regression |

本门禁验证 AI 生成的内容是否与世界观骨架快照保持一致，确保阵营关系、NPC 身份认知、聚落资源配置以及主线走向不发生冲突。

---

## 常见失败原因

按出现频率从高到低排序：

### 1. 阵营关系冲突

生成内容中 NPC 或聚落所属阵营与世界观设定的阵营关系矩阵不一致，出现敌对阵营友好互动或盟友阵营相互攻击的矛盾描述。

### 2. NPC 身份越界

NPC 掌握了超出其当前章节认知边界的信息，例如第一章的 NPC 谈论第二章才开放的区域或事件，或低阶角色知晓高层机密。

### 3. 资源不匹配

聚落或区域的资源配置与地貌和势力设定不匹配，例如荒漠区域出现大量水资源，或农耕部落拥有高级锻造设施。

### 4. 主线冲突

生成的支线或事件直接改写主线剧情走向，或与已确定的主线终局设定产生矛盾，导致世界观根基被动摇。

---

## 解决方案

### 1. 阵营关系冲突

```bash
# 第一步：查看详细错误报告，定位具体冲突的 NPC 或聚落
python tools/content_check/world_consistency.py --input <content_dir> --rules game/data/ --verbose

# 第二步：检查阵营关系矩阵
# 打开 game/data/factions/faction_relations.json
# 确认各阵营之间的友好/中立/敌对关系

# 第三步：修正生成内容中的阵营描述
# 将冲突的 NPC 所属阵营或互动描述调整为符合关系矩阵
```

### 2. NPC 身份越界

```bash
# 第一步：查看越界详情
python tools/content_check/world_consistency.py --input <content_dir> --rules game/data/ --verbose

# 第二步：检查章节认知边界
# 打开 game/data/chapters/chapter_xx.json
# 查看该章节允许 NPC 知晓的区域、事件、势力范围

# 第三步：调整 NPC 对话和背景描述
# 移除超出认知边界的信息，替换为符合其身份层级的表述
```

### 3. 资源不匹配

```bash
# 第一步：查看资源不匹配详情
python tools/content_check/world_consistency.py --input <content_dir> --rules game/data/ --verbose

# 第二步：检查区域地貌与势力设定
# 打开 game/data/regions/region_xxx.json
# 查看该区域的地貌类型、资源禀赋、势力技术水平

# 第三步：调整聚落资源配置
# 将不匹配的资源替换为符合区域设定的类型，或补充合理的获取途径说明
```

### 4. 主线冲突

```bash
# 第一步：查看主线冲突详情
python tools/content_check/world_consistency.py --input <content_dir> --rules game/data/ --verbose

# 第二步：核对主线骨架
# 打开 game/data/mainline/story_outline.json
# 确认主线关键节点、终局设定、不可变更的核心剧情

# 第三步：修正冲突内容
# 将冲突的支线或事件调整为主线的侧面补充，避免直接影响主线走向
# 如冲突严重，直接废弃该内容并重新生成
```

---

## 手动执行

```bash
# 基本执行方式
python tools/content_check/world_consistency.py --input <content_dir> --rules game/data/

# 查看详细输出
python tools/content_check/world_consistency.py --input <content_dir> --rules game/data/ --verbose

# 仅检查特定类型的内容（如 NPC）
python tools/content_check/world_consistency.py --input <content_dir>/npcs --rules game/data/ --type npc

# 生成 JSON 格式报告
python tools/content_check/world_consistency.py --input <content_dir> --rules game/data/ --report report.json
```

---

## 升级路径

| 级别 | 处理方式 | 联系人 |
|------|----------|--------|
| 一级 | 按上述解决方案自行修正内容数据 | 内容生成 Agent |
| 二级 | 修正后仍不通过，怀疑检查规则有误 | Rule Engine 负责人 |
| 三级 | 规则本身与世界观设定有歧义 | 世界观策划 |
| 四级 | 涉及主线核心设定变更 | 项目主策 |

**升级流程：**
1. 先尝试自行修正内容，重新跑门禁
2. 连续 2 次不通过且怀疑规则问题，联系 Rule Engine 负责人确认规则
3. 确认是世界观设定歧义，提交世界观策划评审
4. 涉及主线核心设定，上报项目主策决策

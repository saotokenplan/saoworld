# 数值平衡检查 (G-CONTENT-002)

## 门禁概述

| 项目 | 说明 |
|------|------|
| 门禁名称 | 数值平衡检查 |
| 门禁 ID | G-CONTENT-002 |
| 类型 | content |
| 触发条件 | 内容 PR 提交时，路径匹配 `game/data/**` 或 `tools/content_check/**` |
| 覆盖风险类型 | reward-boundary, data-integrity |

本门禁验证 AI 生成内容中的数值是否在合理边界内，包括任务奖励、敌人强度、资源刷新频率等，防止破坏游戏经济平衡和玩家体验。

---

## 常见失败原因

按出现频率从高到低排序：

### 1. 奖励超上限

任务或事件奖励超出当前章节允许的上限，包括经验值、金币、道具等奖励数值过高，可能导致玩家快速毕业，缩短游戏生命周期。

### 2. 敌人强度超标

敌人等级、攻击力、生命值等属性超出当前区域允许的难度区间，导致玩家无法正常推进，或越级击杀收益异常。

### 3. 刷取漏洞

重复可完成的支线任务或事件累计收益过高，形成可无限刷取的经济漏洞，破坏游戏经济系统平衡。

### 4. 资源刷新异常

资源点刷新频率或数量不在服务器配置区间内，过快或过慢都会影响游戏节奏和经济平衡。

---

## 解决方案

### 1. 奖励超上限

```bash
# 第一步：查看详细错误报告，定位超标奖励的任务和具体数值
python tools/content_check/reward_boundary.py --input <content_dir> --budget game/data/config/ --verbose

# 第二步：检查章节数值配置
# 打开 game/data/config/chapter_budgets.json
# 确认当前章节的奖励上限（经验、金币、稀有度等）

# 第三步：调低任务奖励数值
# 将超出部分调整到章节上限以内
# 如确有必要增加奖励，考虑拆分到多个任务或提升章节
```

### 2. 敌人强度超标

```bash
# 第一步：查看敌人强度超标详情
python tools/content_check/reward_boundary.py --input <content_dir> --budget game/data/config/ --verbose

# 第二步：检查区域难度配置
# 打开 game/data/regions/region_xxx.json
# 查看该区域允许的敌人等级范围、属性区间

# 第三步：调整敌人属性
# 将敌人的等级、攻击、防御等属性降到区域允许范围内
# 或调整该敌人出现的区域到难度匹配的地方
```

### 3. 刷取漏洞

```bash
# 第一步：查看刷取漏洞详情
python tools/content_check/reward_boundary.py --input <content_dir> --budget game/data/config/ --verbose

# 第二步：分析重复收益计算
# 检查任务是否可重复完成、冷却时间、单位时间收益

# 第三步：修复漏洞
# 方案A：增加任务冷却时间
# 方案B：降低单次奖励，提升首次奖励
# 方案C：改为一次性任务，不可重复完成
```

### 4. 资源刷新异常

```bash
# 第一步：查看资源刷新异常详情
python tools/content_check/reward_boundary.py --input <content_dir> --budget game/data/config/ --verbose

# 第二步：检查服务器配置区间
# 打开 game/data/config/resource_refresh.json
# 确认各类资源的刷新频率和数量上下限

# 第三步：调整刷新参数
# 将刷新频率和数量调整到配置区间内
# 如确有特殊需求，提交策划评审后调整配置上限
```

---

## 手动执行

```bash
# 基本执行方式
python tools/content_check/reward_boundary.py --input <content_dir> --budget game/data/config/

# 查看详细输出
python tools/content_check/reward_boundary.py --input <content_dir> --budget game/data/config/ --verbose

# 仅检查奖励项
python tools/content_check/reward_boundary.py --input <content_dir> --budget game/data/config/ --check reward

# 仅检查敌人强度
python tools/content_check/reward_boundary.py --input <content_dir> --budget game/data/config/ --check enemy

# 生成 JSON 格式报告
python tools/content_check/reward_boundary.py --input <content_dir> --budget game/data/config/ --report report.json
```

---

## 升级路径

| 级别 | 处理方式 | 联系人 |
|------|----------|--------|
| 一级 | 按上述解决方案自行调整数值 | 内容生成 Agent |
| 二级 | 调整后仍不通过，怀疑检查计算有误 | Rule Engine 负责人 |
| 三级 | 配置上限不合理，需要调整预算 | 数值策划 |
| 四级 | 涉及核心经济系统调整 | 项目主策 |

**升级流程：**
1. 先尝试自行调整数值，重新跑门禁
2. 连续 2 次不通过且怀疑规则问题，联系 Rule Engine 负责人确认计算逻辑
3. 确认是配置上限不合理，提交数值策划评审调整预算
4. 涉及核心经济系统变更，上报项目主策决策

# 内容安全检查 (G-CONTENT-003)

## 门禁概述

| 项目 | 说明 |
|------|------|
| 门禁名称 | 内容安全检查 |
| 门禁 ID | G-CONTENT-003 |
| 类型 | content |
| 触发条件 | 内容 PR 提交时，路径匹配 `game/data/**` 或 `tools/content_check/**` |
| 覆盖风险类型 | security, content-safety |

本门禁验证 AI 生成内容是否符合安全规范，包括敏感词检测、高风险主题识别、目标年龄层适配，防止不适宜内容进入游戏。

---

## 常见失败原因

按出现频率从高到低排序：

### 1. 敏感词命中

内容中包含明确的敏感词（如政治敏感、色情、暴力、违禁品等），属于严重违规，直接驳回，不进入人工复核。

### 2. 高风险主题

内容涉及高风险主题（如自杀、自残、毒品、极端主义等），虽未命中精确敏感词，但主题本身具有较高风险，需进入人工复核。

### 3. 年龄层不适配

内容不符合游戏目标年龄层的内容分级标准，包含超出适龄范围的暴力、血腥、性暗示等描述，需要调整或移除。

---

## 解决方案

### 1. 敏感词命中

```bash
# 第一步：查看敏感词命中详情
python tools/content_check/content_safety.py --input <content_dir> --verbose

# 第二步：定位命中的具体内容
# 在输出中查找 SENSITIVE_WORD 标记，记录命中的词和位置

# 第三步：修改内容
# - 使用同义词替换
# - 重写相关段落，移除敏感表述
# - 注意不要使用拼音、缩写等规避手段
```

### 2. 高风险主题

```bash
# 第一步：查看高风险主题详情
python tools/content_check/content_safety.py --input <content_dir> --verbose

# 第二步：评估风险等级
# 查看风险分类：high / medium / low
# high 级：必须修改或移除
# medium 级：可提交人工复核

# 第三步：处理方式
# 方案A：修改内容，淡化或移除高风险主题
# 方案B：提交人工复核，由审核团队判断是否放行
```

### 3. 年龄层不适配

```bash
# 第一步：查看年龄层不匹配详情
python tools/content_check/content_safety.py --input <content_dir> --verbose

# 第二步：确认目标年龄层
# 打开 game/data/config/game_config.json
# 查看 target_age_rating 字段（如 PEGI 12 / ESRB T）

# 第三步：调整内容
# - 暴力描述：降低血腥程度，改为侧面描写
# - 性暗示：移除或替换为适龄表述
# - 恐怖元素：降低惊吓程度，减少突然惊吓
```

---

## 手动执行

```bash
# 基本执行方式
python tools/content_check/content_safety.py --input <content_dir>

# 查看详细输出
python tools/content_check/content_safety.py --input <content_dir> --verbose

# 指定目标年龄层检查
python tools/content_check/content_safety.py --input <content_dir> --age-rating 12

# 仅检查敏感词
python tools/content_check/content_safety.py --input <content_dir> --check sensitive

# 生成 JSON 格式报告
python tools/content_check/content_safety.py --input <content_dir> --report report.json
```

---

## 升级路径

| 级别 | 处理方式 | 联系人 |
|------|----------|--------|
| 一级 | 按上述方案自行修改内容 | 内容生成 Agent |
| 二级 | 不确定是否违规，提交人工复核 | 内容审核团队 |
| 三级 | 审核团队有争议，需策划判断 | 世界观策划 |
| 四级 | 涉及重大安全合规风险 | 项目负责人 + 法务 |

**升级流程：**
1. 先尝试自行修改内容，重新跑门禁
2. 连续 2 次不通过或无法判断，提交人工复核
3. 审核团队内部有争议，提交世界观策划从内容角度判断
4. 涉及重大合规风险，上报项目负责人和法务团队决策

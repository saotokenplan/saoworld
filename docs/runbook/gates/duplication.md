# Runbook: Duplication Check (G-CONTENT-004)

> gate_id: G-CONTENT-004
> gate_name: Duplication Check
> gate_type: content
> owner: Rule Engine

## 门禁概述

Duplication Check 是重复度检查门禁，验证内容是否与已有内容重复度过高。

**触发条件**：
- 路径：`game/data/**`, `tools/content_check/**`
- 触发：`on_content_pr`

**执行命令**：
```bash
python tools/content_check/duplication.py --input <content_dir> --existing <existing_dir>
```

**预期耗时**：90 秒

## 常见失败原因

### 1. NPC 设定相似度超限

**现象**：
- 同章节 NPC 设定相似度超过 0.8
- NPC 描述过于相似

**解决方案**：
```bash
# 查看详细错误信息
python tools/content_check/duplication.py --input game/data/ --existing game/data/ --verbose

# 检查 NPC 数据
# 文件：game/data/npcs/npc_list.json

# 修改 NPC 设定，增加差异化
```

### 2. 支线骨架复用比例超限

**现象**：
- 同区域支线骨架复用比例超过 0.6
- 任务结构过于相似

**解决方案**：
```bash
# 查看详细错误信息
python tools/content_check/duplication.py --input game/data/ --existing game/data/ --verbose

# 检查任务数据
# 文件：game/data/quests/quest_list.json

# 修改任务结构，增加多样性
```

### 3. 文案段落重复率超限

**现象**：
- 文案段落重复率超过 0.3
- 文本内容大量重复

**解决方案**：
```bash
# 查看详细错误信息
python tools/content_check/duplication.py --input game/data/ --existing game/data/ --verbose

# 修改文案内容，减少重复
```

## 手动执行

```bash
# 检查整个 game/data 目录
python tools/content_check/duplication.py --input game/data/ --existing game/data/

# 查看详细输出
python tools/content_check/duplication.py --input game/data/ --existing game/data/ --verbose

# 生成重复度报告
python tools/content_check/duplication.py --input game/data/ --existing game/data/ --report
```

## 升级路径

| 级别 | 处理方式 |
|------|----------|
| NPC 相似度 | 修改 NPC 设定增加差异化 |
| 支线复用 | 修改任务结构增加多样性 |
| 文案重复 | 修改文案内容减少重复 |
| 无法解决 | 联系 Rule Engine |

## 相关链接

- 规范文档：`docs/20-specs/content-generation-spec.md`
- 检查工具：`tools/content_check/duplication.py`
- 门禁注册表：`docs/40-dev-loop/gate_registry.yaml`
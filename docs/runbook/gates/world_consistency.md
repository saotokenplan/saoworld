# Runbook: World Consistency Check (G-CONTENT-001)

> gate_id: G-CONTENT-001
> gate_name: World Consistency Check
> gate_type: content
> owner: Rule Engine

## 门禁概述

World Consistency Check 是内容一致性检查门禁，验证生成的内容是否符合世界观设定。

**触发条件**：
- 路径：`game/data/**`, `tools/content_check/**`
- 触发：`on_content_pr`

**执行命令**：
```bash
python tools/content_check/world_consistency.py --input <content_dir> --rules game/data/
```

**预期耗时**：60 秒

## 常见失败原因

### 1. 阵营关系冲突

**现象**：
- 检查失败，提示阵营关系冲突
- NPC 所属阵营与世界观设定不一致

**解决方案**：
```bash
# 查看详细错误信息
python tools/content_check/world_consistency.py --input game/data/ --rules game/data/ --verbose

# 检查阵营关系矩阵
# 文件：game/data/factions/faction_list.json
# 确认阵营关系是否正确

# 修改内容数据中的阵营信息
```

### 2. NPC 身份越界

**现象**：
- NPC 身份越过章节认知边界
- NPC 不应该知道某个区域或事件

**解决方案**：
```bash
# 查看详细错误信息
python tools/content_check/world_consistency.py --input game/data/ --rules game/data/ --verbose

# 检查章节定义
# 文件：game/data/chapters/chapter_list.json
# 确认章节认知边界

# 修改 NPC 数据中的知识范围
```

### 3. Schema 版本缺失

**现象**：
- 提示缺少 schema_version 字段
- 内容数据格式不符合要求

**解决方案**：
```bash
# 查看详细错误信息
python tools/content_check/world_consistency.py --input game/data/ --rules game/data/ --verbose

# 在内容数据中添加 schema_version 字段
# 示例：{"schema_version": 1, ...}
```

## 手动执行

```bash
# 检查整个 game/data 目录
python tools/content_check/world_consistency.py --input game/data/ --rules game/data/

# 检查单个区域
python tools/content_check/world_consistency.py --input game/data/regions/ --rules game/data/

# 查看详细输出
python tools/content_check/world_consistency.py --input game/data/ --rules game/data/ --verbose
```

## 升级路径

| 级别 | 处理方式 |
|------|----------|
| 阵营冲突 | 修改内容数据中的阵营信息 |
| 身份越界 | 调整 NPC 的知识范围 |
| Schema 缺失 | 添加 schema_version 字段 |
| 无法解决 | 联系 Rule Engine |

## 相关链接

- 规范文档：`docs/20-specs/content-generation-spec.md`
- 检查工具：`tools/content_check/world_consistency.py`
- 门禁注册表：`docs/40-dev-loop/gate_registry.yaml`
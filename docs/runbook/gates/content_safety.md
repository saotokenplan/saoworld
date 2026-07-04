# Runbook: Content Safety Check (G-CONTENT-003)

> gate_id: G-CONTENT-003
> gate_name: Content Safety Check
> gate_type: content
> owner: Rule Engine

## 门禁概述

Content Safety Check 是内容安全检查门禁，验证内容是否包含敏感词、高风险主题等不适宜内容。

**触发条件**：
- 路径：`game/data/**`, `tools/content_check/**`
- 触发：`on_content_pr`

**执行命令**：
```bash
python tools/content_check/content_safety.py --input <content_dir>
```

**预期耗时**：30 秒

## 常见失败原因

### 1. 敏感词命中

**现象**：
- 内容包含敏感词，检查直接驳回
- 提示风险等级为 critical

**解决方案**：
```bash
# 查看详细错误信息
python tools/content_check/content_safety.py --input game/data/ --verbose

# 修改内容中的敏感词
# 使用同义词替换或重写相关段落
```

### 2. 高风险主题识别

**现象**：
- 内容包含高风险主题，进入人工复核
- 提示风险等级为 high

**解决方案**：
```bash
# 查看详细错误信息
python tools/content_check/content_safety.py --input game/data/ --verbose

# 评估内容是否适合目标年龄层
# 修改或移除高风险内容
# 或提交人工复核
```

### 3. 目标年龄层不匹配

**现象**：
- 内容不符合目标年龄层要求
- 包含暴力、色情或政治敏感内容

**解决方案**：
```bash
# 查看详细错误信息
python tools/content_check/content_safety.py --input game/data/ --verbose

# 检查游戏配置中的目标年龄层
# 文件：game/data/config/game_config.json

# 修改内容使其符合目标年龄层
```

## 手动执行

```bash
# 检查整个 game/data 目录
python tools/content_check/content_safety.py --input game/data/

# 查看详细输出
python tools/content_check/content_safety.py --input game/data/ --verbose

# 生成安全报告
python tools/content_check/content_safety.py --input game/data/ --report
```

## 升级路径

| 级别 | 处理方式 |
|------|----------|
| 敏感词命中 | 修改或替换敏感词 |
| 高风险主题 | 修改内容或提交人工复核 |
| 年龄层不匹配 | 调整内容适合目标年龄层 |
| 无法解决 | 联系 Rule Engine |

## 相关链接

- 规范文档：`docs/20-specs/content-generation-spec.md`
- 检查工具：`tools/content_check/content_safety.py`
- 门禁注册表：`docs/40-dev-loop/gate_registry.yaml`
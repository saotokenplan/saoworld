# Runbook: Reward Boundary Check (G-CONTENT-002)

> gate_id: G-CONTENT-002
> gate_name: Reward Boundary Check
> gate_type: content
> owner: Rule Engine

## 门禁概述

Reward Boundary Check 是数值平衡检查门禁，验证奖励、敌人强度、资源刷新等是否在合理范围内。

**触发条件**：
- 路径：`game/data/**`, `tools/content_check/**`
- 触发：`on_content_pr`

**执行命令**：
```bash
python tools/content_check/reward_boundary.py --input <content_dir> --budget game/data/config/
```

**预期耗时**：45 秒

## 常见失败原因

### 1. 奖励突破章节上限

**现象**：
- 任务奖励超过章节允许的上限
- 经验值或金币奖励过高

**解决方案**：
```bash
# 查看详细错误信息
python tools/content_check/reward_boundary.py --input game/data/ --budget game/data/config/ --verbose

# 检查章节数值配置
# 文件：game/data/chapters/chapter_list.json
# 确认章节奖励上限

# 修改任务奖励数值
```

### 2. 敌人强度超限

**现象**：
- 敌人强度超出区域允许的区间
- 玩家无法击败敌人

**解决方案**：
```bash
# 查看详细错误信息
python tools/content_check/reward_boundary.py --input game/data/ --budget game/data/config/ --verbose

# 检查区域难度配置
# 文件：game/data/regions/*.json
# 确认区域敌人强度范围

# 修改敌人属性
```

### 3. 资源刷新异常

**现象**：
- 资源刷新频率不在服务器配置区间内
- 刷取漏洞风险

**解决方案**：
```bash
# 查看详细错误信息
python tools/content_check/reward_boundary.py --input game/data/ --budget game/data/config/ --verbose

# 检查游戏配置
# 文件：game/data/config/game_config.json
# 确认资源刷新配置

# 修改资源刷新参数
```

## 手动执行

```bash
# 检查整个 game/data 目录
python tools/content_check/reward_boundary.py --input game/data/ --budget game/data/config/

# 查看详细输出
python tools/content_check/reward_boundary.py --input game/data/ --budget game/data/config/ --verbose
```

## 升级路径

| 级别 | 处理方式 |
|------|----------|
| 奖励超限 | 降低任务奖励数值 |
| 敌人强度 | 调整敌人属性到合理范围 |
| 资源刷新 | 修改刷新参数 |
| 无法解决 | 联系 Rule Engine |

## 相关链接

- 规范文档：`docs/20-specs/content-generation-spec.md`
- 检查工具：`tools/content_check/reward_boundary.py`
- 门禁注册表：`docs/40-dev-loop/gate_registry.yaml`
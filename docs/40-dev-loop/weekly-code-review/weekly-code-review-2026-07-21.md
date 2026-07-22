# 每周代码审查与重构报告 - 2026-07-21

> 统计窗口：2026-07-15 至 2026-07-21
> 执行方式：自动化周审查 + 小步验证式重构
> 执行口径：优先高价值、低风险、可验证修改；无法确认安全性的事项只记录建议，不强行落地
> 说明：本文档聚焦代码热点、审查发现、已实施修复和下周治理方向，不重复承担项目级状态页或周报职责。

## 一、本周代码热点

### 1.1 数据来源

- 最近 7 天 Git 改动与热点文件统计
- `.trae/rules/10-python-backend.md`
- `.trae/rules/41-testing.md`
- `docs/00-governance/project-status.md`
- `docs/40-dev-loop/weekly-report-2026-07-21.md`

### 1.2 热点模块

| 模块 | 近 7 天热度 | 代码审查关注点 |
|------|-------------|----------------|
| `docs/40-dev-loop` | 很高 | 自动产物、状态文档和周报更新过密，易产生噪音 |
| `services/player` | 很高 | 模型与 schema 大文件化，子域边界模糊 |
| `services/generation` | 很高 | 模板、适配器和生成链路持续扩张 |
| `services/ops` | 很高 | 路由聚合过载，接口层职责过宽 |
| `services/vote` | 高 | 讨论、复盘、风控能力集中扩展 |
| `services/world` | 高 | 怪物/Boss 等内容定义与接口风格漂移 |
| `game/` | 高 | 场景与脚本契约、测试基建和 UI 直接依赖问题 |
| `workers/` | 高 | 审核汇总、调度参数和任务测试薄弱 |
| `tools/content_check` | 中 | 规则实现与配置语义存在漂移 |

## 二、核心发现

### 2.1 架构与边界问题

- `services/ops/app/api/routes.py` 单文件承载过多路由，已达到需要按领域拆分的阈值。
- `services/player/app/domain/models.py` 与 `schemas/player.py` 同时覆盖玩家、社交、公会、经济、匹配等子域，维护成本持续升高。
- `workers/tasks/analytics_pipeline.py` 直接依赖服务内部模型与仓储，Worker 与服务边界开始模糊。
- `game` 多处 UI 直接读取 manager 私有字段，客户端解耦性不足。

### 2.2 可靠性与稳定性问题

- `workers` 审核汇总结果与子审核状态语义不一致，容易导致总结果错误。
- `workers/tasks/scheduled_tasks.py` 的定时审核任务存在错误参数调用，运行时可能直接异常。
- `tools/content_check/content_safety.py` 存在死分支与阈值逻辑空操作，导致规则配置失真。
- `game/scripts/ui/voting_panel.gd` 与 `VotingPanel.tscn` 的节点契约存在高风险失配。
- `services/world` monster/boss 路由在 envelope 风格上存在漂移，影响接口一致性。

### 2.3 测试与维护问题

- `workers` 缺少对审核汇总语义和定时审核参数行为的关键回归测试。
- `tools/content_check` 缺少全年龄内容和违禁词阈值边界测试。
- `game/tests` 当前混用多种测试风格，GUT 安装与基类不统一，回归信号可信度不足。
- `tools/generate-commit-msg.py` 与 `tools/validate-commit-msg.py` 存在重复逻辑，值得后续抽公共 helper。

## 三、本周已落地修复

### 3.1 `workers` 审核链路修复

- 统一完整审核汇总结果与子审核状态语义。
- 修复定时内容审核任务的错误参数调用。
- 在缺少 `content_package_id` 时改为安全返回 `skipped`，提升行为可解释性。

### 3.2 `content_check` 规则修复

- 修复全年龄内容场景下成熟主题升级逻辑不可达的问题。
- 补齐违禁词阈值超限告警，让配置字段真正生效。

### 3.3 回归测试补齐

- 为 `workers` 审核汇总与定时审核补齐最小回归测试。
- 为 `tools/content_check` 的边界规则补齐回归测试。
- 对改动文件执行了 `pytest`、`ruff` 和聚焦式 `mypy` 验证。

## 四、暂未处理但建议跟进

### 4.1 下周优先治理

1. 拆分 `services/ops/app/api/routes.py`，先做无行为变化整理。
2. 拆分 `services/player` 的大型模型与 schema 文件，降低跨子域冲突面。
3. 修复 `game` 投票面板与场景脚本契约问题，并统一客户端测试基建。
4. 统一 `services/world` monster/boss 路由的 envelope 返回风格。
5. 单独开类型债治理任务，收敛 `workers` 与 `tools` 的既有 `mypy` 基线问题。

### 4.2 暂缓处理

- `workers` 直连数据库的分析链路重构
- `tools/agents` 多 CLI 风格统一
- 客户端投票/社交场景的视觉资源收敛

## 五、验证结果

### 5.1 通过项

- `tools/content_check/tests/test_content_safety.py`
  - 结果：通过
- `workers/tests/test_content_review.py`
  - 结果：通过
- `workers/tests/test_scheduled_tasks.py`
  - 结果：通过
- `ruff` 针对改动文件
  - 结果：通过
- 聚焦式 `mypy` 针对改动文件
  - 结果：通过

### 5.2 基线说明

- `workers` 与 `tools` 目录仍存在既有类型债，不属于本轮新增问题。
- 本轮已确认增量修复本身没有引入新的静态检查问题。

## 六、回滚与风险

- 本轮修复均为小步、可回滚的局部调整，未进行跨模块大面积重写。
- 当前残余高风险问题主要仍在：
  - `game` 场景/脚本契约
  - `services/ops` 与 `services/player` 大文件化
  - 运行时环境验证受 Docker / PostgreSQL / Godot 导出环境限制

## 七、与其他文档的关系

- `docs/00-governance/project-status.md`
  - 项目级状态、阻塞和下一阶段建议
- `docs/40-dev-loop/weekly-report-2026-07-21.md`
  - 周度成果、偏差判断与交付建议
- `weekly-code-review-automation.md`
  - 周度代码审查自动执行边界与授权

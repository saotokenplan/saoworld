# 每周代码审查与重构报告 - 2026-07-21

> 统计窗口：2026-07-15 至 2026-07-21
> 执行方式：自动化周审查 + 小步验证式重构
> 执行口径：优先高价值、低风险、可验证修改；无法确认安全性的事项只记录建议，不强行落地

## 一、本周改动概览

### 1.1 数据来源

- Git 最近 7 天提交与文件变更统计
- `docs/10-requirements/需求迭代计划.md`
- `docs/10-requirements/项目里程碑与验收标准.md`
- `.trae/rules/10-python-backend.md`
- `.trae/rules/41-testing.md`
- `docs/00-governance/project-status.md`
- `docs/40-dev-loop/weekly-report-2026-07-21.md`

### 1.2 主要改动模块

按最近 7 天文件命中次数汇总，热点主要集中在：

| 模块 | 近 7 天变更命中 | 观察 |
|------|----------------|------|
| `docs/40-dev-loop` | 666 | 执行记录、状态报告和周报密集更新 |
| `services/player` | 91 | 玩家成长、社交、经济、公会、公会战、匹配等持续扩张 |
| `services/generation` | 91 | 生成链路与模板/适配器保持活跃 |
| `tools/agents` | 74 | 多个 agent CLI、schema 和测试集中扩展 |
| `services/ops` | 70 | 运营后台统一 API、反馈系统、洞察与事件配置持续增加 |
| `services/vote` | 51 | 投票讨论、异常检测、投票复盘与风控能力完善 |
| `services/world` | 48 | NPC/任务/物品/怪物/Boss 等世界内容模型扩展 |
| `game/scripts` | 48 | 投票 UI、社交 UI、管理器脚本和客户端行为持续迭代 |
| `game/tests` | 45 | GUT/脚本式测试持续补充 |
| `workers` | 高频新增 | 内容生成、审核、打包、发布、门禁与定时任务链路活跃 |

### 1.3 本周改动主题判断

- 主主题 1：Sprint 9 公测准备收尾，重点从“功能建设”转向“发布闭环与运行时验证”
- 主主题 2：`player` / `ops` / `vote` / `world` 四个服务继续做产品面扩张，出现“大文件、跨子域聚合、接口层热点”
- 主主题 3：`workers` 和 `tools` 继续承接自动化与内容治理，开始暴露“任务编排与规则实现漂移”的维护风险
- 主主题 4：客户端 `game/` 在投票、社交、公会战、协作任务等 UI 链路上快速推进，但出现脚本与场景契约不一致、测试基建不统一的问题

### 1.4 风险区域概览

- `workers/`：审核链路结果聚合、定时任务参数、任务测试薄弱
- `services/ops/`：单个路由文件过载，运营 API 聚合层职责过宽
- `services/player/`：领域模型与 schema 大文件化，子域边界模糊
- `services/world/`：怪物/Boss 路由返回风格漂移， envelope 一致性存在退化
- `game/`：场景节点与脚本 onready 契约失配，UI 直接读取管理器私有字段
- `tools/content_check/`：规则实现存在死分支，测试缺少关键边界场景

## 二、多维度分析

### 2.1 架构一致性

| 问题 | 影响范围 | 严重度 | 处理建议 |
|------|----------|--------|----------|
| `services/ops/app/api/routes.py` 单文件承载健康检查、分析、洞察、投票/内容/审核代理、事件、反馈等 50+ 路由 | `ops-service` 新增接口与审计/trace 逻辑 | 高 | 下周按领域拆分 route 模块，只拆文件不改行为 |
| `services/player/app/domain/models.py` 与 `schemas/player.py` 跨玩家/社交/公会/经济/匹配多子域持续膨胀 | `player-service` 全域维护成本 | 高 | 下周按子域拆模型与 schema，并抽 JSONB→DTO 装配层 |
| `workers/tasks/analytics_pipeline.py` 直接依赖 `app.domain.models` 和 `app.repositories.analytics_repo` | Worker 与服务边界 | 中 | 下周评估替换为服务 API / 专用数据访问适配层 |
| `game` 多个 UI 直接读取 manager 私有字段（如 `FriendManager._friends`） | 客户端 UI 与 manager 解耦性 | 中 | 下周补公开 getter，禁止 UI 访问 `_` 前缀状态 |

### 2.2 可读性

| 问题 | 影响范围 | 严重度 | 处理建议 |
|------|----------|--------|----------|
| `services/ops` / `services/player` 大文件化，职责边界越来越难扫描 | 后端服务审查与后续重构 | 高 | 按领域拆文件，先做无行为变化整理 |
| `workers/tasks/content_review.py` 多个审核任务模板高度相似 | Worker 审核链路 | 中 | 下周抽公共 review 执行骨架 |
| `game` 投票相关场景重复写 UI 风格与状态映射 | 客户端投票 UI | 中 | 抽共享 formatter / theme 资源 |
| `tools/generate-commit-msg.py` 与 `tools/validate-commit-msg.py` 逻辑重复 | 提交信息工具链 | 中 | 下周抽公共 commit message helper 模块 |

### 2.3 可靠性

| 问题 | 影响范围 | 严重度 | 处理建议 |
|------|----------|--------|----------|
| `workers` 完整审核汇总任务按 `passed/failed` 旧状态聚合，但子审核已返回 `approved/manual_review/rejected` | 内容审核总结果 | 高 | 本轮已修复 |
| `workers/tasks/scheduled_tasks.py` 的 `daily_content_review` 调用了错误参数名，运行即异常 | 定时审核任务 | 高 | 本轮已改为显式参数化行为；无包 ID 时返回 `skipped` 而非错误调用 |
| `tools/content_check/content_safety.py` 中 `target_age_rating == "all"` 的成熟内容升级逻辑不可达 | 内容安全检查 | 中 | 本轮已修复 |
| `tools/content_check/content_safety.py` 中违禁词阈值逻辑是空操作 | 内容安全检查 | 中 | 本轮已补实现与测试 |

### 2.4 稳定性

| 问题 | 影响范围 | 严重度 | 处理建议 |
|------|----------|--------|----------|
| `game/scripts/ui/voting_panel.gd` 依赖的节点与 `VotingPanel.tscn` 不匹配 | 客户端投票界面运行时 | 高 | 下周优先修复脚本/场景契约 |
| `services/world` monster/boss 路由存在 `request_id=""` 与手写 `model_dump()` 风格漂移 | 世界服务响应兼容性 | 中 | 下周统一到强类型 envelope |
| `workers` 定时任务和 README 描述存在漂移 | 运维使用与排障 | 中 | 下周同步文档与实际链路 |

### 2.5 可测试性

| 问题 | 影响范围 | 严重度 | 处理建议 |
|------|----------|--------|----------|
| `workers` 缺少对汇总审核结果和定时审核参数行为的测试 | Worker 核心链路 | 高 | 本轮已补关键回归测试 |
| `tools/content_check` 缺少 all-age 与违禁词阈值场景测试 | 内容质量门禁 | 中 | 本轮已补测试 |
| `game/tests` 混用 GUT 与普通 `Node` 脚本式测试，且 GUT 安装方式不固化 | 客户端测试基建 | 高 | 下周统一测试基类与插件安装方式 |

### 2.6 可维护性

| 问题 | 影响范围 | 严重度 | 处理建议 |
|------|----------|--------|----------|
| `player` 与 `vote` 同时复制贡献度倍率计算逻辑 | 投票资格与权重规则 | 中 | 下周抽共享策略或统一来源 |
| `ops` 事件 schema 同时维护 `TargetScope` 与 `EventTargetScope` 两套枚举来源 | 运营事件配置 | 中 | 下周统一枚举来源，避免更新请求与创建请求语义漂移 |
| `workers` / `tools` 中存在历史基线类型问题，容易掩盖增量改动的真实风险 | 静态检查信号质量 | 中 | 建议单独开类型债治理任务，不与业务扩张混做 |

## 三、关键问题清单

### 3.1 立即实施

1. 修复 `workers` 完整审核汇总结果与子审核状态不一致问题
2. 修复 `workers` 定时内容审核任务错误参数调用，并改为安全可解释行为
3. 修复 `tools/content_check` 内容安全检查中的死分支与空实现
4. 补齐对应最小回归测试

### 3.2 建议纳入下周

1. 拆分 `services/ops/app/api/routes.py`
2. 拆分 `services/player` 大型模型与 schema 文件
3. 统一 `services/world` monster/boss 路由 envelope 返回风格
4. 修复 `game` 投票面板场景/脚本契约不一致
5. 统一 `game/tests` 的 GUT 测试基建
6. 抽取 `tools` 提交信息工具公共模块

### 3.3 暂缓处理

1. `workers` 直连 DB 的分析链路重构
2. `tools/agents` 多 CLI 风格统一
3. `game` 投票/社交场景视觉层重复资源收敛

## 四、已实施的重构与优化项

### 4.1 `workers` 审核链路修复

- 文件：`workers/tasks/content_review.py`
- 修改：
  - 新增 `_determine_overall_result()`
  - 将完整审核汇总从旧状态 `passed/failed/needs_review` 切换为与子审核一致的 `approved/manual_review/rejected`
- 价值：
  - 避免完整审核结果长期偏向错误状态
  - 使 review-service 与 workers 语义对齐

### 4.2 `workers` 定时任务防故障修复

- 文件：`workers/tasks/scheduled_tasks.py`
- 修改：
  - `daily_content_review` 改为显式接收 `content_package_id`
  - 无 `content_package_id` 时返回 `skipped` + 原因，不再走错误参数调用
  - 有 `content_package_id` 时调用 `run_full_content_review`
- 价值：
  - 消除既有错误参数导致的运行时失败
  - 让调度行为更可解释、可测试

### 4.3 `content_check` 规则修复

- 文件：`tools/content_check/content_safety.py`
- 修改：
  - 修复 `target_age_rating == "all"` 时成熟主题严重度升级逻辑不可达问题
  - 补齐违禁词阈值超限告警 issue
- 价值：
  - 让“全年龄内容更严格”规则真正生效
  - 让违禁词阈值配置从摆设变成可执行规则

### 4.4 测试补齐

- 文件：
  - `workers/tests/test_content_review.py`
  - `workers/tests/test_scheduled_tasks.py`
  - `tools/content_check/tests/test_content_safety.py`
- 新增验证点：
  - 完整审核汇总在 mixed / rejected 场景下的结果
  - 定时内容审核在缺少参数与显式传参场景下的行为
  - 全年龄等级成熟主题升级
  - 违禁词阈值超限告警

## 五、暂未处理但建议跟进的问题

1. `game/scripts/ui/voting_panel.gd` 与 `VotingPanel.tscn` 的节点契约失配，属于高风险运行时问题
2. `services/ops` 路由过载，已达到需要无行为拆分的阈值
3. `services/player` 的模型与 schema 大文件化会持续放大改动冲突面
4. `services/world` 的 monster/boss 接口返回风格漂移，后续容易引发客户端兼容问题
5. `game/tests` 当前环境不可复现，导致客户端回归信号可信度不足
6. `workers` 分析链路与类型检查基线债务仍在，需要单独治理

## 六、测试与验证结果

### 6.1 通过项

- `python -m pytest tools/content_check/tests/test_content_safety.py -q`
  - 结果：`9 passed`
- `python -m pytest workers/tests/test_content_review.py workers/tests/test_scheduled_tasks.py -q`
  - 结果：`11 passed`
- `python -m ruff check workers/tasks/content_review.py workers/tasks/scheduled_tasks.py workers/tests/test_content_review.py workers/tests/test_scheduled_tasks.py tools/content_check/content_safety.py tools/content_check/tests/test_content_safety.py`
  - 结果：通过
- `python -m mypy tasks/content_review.py tasks/scheduled_tasks.py --follow-imports skip`（在 `workers/` 下执行）
  - 结果：通过
- `python -m mypy content_safety.py --follow-imports skip`（在 `tools/content_check/` 下执行）
  - 结果：通过

### 6.2 基线问题说明

- 在直接执行 `mypy` 时，`workers` 与 `tools/content_check` 目录都暴露出仓库既有类型问题，不属于本轮修改文件：
  - `workers/tasks/analytics_pipeline.py`
  - `workers/tasks/content_generation.py`
  - `tools/content_check/base.py`
- 本轮已使用“只针对改动文件的收敛式类型检查”验证增量改动没有新增类型问题。

## 七、新增或沉淀的规范 / Skills

### 7.1 新增规范文档

- `docs/40-dev-loop/weekly-code-review/weekly-code-review-automation.md`
  - 场景：每周六自动执行周度代码审查与低风险重构
  - 作用：固化自动执行边界、无需再次人工确认的条件、降级与回滚策略
- 平台定时任务登记尝试：
  - 已尝试创建每周六自动执行任务
  - 本轮结果：平台确认超时，自动跳过
  - 后续动作：保留自动执行规范，待下次重新登记调度

### 7.2 本轮沉淀的可复用检查项

- 常见坏味道识别：
  - 子任务状态语义和聚合状态不一致
  - 场景与脚本节点契约漂移
  - 规则配置字段存在但实现为空操作
  - UI 读取管理器私有字段
- 最小回归测试模式：
  - 针对“错误旧逻辑 → 新语义”补聚合测试
  - 针对“错误参数调用 → 安全降级”补定时任务测试
  - 针对“死分支 → 可执行规则”补边界测试

## 八、风险与回滚说明

- 本轮代码修改均为小步、可回滚的局部修复，未做跨模块大面积重写
- 回滚路径清晰：
  - `workers` 修复可逐文件回退
  - `tools/content_check` 规则修复可逐文件回退
  - 测试文件为新增回归保护，可保留
- 当前残余风险：
  - `game` 场景/脚本契约问题尚未落地修复
  - `services/ops` / `services/player` 大文件风险仍会持续放大
  - 运行时环境验证仍受 Docker / PostgreSQL / Godot 导出环境限制

## 九、下周建议继续治理的方向

1. 优先修复 `game` 投票面板与结果面板的场景/脚本契约问题，并统一客户端测试基建
2. 拆分 `services/ops` 路由热点，先做无行为变化的文件整理
3. 拆分 `services/player` 模型与 schema，降低跨子域改动冲突
4. 统一 `services/world` monster/boss 接口响应 envelope
5. 单独开类型债治理任务，清理 `workers` / `tools` 既有 `mypy` 基线问题

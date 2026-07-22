# docs/40-dev-loop 与 project-status 深度整理任务规划

## 任务目标

在不改动业务代码的前提下，系统整理 `docs/40-dev-loop/` 与 `docs/00-governance/project-status.md`，收拢项目级状态、周报/日报、自动状态报告和累计进度日志之间的边界，去除重复堆叠内容，降低根目录噪音，并保留必要的审计与追溯能力。

## 当前判断

- `docs/40-dev-loop/` 根目录同时存在入口文档、方法论文档、周报、自动状态报告、累计进度日志和发布资料，一级阅读路径过载。
- `docs/00-governance/project-status.md` 混入大量按小时追加的“项目就绪状态持续验证”记录，导致项目级状态判断与过程遥测耦合。
- `docs/40-dev-loop/auto-progress-log.md`、`docs/40-dev-loop/auto-status-report-*.md`、周报，以及 `project-status.md` 之间存在高重复的“当前阻塞 / 测试数量 / 灰度发布就绪”表述。
- 当前真正缺少的不是更多状态文本，而是明确的分层规则：
  - `project-status.md` 应只回答“现在做到哪一步、当前阻塞是什么、下一步建议是什么”
  - `40-dev-loop/README.md` 应只回答“研发过程材料去哪看”
  - `weekly-report-*` 应承担周度分析
  - `auto-progress-log.md` 与 `archives/auto-generated/` 应承担遥测和审计追溯

## 目标范围

本轮默认只处理以下内容：

- `docs/40-dev-loop/README.md`
- `docs/40-dev-loop/auto-progress-log.md`
- `docs/40-dev-loop/weekly-report-*.md`
- `docs/40-dev-loop/auto-status-report-*.md`
- `docs/00-governance/project-status.md`
- 如有必要，同步更新少量与阅读路径强相关的治理入口文档
- `.trae/output/dev-loop-governance-cleanup-20260722/` 下的规划与验收文档

本轮默认不处理以下内容：

- `archives/auto-generated/` 下的大规模历史归档改名或删除
- `services/`、`game/`、`workers/` 等业务代码
- `.trae/rules/` 规则文件
- 与本轮边界无关的其他 `docs/` 主题文档

## 整理原则

- 先做“分层归位”，再做“正文删重”
- 优先压缩根级重复描述，不破坏归档和审计线索
- 项目级状态文档保留“结论、阻塞、建议”，不保留按小时流水
- 流程治理目录保留“入口、分组、阅读顺序”，不把自动状态报告继续当一级阅读入口
- 自动状态报告与进度日志保留，但应明确其为“过程遥测 / 审计材料”

## 六阶段执行计划

### 阶段 1：基线盘点

- 盘点 `40-dev-loop` 根目录现有文档分组
- 标记与 `project-status.md` 重复最严重的状态类文档
- 提炼“项目级状态 / 周度复盘 / 自动遥测 / 审计归档”的分层方案

### 阶段 2：状态边界重写

- 重写 `project-status.md` 的定位和结构
- 将按小时堆叠的运行状态从项目级正文中剥离
- 保留少量关键里程碑和当前阻塞，不再把周期性验证流水直接堆进主状态页

### 阶段 3：40-dev-loop 根目录收口

- 重写 `docs/40-dev-loop/README.md`
- 明确根目录只保留入口型和长期型文档
- 弱化 `auto-status-report-*.md` 在一级阅读路径中的权重

### 阶段 4：自动状态与进度日志降噪

- 评估 `auto-progress-log.md` 是否收敛为“索引 + 近期摘要”
- 评估根目录 `auto-status-report-*.md` 是否应转为“最近快照”或仅由进度日志与归档引用
- 对明显重复的“无新工作 / 优雅结束 / 同一阻塞”表述进行摘要化

### 阶段 5：周报与状态关系梳理

- 检查 `weekly-report-*` 与 `project-status.md` 的重复段
- 保留周报的分析属性，避免其重复承担“当前唯一权威状态页”的角色
- 统一“哪里看当前结论 / 哪里看趋势复盘 / 哪里看自动遥测”的说法

### 阶段 6：验收与交付

- 复查各文档是否回归单一职责
- 检查根目录噪音是否下降
- 输出整理摘要、未决项和后续建议

## 建议的实际改动清单

优先级从高到低：

1. 精简 `docs/00-governance/project-status.md`
2. 更新 `docs/40-dev-loop/README.md`
3. 视结果收敛 `docs/40-dev-loop/auto-progress-log.md`
4. 视结果调整根目录 `auto-status-report-*.md` 的入口定位
5. 视结果微调 `weekly-report-2026-07-21.md` 中对状态页的依赖表述

## 风险与控制

- 风险：过度删减导致历史状态线索丢失
  - 控制：不删除归档报告，优先把重复内容改为引用和摘要
- 风险：`project-status.md` 改得过轻，失去可读性
  - 控制：保留“当前阶段 / 当前结论 / 已确定事项 / 当前风险 / 下一阶段建议”主骨架
- 风险：`40-dev-loop/` 根目录调整后阅读路径断裂
  - 控制：在 `README.md` 中明确“入口页 / 周报 / 进度日志 / 自动归档”的关系
- 风险：本轮范围外溢到整个 `docs/`
  - 控制：本轮只处理 `40-dev-loop` 与 `project-status.md` 直接相关文档

## 回滚路径

- 若 `project-status.md` 调整后不利于阅读，可按文件级回滚该文档
- 若 `40-dev-loop/README.md` 调整后导航不清，可按文件级回滚入口页
- 对自动状态报告和进度日志优先做“摘要化 / 引用化”，不做不可逆删除

## 待确认决策

请在执行前确认以下问题：

1. 本轮是否允许直接精简 `project-status.md` 中的大段历史状态流水，而不是仅做头部说明补充。
2. 本轮是否允许把 `40-dev-loop` 根目录中的状态型文档进一步降级为“引用入口”，减少其在一级阅读路径的直接暴露。
3. 本轮是否只做“结构去重 + 正文收敛”，还是连同最近几份 `weekly-report-*` 一并做轻量瘦身。

## 默认执行建议

若你不额外指定，我建议本轮采用以下默认方案：

- 直接精简 `project-status.md` 的小时级状态流水
- 保留 `40-dev-loop` 根目录文档，但重写入口和阅读顺序，降低状态类文档的一级权重
- 只对最近一份周报做必要同步，不大规模改历史周报

这样能先把“当前状态页”和“研发过程层”拆开，再决定是否做第二轮历史文档归档整理。

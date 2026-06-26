# Agent 与 Loop 执行规范

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 适用范围

- 适用于 AI coding 体系下的 Agent 角色分工、需求包格式、门禁设计、日志采集和反馈闭环。
- 适用于任务拆分、执行循环、问题归因、规则改进和回滚升级流程。
- 不替代产品规范、系统契约和工程协作规范中的专项内容，而是约束这些规范如何进入执行闭环。

## 当前定位

- 本文档是 Agent 与研发闭环的核心执行规范，用于回答“任务如何输入、Agent 如何协作、门禁如何工作、问题如何持续改进”。
- 本文档聚焦流程治理、闭环机制和人机协作边界，不单独定义产品边界、数据模型或接口契约。
- 当日常执行方式、门禁策略或反馈机制存在歧义时，应优先以本文档为准。

## 目标

本规范定义 AI coding 体系下的角色分工、输入输出格式、门禁设计、日志采集和问题反馈流程。重点不是让单个 Agent 更聪明，而是让整个闭环能稳定交付、稳定暴露问题、稳定吸收反馈。

## Agent 角色规范

### Product Agent

- 读取产品目标、用户反馈、投票趋势和路线图
- 输出需求包与优先级
- 不直接写代码

### System Designer Agent

- 拆系统边界、模块接口、数据契约
- 维护模板和规则版本
- 不直接上线内容

### Gameplay Agent

- 实现 Godot 客户端逻辑
- 编写场景、交互、角色控制和任务触发
- 补齐客户端测试和最小验证脚本

### World Agent

- 生成 NPC、任务、聚落和事件内容草案
- 输出结构化内容对象
- 不跳过审核直接上线

### Backend Agent

- 实现投票、生成、审核、投放和运营接口
- 维护任务队列、数据模型和服务协作

### QA Agent

- 维护门禁、验收、内容检查和回归脚本
- 汇总失败模式并创建改进输入

### Build Agent

- 负责打包、镜像、部署、灰度和回滚执行

### Ops Agent

- 汇总线上与流水线信号
- 生成 Gate Improvement Issue 和 Rule Improvement 输入

## 需求包规范

所有开发任务必须以需求包为输入。需求包最少包含：

- `spec.md`
  - 需求说明、范围、非目标
- `acceptance.md`
  - 可执行的验收语句
- `risk.md`
  - 风险点与约束
- `tasks.md`
  - 原子任务拆分

### 需求包规则

- 每个任务只允许有一个主目标
- 非目标必须显式列出
- 验收必须能映射到测试或门禁
- 风险必须带处理策略

## 任务拆分规范

- 每个任务应可在 `1` 个工作日内实现并验证
- 任务粒度优先按“可验收能力”拆分，不按技术层随意切块
- 任务必须标明依赖关系
- 任务必须标明修改范围和回滚影响

## 一层 Loop 规范

### 执行流程

1. 读取需求包
2. 拆成实现任务
3. 编码与补测试
4. 运行门禁
5. 失败则生成修复计划
6. 重复直到全绿
7. **提交前自检**（见下方清单）
8. git commit 并 push（通过 commit-msg hook 校验）
9. 生成人类验收摘要

### AI 提交前自检清单（强制执行）

在执行 `git commit` 之前，Agent 必须逐项确认以下内容：

1. **主题单一性**：本次提交是否只包含一个清晰主题？若有多个独立改动，必须拆分多次提交。
2. **提交信息格式**：
   - 是否符合 `&lt;type&gt;(&lt;scope&gt;): &lt;summary&gt;` 格式？
   - type 是否为 `docs/feat/fix/refactor/test/chore` 之一？
   - scope 是否与改动模块一致（如 `vote`、`specs`、`api`、`game`）？
   - summary 是否使用祈使句（新增/补充/调整/修复/重构）、是否具体、是否在 100 字符以内？
   - summary 是否避免了模糊词汇（"update"、"fix stuff"、"一些修改"、"临时提交"）？
3. **内容完整性**：相关文档、配置、测试是否已同步更新？有无遗漏的引用更新？
4. **工作区清洁度**：是否混入了无关文件、调试代码、`pdb.set_trace()`、`print(debug)` 或 `&lt;&lt;&lt;&lt;&lt;&lt;&lt;` 冲突标记？
5. **自检验证**：可用 `python tools/validate-commit-msg.py --message "feat(vote): 你的摘要"` 预先验证。

提交后必须立即 push（除非远程不可用并明确说明阻塞原因）。

### 产物要求

- 代码变更
- 测试变更
- 门禁运行结果
- `fix-plan.md` 或等效修复摘要
- `release-notes.md` 或等效发布摘要

## 门禁体系规范

### 代码门禁

- `lint`
- `format`
- `typecheck`
- `unit`
- `integration`
- `e2e`
- `commit-msg`（提交信息格式校验，必须在 commit 阶段通过，CI 二次校验）
- `pre-commit`（调试残留、冲突标记、大文件检查）

### 内容门禁

- 世界一致性检查
- 奖励边界检查
- 敏感内容检查
- 重复度检查
- 可玩性最小路径检查

### 非功能门禁

- 构建时间基线
- 服务接口性能基线
- 崩溃率与错误率
- 内容发布时长

## 门禁设计要求

- 每个 gate 必须有唯一 `gate_id`
- 必须记录 owner、触发时机、成本预算、覆盖风险
- 必须能说明“挡住什么风险”
- 没有明确风险覆盖说明的 gate 不允许进入常驻流水线

## 二层 Loop 规范

### 输入

- Agent 会话日志
- CI 失败日志
- 线上事故日志
- 回滚记录

### 输出

- `Gate Improvement Issue`
- 门禁退役建议
- 阈值调整建议

### 归因分类

- 缺少 gate
- gate 覆盖不足
- gate 误报过高
- 验收语句不完整
- 模板或规则边界失效

## 三层 Loop 规范

### 输入

- Gate Improvement Issue 的处理结果
- 被采纳与被拒绝原因
- 规则命中率与误报率

### 输出

- `Rule Improvement PR`
- 阈值配置修改
- 样本集扩充
- 分类标签更新

## 日志采集规范

### `agent_session_log`

至少包含：

- `session_id`
- `agent_name`
- `task_id`
- `stage`
- `event`
- `status`
- `summary`
- `ts`

### `ci_failures`

至少包含：

- `pipeline_id`
- `branch`
- `gate_id`
- `status`
- `duration_s`
- `failure_signature`
- `related_task_id`

### `prod_incidents`

至少包含：

- `incident_id`
- `severity`
- `region_scope`
- `content_package_id`
- `symptom`
- `rollback_required`
- `root_cause`

## Issue 规范

### Gate Improvement Issue

必须包含：

- 症状
- 现有 gate 为何没挡住
- 建议新增或修改的 gate
- 验收标准
- 风险与成本

### Rule Improvement Issue

必须包含：

- 哪条规则误报或漏报
- 证据样本
- 建议阈值或匹配范围调整
- 预期改进指标

## 回滚与升级规范

### 代码回滚

- 所有发布必须有可回滚版本号
- 数据迁移必须有逆向方案或兼容期
- 任意失败发布必须在 `30` 分钟内完成回滚演练

### 内容回滚

- 回滚最小单位为内容包
- 回滚后需冻结相关模板，直到完成复盘

### Gate 升级

- 新 gate 先进入观察模式
- 连续两个周期有效后再进入强制阻断模式

## 人类介入边界

人类只在以下场景介入：

- 审批高风险内容上线
- 决定是否接受新 gate 或退役旧 gate
- 最终版本发布授权
- 核心事故复盘与边界调整

其他编码、修复、重复验证和常规问题归因应由 Agent 自主完成。

## 与其他文档的关系

- `docs/20-specs/product-spec.md`
  - 定义产品目标、范围和验收口径，本文档负责把这些要求转成 Agent 可执行的需求包与闭环流程。
- `docs/20-specs/backend-data-spec.md`
  - 提供后端接口、任务和回滚链路约束，作为 Agent 实施和门禁验证的重要输入。
- `docs/20-specs/content-generation-spec.md`
  - 定义生成与审核规则，本文档负责把这些规则纳入门禁、日志和问题反馈机制。
- `docs/20-specs/engineering-conventions.md`
  - 约束仓库结构、命名、测试和提交方式，作为本文档执行产物的工程落地标准。
- `docs/40-dev-loop/`
  - 提供门禁配置、日志 schema 和改进素材，作为本文档闭环机制的补充实现参考。

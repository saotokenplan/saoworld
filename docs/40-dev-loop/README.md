# 研发闭环入口

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本目录作为 `docs/40-dev-loop/` 的统一入口，用于区分研发方法论文档、运行手册、阶段设计、每日进展和自动化产物，降低该目录的检索噪音。

## 适用范围

- 适用于需要了解 AI Coding、Loop Engineering、门禁体系、日志观测和研发协作流程的场景。
- 适用于查找当前可执行流程、历史自动产物和运维型说明。
- 不替代 `docs/20-specs/` 的产品、数据和工程执行规范。

## 当前定位

- 本目录属于流程治理层，重点回答“研发怎么推进、门禁怎么运转、自动化产物怎么看”。
- 本目录不单独定义产品边界、接口契约或数据库约束。
- 若与 `docs/20-specs/` 的执行规范冲突，以 `docs/20-specs/` 为准。

## 目录分组

- `loop-engineering-plan.md`
  - Loop Engineering 主方案和治理设计
- `ai-coding-game-dev-loop-plan.md`
  - AI-first 游戏研发闭环方案
- `issue-templates-loop-engineering.md`
  - 流程改进和问题反馈模板
- `log-schemas-loop-engineering.md`
  - 会话、CI 和事故日志 schema
- `gate_registry.yaml`
  - 门禁注册表
- `daily-progress/`
  - 按日期记录的阶段性日报
- `runbooks/`
  - 已正式并入的运行手册目录，包含门禁排障与运维操作
- `p2-agent-design/`
  - 特定阶段或专题的 Agent 设计资料
- `archives/auto-generated/`
  - 自动规划、执行摘要和状态快照的归档目录
- `auto-progress-log.md`
  - 自动流程的累计进展日志

## 推荐阅读路径

1. 先读 `loop-engineering-plan.md`，理解流程主框架
2. 再读 `ai-coding-game-dev-loop-plan.md`，理解项目级落地方式
3. 需要查看门禁和观测时，读 `gate_registry.yaml` 与 `log-schemas-loop-engineering.md`
4. 需要查看最近自动化状态时，优先读 `auto-progress-log.md` 和最近的周报/日报
5. 需要追溯具体某轮自动产物时，再进入 `archives/auto-generated/`

## 自动产物阅读建议

- `auto-progress-log.md` 是优先入口，用于了解累计进展
- 自动规划、执行摘要和状态快照已归档到 `archives/auto-generated/`
- 归档文档主要用于审计和回溯，不建议作为一级阅读入口
- 归档文档中可能保留迁移前的历史路径描述，应按其产生时点理解

## 维护边界

- 方法论、门禁、日志 schema 和运行手册继续维护在本目录
- 自动产物保留，但不应继续污染根导航
- 新增流程性文档应先判断是“长期规范”还是“阶段性/自动化产物”，避免混放

## 与其他文档的关系

- `docs/20-specs/agent-loop-spec.md`
  - 提供执行规范层的 Agent 约束；本目录补充流程设计和运行材料
- `docs/40-dev-loop/runbooks/`
  - 作为本目录下的运行手册子目录，承接原排障与运维说明
- `docs/00-governance/`
  - 提供文档治理规则，负责定义本目录在整体体系中的位置

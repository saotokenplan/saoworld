# 研发闭环入口

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本目录作为 `docs/40-dev-loop/` 的统一入口，用于承接研发过程层材料，并把“项目级状态”“周度分析”“自动遥测”“运行手册”“归档追溯”区分开，降低根目录噪音。

## 适用范围

- 适用于需要了解 AI Coding、Loop Engineering、门禁体系、日志观测和研发协作流程的场景。
- 适用于查找当前可执行流程、历史自动产物和运维型说明。
- 不替代 `docs/20-specs/` 的产品、数据和工程执行规范。

## 当前定位

- 本目录属于流程治理层，重点回答“研发怎么推进、过程材料去哪看、自动化状态如何回查”。
- 本目录不承担项目级主状态页角色；项目当前结论统一以 `docs/00-governance/project-status.md` 为准。
- 本目录不单独定义产品边界、接口契约或数据库约束。
- 若与 `docs/20-specs/` 的执行规范冲突，以 `docs/20-specs/` 为准。

## 阅读顺序

1. 先看 `docs/00-governance/project-status.md`，了解项目级结论、阻塞与下一步
2. 再看最近周报，理解本周成果、偏差分析与趋势判断
3. 需要确认自动推进近况时，读 `auto-progress-log.md`
4. 需要查看长期规范和门禁时，读 `loop-engineering-plan.md`、`gate_registry.yaml`、`runbooks/`
5. 需要逐轮审计和回放时，再进入 `archives/auto-generated/`

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
  - 自动流程的累计摘要与近期快照入口
- `auto-status-report-*.md`
  - 根目录仅保留最近快照；详细状态历史统一进入归档目录
- `weekly-report-*.md`
  - 周度成果、指标变化和偏差分析

## 状态材料分层

- `project-status.md`
  - 只保留项目级结论、阻塞和下一阶段建议
- `weekly-report-*.md`
  - 只保留周度分析和趋势判断
- `auto-progress-log.md`
  - 只保留自动推进累计摘要与归档入口
- `auto-status-report-*.md`
  - 只保留最近自动状态快照，不作为一级主入口
- `archives/auto-generated/`
  - 保留逐轮自动产物，用于审计与回溯

## 维护边界

- 方法论、门禁、日志 schema 和运行手册继续维护在本目录
- 根目录优先保留长期入口型文档，自动产物优先进入归档体系
- 状态类文档新增前应先判断是“项目级结论”“周度分析”还是“自动遥测”，避免多处重复展开
- 新增流程性文档应先判断是“长期规范”还是“阶段性/自动化产物”，避免混放

## 与其他文档的关系

- `docs/20-specs/agent-loop-spec.md`
  - 提供执行规范层的 Agent 约束；本目录补充流程设计和运行材料
- `docs/40-dev-loop/runbooks/`
  - 作为本目录下的运行手册子目录，承接原排障与运维说明
- `docs/00-governance/`
  - 提供文档治理规则，负责定义本目录在整体体系中的位置

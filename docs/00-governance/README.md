# 文档治理入口

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本目录作为 `docs/00-governance/` 的统一入口，用于解释文档体系本身如何组织、如何变更、如何评审，以及在整理或扩展 `docs/` 时应先看哪些治理文档。

## 适用范围

- 适用于需要理解 `docs/` 分层规则、权威关系、变更流程和维护职责的协作场景。
- 适用于目录迁移、入口补齐、结构整理、文档评审和状态更新。
- 不替代 `20-specs/` 的执行规范，也不承担需求背景或接口参考角色。

## 当前定位

- 本文档是治理目录入口，不替代具体治理规则正文。
- 当需要回答“文档放哪里、以谁为准、谁来维护、改动后要同步什么”时，优先从本目录开始。
- 若治理说明与执行规范冲突，实施仍以 `docs/20-specs/` 和 `.trae/rules/52-documentation.md` 为准。

## 文档列表

- `document-directory-spec.md`
  - 定义 `docs/` 的标准分层、落位规则和命名原则
- `document-change-process.md`
  - 定义新增、迁移、重命名、归档和引用同步流程
- `document-lifecycle.md`
  - 定义文档状态模型和状态切换条件
- `document-ownership.md`
  - 定义治理责任和维护角色
- `document-review-checklist.md`
  - 定义文档评审时的统一检查项
- `document-template-alignment-checklist.md`
  - 记录模板对齐和增量复查情况
- `document-template-maintenance.md`
  - 定义模板后续维护方式
- `document-template-spec.md`
  - 定义各类文档的标准章节结构
- `document-map.md`
  - 定义权威关系、保留策略和全局角色说明
- `project-status.md`
  - 说明项目当前阶段和资产成熟度
- `quick-start.md`
  - 提供最小阅读路径和实施顺序
- `spec-skill-mapping.md`
  - 维护规范与技能引用关系
- `governance-phase-summary.md`
  - 记录治理阶段总结和移交重点

## 建议阅读顺序

1. 先读 `document-directory-spec.md`，明确文档应放在哪里
2. 再读 `document-map.md`，明确以谁为准
3. 然后读 `document-change-process.md`，明确改动流程
4. 再读 `document-lifecycle.md` 和 `document-template-spec.md`，明确状态和结构
5. 最后按需要查看 `project-status.md`、`quick-start.md` 和 `spec-skill-mapping.md`

## 与其他文档的关系

- `docs/README.md`
  - 作为 `docs/` 总入口，从全局导航本目录
- `docs/20-specs/README.md`
  - 作为执行规范入口，回答如何落地
- `docs/30-api/`
  - 作为接口参考层，回答接口怎么查
- `docs/40-dev-loop/`
  - 作为流程治理层，保留研发闭环设计与自动产物

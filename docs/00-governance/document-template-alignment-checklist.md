# 文档模板对齐复查清单

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本文档用于盘点当前 `docs/` 目录下各类文档与 `docs/00-governance/document-template-spec.md` 的对齐情况，明确哪些文档已经补齐基础结构，哪些文档仍缺 `适用范围`、`当前定位`、`与其他文档的关系` 等模板字段，便于后续按主题分批修整。

## 适用范围

- 适用于 `docs/` 目录下的 Markdown 文档结构复查。
- 适用于新增模板规范后，对既有文档做渐进式补齐时的排期和优先级判断。
- 不替代具体文档正文，也不替代目录规范、变更流程和生命周期规范。

## 当前定位

- 本文档是模板对齐工作的阶段性复查清单，不是最终约束规范。
- 本文档回答“哪些文档还没补齐结构字段”，不直接替代实际修订动作。
- 后续每轮结构补齐完成后，应同步更新本清单，避免复查结果过期。

## 复查口径

本清单按以下三个模板字段是否以标准章节形式存在进行复查：

- `## 适用范围`
- `## 当前定位`
- `## 与其他文档的关系`

说明：

- 本清单只统计 `docs/` 目录下的 Markdown 文档，不包含根 `README.md`。
- 本清单不把自身计入复查样本，避免统计口径循环引用。
- 若某文档已有相近语义内容，但未以标准章节形式出现，本次仍视为“未完全对齐”。
- 本清单不评价正文质量，只评价结构字段是否补齐。

## 复查结果概览

- 复查范围：
  - `docs/` 下共 `31` 份 Markdown 文档，不含本清单
- 已完整对齐：
  - `11` 份
- 部分对齐：
  - `4` 份
- 尚未按模板补齐：
  - `16` 份

## 一、已完整对齐

以下文档已具备 `适用范围`、`当前定位`、`与其他文档的关系` 三类结构字段：

- `docs/README.md`
- `docs/00-governance/document-map.md`
- `docs/00-governance/project-status.md`
- `docs/00-governance/quick-start.md`
- `docs/00-governance/document-directory-spec.md`
- `docs/00-governance/document-change-process.md`
- `docs/00-governance/document-review-checklist.md`
- `docs/00-governance/document-ownership.md`
- `docs/00-governance/document-lifecycle.md`
- `docs/00-governance/document-template-spec.md`
- `docs/20-specs/README.md`

## 二、部分对齐

### API 文档

- `docs/30-api/api-overview.md`
  - 已有：`当前定位`
  - 缺少：`适用范围`、`与其他文档的关系`
- `docs/30-api/api-permissions.md`
  - 已有：`当前定位`
  - 缺少：`适用范围`、`与其他文档的关系`
- `docs/30-api/api-error-codes.md`
  - 已有：`当前定位`
  - 缺少：`适用范围`、`与其他文档的关系`
- `docs/30-api/api-examples-vote.md`
  - 已有：`当前定位`
  - 缺少：`适用范围`、`与其他文档的关系`

## 三、尚未按模板补齐

以下文档目前未按标准章节形式补齐上述三类结构字段：

### 治理与映射

- `docs/00-governance/spec-skill-mapping.md`

### 需求文档

- `docs/10-requirements/open-world-ai-game-prd.md`
- `docs/10-requirements/需求概述.md`
- `docs/10-requirements/功能设计.md`
- `docs/10-requirements/技术方案.md`

### 执行规范正文

- `docs/20-specs/product-spec.md`
- `docs/20-specs/backend-data-spec.md`
- `docs/20-specs/content-generation-spec.md`
- `docs/20-specs/agent-loop-spec.md`
- `docs/20-specs/engineering-conventions.md`

### 研发闭环文档

- `docs/40-dev-loop/ai-coding-game-dev-loop-plan.md`
- `docs/40-dev-loop/loop-engineering-plan.md`
- `docs/40-dev-loop/issue-templates-loop-engineering.md`
- `docs/40-dev-loop/log-schemas-loop-engineering.md`

### 调研文档

- `docs/50-research/stack-research-ai-game-dev.md`
- `docs/50-research/service-stack-comparison.md`

## 四、建议修整顺序

建议按以下顺序推进，而不是全仓一次性机械补齐：

1. API 文档的“部分对齐”项
2. `spec-skill-mapping.md`
3. `20-specs/` 核心规范正文
4. `10-requirements/` 背景文档
5. `40-dev-loop/` 与 `50-research/` 中仍未补结构字段的文档

排序原因：

- API 文档是当前剩余“部分对齐”项中最直接的高频参考入口，补齐后收益最高。
- `20-specs/` 是执行基线，应尽快与模板完全对齐。
- `10-requirements/`、`40-dev-loop/`、`50-research/` 更适合在不打断当前使用的前提下渐进补齐。

## 五、执行建议

- 每次只处理一个清晰主题，例如：
  - 一次只补治理文档
  - 一次只补 API 文档
  - 一次只补 `20-specs/` 正文
- 每轮补齐后，更新本清单中的状态，避免重复排查。
- 若某文档语义上已经具备类似内容，可优先最小化整理为标准章节，而不是大幅重写正文。

## 与其他文档的关系

- `docs/00-governance/document-template-spec.md`
  - 定义模板字段与标准章节结构。
- `docs/00-governance/document-lifecycle.md`
  - 定义文档状态口径，指导哪些文档应持续维护、哪些应归档。
- `docs/00-governance/document-change-process.md`
  - 定义后续分批补齐时的执行流程和提交要求。
- `docs/00-governance/document-review-checklist.md`
  - 定义补齐结构字段后的评审检查项。

# 文档目录说明

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本文档作为 `docs/` 目录的总入口，用于统一说明文档分层、建议阅读顺序和使用原则，帮助读者从仓库总入口进入具体治理、规范、接口、研发闭环和调研文档。

## 适用范围

- 适用于需要快速理解 `docs/` 整体结构的读者。
- 适用于需要判断某份文档应该放在哪一层、先读哪一层的协作场景。
- 不替代各目录下的具体入口文档和规范正文。

## 当前定位

- 本文档是 `docs/` 目录的总导航，不替代 `00-governance/` 中的治理规则。
- 后续拆任务、建仓库、写代码和接入 CI 时，执行仍以 `20-specs/` 为准。
- 当目录规则、变更流程、状态规则存在细节问题时，应分别以下游治理文档为准。

## 目录结构

- `00-governance/`
  - 文档治理、项目状态、快速开始、目录规范、变更流程、生命周期、归属责任、评审清单、模板规范、模板对齐复查、模板维护规则和 spec/skill 映射
  - 适合先看这组，理解文档体系本身怎么组织
- `10-requirements/`
  - 需求背景、产品讨论、方案草案和立项上下文
  - 适合快速了解项目目标、玩法和边界
- `20-specs/`
  - 执行规范、实施约束、验收基线和工程协作标准
  - 适合作为拆任务、建仓库、写代码和接入 CI 的直接输入
- `30-api/`
  - 接口总览、权限矩阵、错误码、接口样例和后续 OpenAPI 入口
  - 适合开始做服务实现前统一接口视图
- `40-dev-loop/`
  - AI Coding、Loop Engineering、门禁和日志 schema
  - 适合做流程治理、门禁建设和持续改进
- `50-research/`
  - 技术选型、方案比较和历史决策依据
  - 适合做引擎、后端和基础设施决策参考

## 建议阅读顺序

1. `00-governance/document-directory-spec.md`
2. `00-governance/document-change-process.md`
3. `00-governance/document-lifecycle.md`
4. `00-governance/document-template-spec.md`
5. `00-governance/document-template-alignment-checklist.md`
6. `00-governance/document-template-maintenance.md`
7. `00-governance/document-ownership.md`
8. `00-governance/document-review-checklist.md`
9. `00-governance/document-map.md`
10. `00-governance/project-status.md`
11. `00-governance/quick-start.md`
12. `30-api/api-overview.md`
13. `30-api/api-permissions.md`
14. `30-api/api-error-codes.md`
15. `30-api/api-examples-vote.md`
16. `00-governance/spec-skill-mapping.md`
17. `10-requirements/open-world-ai-game-prd.md`
18. `10-requirements/需求概述.md`
19. `10-requirements/功能设计.md`
20. `10-requirements/技术方案.md`
21. `40-dev-loop/ai-coding-game-dev-loop-plan.md`
22. `40-dev-loop/loop-engineering-plan.md`
23. `50-research/stack-research-ai-game-dev.md`
24. `50-research/service-stack-comparison.md`
25. `20-specs/README.md`

## 使用原则

- 后续拆任务、建仓库、写代码时，统一以 `20-specs/` 为执行基线。
- `10-requirements/` 保留需求背景和高层方案，不再重复维护实现细节。
- `30-api/` 承担接口参考索引，不替代 `20-specs/` 的后端规范。
- `40-dev-loop/` 保留研发治理、门禁和 AI Coding 流程设计。
- `50-research/` 保留技术选型依据和历史决策背景。

## 与其他文档的关系

- `README.md`
  - 作为仓库根入口，负责引导读者进入 `docs/` 总导航。
- `00-governance/document-directory-spec.md`
  - 定义目录分层与新增文档落位规则。
- `00-governance/document-change-process.md`
  - 定义新增、修订、迁移和删除时应遵循的流程。
- `00-governance/document-map.md`
  - 定义文档体系的权威关系、保留策略与整理判断。
- `00-governance/document-template-alignment-checklist.md`
  - 记录当前模板对齐结果和后续复查状态。
- `00-governance/document-template-maintenance.md`
  - 定义模板全量对齐完成后，后续新增和改写应如何持续保持结构一致。

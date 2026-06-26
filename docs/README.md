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
- 本文档负责提供“全量目录导航”和“按层阅读索引”；最小阅读路径与最小实施顺序以 `00-governance/quick-start.md` 为准。
- 后续拆任务、建仓库、写代码和接入 CI 时，执行仍以 `20-specs/` 为准；目录、流程和状态细节以下游治理文档为准。

## 目录结构

- `00-governance/`
  - 文档治理、阶段总结、项目状态、快速开始、目录规范、变更流程、生命周期、归属责任、评审清单、模板规范、模板对齐复查、模板维护规则和 spec/skill 映射
  - 适合先看这组，理解文档体系本身怎么组织
- `10-requirements/`
  - 需求背景、产品讨论、方案草案和立项上下文
  - 适合快速了解项目目标、玩法和边界
- `20-specs/`
  - 执行规范、实施约束、验收基线和工程协作标准
  - 适合作为拆任务、建仓库、写代码和接入 CI 的直接输入
- `30-api/`
  - 接口总览、OpenAPI 草案入口、权限矩阵、错误码和接口样例
  - 适合开始做服务实现前统一接口视图
- `40-dev-loop/`
  - AI Coding、Loop Engineering、门禁和日志 schema
  - 适合做流程治理、门禁建设和持续改进
- `50-research/`
  - 技术选型、方案比较和历史决策依据
  - 适合做引擎、后端和基础设施决策参考

## 建议阅读顺序

以下顺序用于按层浏览完整文档体系；如果你只需要最小阅读路径和最小实施顺序，优先查看 `00-governance/quick-start.md`。

1. `00-governance/document-directory-spec.md`
2. `00-governance/document-change-process.md`
3. `00-governance/document-lifecycle.md`
4. `00-governance/document-map.md`
5. `00-governance/project-status.md`
6. `00-governance/quick-start.md`
7. `20-specs/README.md`
8. `30-api/api-overview.md`
9. `30-api/openapi-draft.md`
10. `10-requirements/需求概述.md`
11. `40-dev-loop/loop-engineering-plan.md`
12. `50-research/stack-research-ai-game-dev.md`

## 使用原则

- 后续拆任务、建仓库、写代码时，统一以 `20-specs/` 为执行基线。
- `10-requirements/` 保留需求背景和高层方案，不再重复维护实现细节。
- `30-api/` 承担接口参考索引，不替代 `20-specs/` 的后端规范。
- `40-dev-loop/` 保留研发治理、门禁和 AI Coding 流程设计。
- `50-research/` 保留技术选型依据和历史决策背景。

## 与其他文档的关系

- `README.md`
  - 仓库根入口。
- `00-governance/document-directory-spec.md`
  - 目录分层与落位规则。
- `00-governance/document-map.md`
  - 文档角色与权威关系。
- `00-governance/quick-start.md`
  - 最小阅读路径与最小实施顺序。
- `00-governance/document-template-maintenance.md`
  - 模板持续维护规则。

# 仓库入口说明

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本文档作为仓库根入口，帮助读者快速理解当前仓库的定位、`docs/` 目录分层以及建议阅读路径，避免初次进入仓库时不知道应该从哪一层文档开始。

## 当前定位

- 当前仓库是文档与规范仓库，不是可直接运行的业务工程仓库。
- 根 `README.md` 负责提供最外层导航，详细阅读顺序和治理规则以 `docs/README.md` 及 `docs/00-governance/` 下的文档为准。
- 后续进入拆任务、建仓库、写代码和接入 CI 时，执行基线以 `docs/20-specs/` 为准。

## 目录结构

- `docs/00-governance/`
  - 文档治理、项目状态、快速开始、目录规范、变更流程、生命周期、归属责任、评审清单、模板规范和 spec/skill 映射
- `docs/10-requirements/`
  - 需求背景、产品讨论、方案草案和立项上下文
- `docs/20-specs/`
  - 执行规范、实施约束、验收基线和工程协作标准
- `docs/30-api/`
  - 接口总览、权限矩阵、错误码、接口样例和后续 OpenAPI 入口
- `docs/40-dev-loop/`
  - AI Coding、Loop Engineering、门禁和日志 schema
- `docs/50-research/`
  - 技术选型、方案比较和历史决策依据

## 建议阅读顺序

1. `docs/README.md`
2. `docs/00-governance/document-directory-spec.md`
3. `docs/00-governance/document-change-process.md`
4. `docs/00-governance/document-lifecycle.md`
5. `docs/00-governance/document-template-spec.md`
6. `docs/00-governance/document-map.md`
7. `docs/00-governance/project-status.md`
8. `docs/00-governance/quick-start.md`
9. `docs/20-specs/README.md`
10. `docs/30-api/api-overview.md`

## 与其他文档的关系

- `docs/README.md`
  - 作为 `docs/` 目录的详细入口，提供更完整的目录说明和阅读顺序。
- `docs/00-governance/project-status.md`
  - 说明当前仓库阶段、已具备资产和未落地部分。
- `docs/20-specs/README.md`
  - 作为执行规范入口，承接后续实施所需的核心约束。
- `docs/00-governance/document-map.md`
  - 说明整套文档体系的分层、权威关系和保留策略。

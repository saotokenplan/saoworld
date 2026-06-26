# 文档目录说明

## 目录结构

- `00-governance/`
  - 文档治理、项目状态、快速开始、目录规范和 spec/skill 映射
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
2. `00-governance/document-map.md`
3. `00-governance/project-status.md`
4. `00-governance/quick-start.md`
5. `30-api/api-overview.md`
6. `30-api/api-permissions.md`
7. `30-api/api-error-codes.md`
8. `30-api/api-examples-vote.md`
9. `00-governance/spec-skill-mapping.md`
10. `10-requirements/open-world-ai-game-prd.md`
11. `10-requirements/需求概述.md`
12. `10-requirements/功能设计.md`
13. `10-requirements/技术方案.md`
14. `40-dev-loop/ai-coding-game-dev-loop-plan.md`
15. `40-dev-loop/loop-engineering-plan.md`
16. `50-research/stack-research-ai-game-dev.md`
17. `50-research/service-stack-comparison.md`
18. `20-specs/README.md`

## 使用原则

- 后续拆任务、建仓库、写代码时，统一以 `20-specs/` 为执行基线。
- `10-requirements/` 保留需求背景和高层方案，不再重复维护实现细节。
- `30-api/` 承担接口参考索引，不替代 `20-specs/` 的后端规范。
- `40-dev-loop/` 保留研发治理、门禁和 AI Coding 流程设计。
- `50-research/` 保留技术选型依据和历史决策背景。

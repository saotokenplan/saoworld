# 文档目录说明

## 目录结构

- `document-map.md`
  - 文档地图、权威关系与整理建议
  - 适合开始维护文档前先看，明确哪类文档承担什么职责
- `spec-skill-mapping.md`
  - `specs/` 与 `.trae/skills/` 的上下游映射
  - 适合维护 Skill 或调整规范时查阅
- `requirements/`
  - 游戏需求与方案拆分文档
  - 适合先看这组，快速了解项目目标、功能和技术边界
- `dev-loop/`
  - AI Coding 研发闭环、Loop Engineering 与门禁配套文件
  - 适合做工程落地和仓库初始化时使用
- `research/`
  - 技术选型与服务端技术栈调研
  - 适合做引擎、后端和基础设施决策时参考
- `specs/`
  - 基于前面讨论继续细化出的详细规范包
  - 适合直接作为拆任务、建仓库和写代码的输入

## 建议阅读顺序

1. `document-map.md`
2. `spec-skill-mapping.md`
3. `requirements/open-world-ai-game-prd.md`
4. `requirements/需求概述.md`
5. `requirements/功能设计.md`
6. `requirements/技术方案.md`
7. `dev-loop/ai-coding-game-dev-loop-plan.md`
8. `dev-loop/loop-engineering-plan.md`
9. `research/stack-research-ai-game-dev.md`
10. `research/service-stack-comparison.md`
11. `specs/README.md`

## 使用原则

- 后续拆任务、建仓库、写代码时，统一以 `specs/` 为执行基线。
- `requirements/` 保留需求背景和高层方案，不再重复维护实现细节。
- `dev-loop/` 保留研发治理、门禁和 AI Coding 流程设计。
- `research/` 保留技术选型依据和历史决策背景。

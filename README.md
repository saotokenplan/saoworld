# 仓库入口说明

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本文档作为仓库根入口，帮助读者快速理解当前仓库的定位、`docs/` 目录分层以及建议阅读路径，避免初次进入仓库时不知道应该从哪一层文档开始。

## 当前定位

- 当前仓库是面向开放世界 AI 游戏项目的单仓工程，已经同时包含文档、客户端、后端服务、异步任务、工具脚本和基础设施目录。
- 当前阶段为“Sprint 9 公测准备收尾 / 灰度发布前校准”；项目重点已从持续补功能转向发布闭环与真实环境验证。
- 根 `README.md` 负责提供最外层导航；详细阅读顺序以 `docs/README.md` 为准，项目现状以 `docs/00-governance/project-status.md` 为准，执行基线以 `docs/20-specs/` 为准。

## 目录结构

- `game/`
  - Godot 4 客户端工程与场景、脚本、测试
- `services/`
  - 八个后端微服务与各自 README、代码和测试
- `workers/`
  - 异步任务 Worker 与任务执行入口
- `tools/`
  - 工具脚本、校验器、压测工具、Agent 模块与 Git hooks
- `infra/`
  - Docker Compose 与部署相关配置
- `telemetry/`
  - 遥测、SLO、日志与告警定义
- `docs/00-governance/`
  - 文档治理、项目状态、快速开始、目录规范、变更流程、生命周期、归属责任、评审清单、模板规范、模板对齐复查、模板维护规则和 spec/skill 映射
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

1. `docs/00-governance/project-status.md`
2. `docs/README.md`
3. `docs/00-governance/document-map.md`
4. `docs/00-governance/quick-start.md`
5. `docs/20-specs/README.md`
6. `docs/30-api/api-overview.md`

## 与其他文档的关系

- `docs/README.md`
  - `docs/` 总导航。
- `docs/00-governance/project-status.md`
  - 当前阶段与资产完备度。
- `docs/20-specs/README.md`
  - 执行规范目录入口。
- `docs/00-governance/document-map.md`
  - 文档分层与权威关系。

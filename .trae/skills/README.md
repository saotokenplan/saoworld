# 游戏 AI 闭环技能包

## 目的

这一组 skills 基于当前项目的需求文档、技术方案、Loop Engineering 方案和详细规范提炼而来，目标是把“需求整理、Godot 客户端开发、内容生成、审核、后端实现、门禁优化、发布回滚”拆成可独立调用的技能。

## 技能列表

- `requirement-package-builder`
  - 把产品目标整理成 `spec.md`、`acceptance.md`、`risk.md`、`tasks.md`
- `godot-gameplay-implementer`
  - 负责 Godot 4 + typed GDScript 的玩法实现与客户端测试
- `world-content-generator`
  - 负责结构化生成 NPC、任务、聚落和事件草案
- `content-review-gate`
  - 负责一致性、数值、安全和重复度审核
- `backend-service-builder`
  - 负责 FastAPI、PostgreSQL、Celery 相关服务实现
- `loop-gate-optimizer`
  - 负责从日志、CI 与事故中提炼 Gate Improvement / Rule Improvement
- `release-package-operator`
  - 负责内容包打包、灰度、发布、回滚与发布摘要

## 建议调用顺序

1. `requirement-package-builder`
2. `backend-service-builder` 与 `godot-gameplay-implementer`
3. `world-content-generator`
4. `content-review-gate`
5. `release-package-operator`
6. `loop-gate-optimizer`

## 说明

- 这些文件是面向当前项目的技能草案，不是通用平台内置技能。
- 每个 skill 都尽量只承担一个明确职责，避免单个 skill 同时做规划、编码、审核和发布。
- 每个 `SKILL.md` 应显式标注“规范来源”，并与 `docs/00-governance/spec-skill-mapping.md` 保持一致。
- 如 Skill 与 `docs/20-specs/` 冲突，以 `docs/20-specs/` 为准。

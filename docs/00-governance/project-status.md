# 项目状态

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本文档用于统一说明当前项目处于什么阶段、哪些内容已经确定、哪些内容仍待确认，以及从文档规划走向工程实施前还缺什么。

## 当前阶段

- 当前阶段：文档规划阶段
- 当前形态：以需求、规范、研发闭环和技术调研文档为主
- 当前目标：先统一执行规范，再进入工程初始化与最小落地

## 当前结论

- 该仓库当前不是已落地的业务工程仓库，而是面向后续实施的文档与规范仓库。
- 后续进入拆任务、建仓库、写代码和接入 CI 时，统一以 `docs/20-specs/` 为执行基线。
- `.trae/skills/` 已经建立了与 `20-specs/` 的映射关系，但 Skill 属于执行层，不替代规范层。

## 已确定事项

### 产品方向

- 产品形态已明确为“大型开放式、玩家投票驱动、AI 持续生成内容”的在线游戏。
- 核心闭环已明确为“探索 -> 参与 -> 投票 -> 世界更新 -> 再探索”。
- AI 的职责边界已明确：负责可变内容生成，不负责主线终局、核心经济和底层战斗规则。
- MVP 范围已明确：首期包含 `1` 个核心常驻区域、`1` 个扩展区域、`1` 条主线骨架、`3` 个候选剧情方向，以及投票、生成、审核、灰度和回滚的完整链路。

### 规范分层

- `00-governance/` 定位为文档治理、项目状态和使用入口。
- `10-requirements/` 定位为需求背景、方案讨论和立项上下文。
- `20-specs/` 定位为执行规范和最终基线。
- `30-api/` 定位为接口参考、权限矩阵和错误码索引。
- `40-dev-loop/` 定位为研发治理、门禁和 AI Coding 闭环设计。
- `50-research/` 定位为技术选型和历史决策依据。

### 技术方向

- 客户端方向已收敛为 Godot 4 + typed GDScript。
- 服务端方向已收敛为 Python、FastAPI、PostgreSQL、Celery。
- 后端服务拆分方向已明确，包括网关、玩家、世界、投票、生成、审核、内容和运营等核心服务。
- 发布策略方向已明确为内容包驱动、优先灰度、支持版本归档和快速回滚。

### 文档治理

- 已明确 `20-specs/` 优先于 `10-requirements/`。
- 已完成 `20-specs/` 与 `.trae/skills/` 的映射文档。
- 已在 `10-requirements/` 文档顶部补充“如与 `20-specs/` 冲突，以 `20-specs/` 为准”的声明。
- 已在各 `SKILL.md` 中补充“规范来源”。
- 已建立文档目录规范，并完成 `docs/` 目录按层重组。
- 已补齐 API 总览、权限矩阵和错误码三类接口参考文档。

## 已准备好的资产

- 产品规范：
  - `docs/20-specs/product-spec.md`
- 内容生成规范：
  - `docs/20-specs/content-generation-spec.md`
- 后端与数据规范：
  - `docs/20-specs/backend-data-spec.md`
- Agent 与闭环规范：
  - `docs/20-specs/agent-loop-spec.md`
- 工程协作规范：
  - `docs/20-specs/engineering-conventions.md`
- 文档治理辅助材料：
  - `docs/00-governance/document-directory-spec.md`
  - `docs/00-governance/document-change-process.md`
  - `docs/00-governance/document-lifecycle.md`
  - `docs/00-governance/document-ownership.md`
  - `docs/00-governance/document-review-checklist.md`
  - `docs/00-governance/document-template-spec.md`
  - `docs/00-governance/document-map.md`
  - `docs/00-governance/quick-start.md`
  - `docs/00-governance/spec-skill-mapping.md`
- 接口参考材料：
  - `docs/30-api/api-overview.md`
  - `docs/30-api/api-permissions.md`
  - `docs/30-api/api-error-codes.md`

## 未确定事项

### 产品侧未定

- 世界观根设定的具体文本版本尚未单独沉淀为正式世界观文档。
- 首期区域、阵营、关键 NPC、章节切分仍缺少具体实例化内容包。
- 客户端交互稿、界面流和关键页面信息结构尚未文档化。

### 技术侧未定

- OpenAPI 文档尚未建立，接口目前只有方向性定义，缺少请求响应样例和错误码索引。
- 数据库 ER 图、字段字典、枚举说明和迁移策略尚未补齐。
- 任务队列、事件总线、中间件、部署方式等细节仍停留在方向层，未形成工程实施方案。

### 工程侧未定

- 当前仓库是否继续作为未来主仓库，还是仅保留为上游文档仓库，尚未明确。
- 单仓、多仓或混合仓的实际实施路径尚未最终确认。
- CI 规则、测试入口、发布流水线和环境配置文件尚未建立。

## 尚未落地的工程资产

- `game/` 客户端工程目录尚不存在。
- `services/` 后端服务目录尚不存在。
- `workers/`、`infra/`、`tools/`、`telemetry/` 等目标态目录尚不存在。
- 可运行代码、测试套件、部署脚本和真实 CI 配置尚不存在。
- 可直接执行的工程启动说明、环境依赖和本地运行命令尚不存在。

## 当前主要风险

- 文档与未来工程结构存在落差，如果不先补状态说明，容易让人误判项目已进入开发阶段。
- `10-requirements/` 与 `20-specs/` 仍有一定内容重叠，后续若继续双向修改，容易再次漂移。
- `40-dev-loop/` 中部分设计偏目标态，若不裁剪就直接照搬，实施成本会偏高。
- `engineering-conventions.md` 描述的是目标态仓库结构，与当前仓库现状尚未完全对齐。

## 下一阶段建议

1. 先确认仓库策略：当前仓库是继续演进为主仓库，还是仅作为上游文档仓库。
2. 补 `docs/30-api/` 下的请求响应样例或 OpenAPI 草案。
3. 选定首个最小落地目标，例如先做投票链路、内容生成链路或最小客户端演示。
4. 基于最小目标生成第一版需求包，再进入代码仓初始化。

## 进入实施前的建议门槛

- 产品边界和 MVP 范围不再频繁变更。
- 首个落地目标明确到单条主线能力。
- 至少补齐接口样例、最小任务拆分和工程初始化说明。
- 确认是沿当前仓库继续扩展，还是拆出独立工程仓库。

# 文档地图

## 目的

本文档用于统一当前仓库的文档分层、权威关系、保留策略与整理建议，减少重复维护和后续落地时的理解偏差。

## 当前判断

- 当前仓库属于“文档规划阶段”。
- 当前资产以需求、规范、研发闭环和技术调研为主。
- 后续如果进入工程实施，`20-specs/` 应作为主要执行输入。

## 文档权威关系

- `20-specs/`
  - 角色：执行规范
  - 用途：后续拆任务、建仓库、写代码、接入 CI 的主要依据
  - 权威级别：最高
- `10-requirements/`
  - 角色：需求背景与方案说明
  - 用途：帮助理解项目目标、玩法和技术边界
  - 权威级别：次级，如与 `20-specs/` 冲突，以 `20-specs/` 为准
- `40-dev-loop/`
  - 角色：研发治理与 AI Coding 流程设计
  - 用途：指导门禁、日志、Issue、回滚和多 Agent 协作
  - 权威级别：流程参考，需结合当前工程现状裁剪使用
- `50-research/`
  - 角色：技术选型依据
  - 用途：保留引擎、后端、基础设施的决策背景
  - 权威级别：归档参考，不直接作为实施规范

## 文档整理表

| 文件 | 作用 | 当前状态 | 是否保留 | 整理建议 |
|---|---|---|---|---|
| `README.md` | 仓库总入口，说明文档目录与阅读顺序 | 可用，但更像目录说明，缺项目现状与启动指引 | 保留 | 补充仓库定位、当前阶段、下一步行动、如何开始 |
| `docs/README.md` | `docs` 总导航，说明新目录规范与阅读顺序 | 结构清晰，是当前较好的文档入口 | 保留 | 明确执行以 `20-specs/` 为准，其他为背景、调研、治理参考 |
| `docs/10-requirements/open-world-ai-game-prd.md` | 完整 PRD，覆盖目标、玩法、MVP、验收 | 内容最完整，但与需求摘要和执行规范重叠明显 | 有条件保留 | 保留为立项 PRD，删除与 `20-specs/` 重复的执行细节，并标注非权威 |
| `docs/10-requirements/需求概述.md` | 高层摘要，便于快速理解项目 | 简洁清楚，但信息密度有限 | 保留 | 定位为一页式摘要，避免继续堆叠细节 |
| `docs/10-requirements/功能设计.md` | 从产品和策划视角描述玩法闭环和模块 | 有价值，但与 `product-spec.md` 局部重复 | 保留 | 聚焦玩法设计与体验，不再承载接口、数据、流程约束 |
| `docs/10-requirements/技术方案.md` | 高层技术架构和链路方案 | 适合方案讨论，但还不是实施文档 | 保留 | 聚焦架构选型与总体方案，详细约束统一下沉到 `20-specs/` |
| `docs/20-specs/README.md` | 详细规范入口，说明执行顺序 | 定位明确，承上启下 | 保留 | 明确写清后续拆任务、建仓、写代码统一以 `20-specs/` 为准 |
| `docs/20-specs/product-spec.md` | 产品边界、玩法闭环、投票治理、MVP、验收 | 成熟度高，是产品执行基线之一 | 强烈保留 | 作为产品唯一执行基线，其他需求文档引用它而不是重复定义 |
| `docs/20-specs/content-generation-spec.md` | AI 内容生成输入输出、审核规则、生命周期 | 落地性较强，对 AI 生成约束有实际价值 | 强烈保留 | 补充 schema 示例、输入输出样例和失败案例 |
| `docs/20-specs/backend-data-spec.md` | 服务边界、数据模型、API 方向、事件与异步任务 | 成熟度高，但仍缺 API 细节与字段字典 | 强烈保留 | 补 OpenAPI、错误码表、枚举表、ER 图和迁移策略 |
| `docs/20-specs/agent-loop-spec.md` | Agent 角色、需求包、门禁、日志、回滚流程 | 体系完整，但偏治理目标态 | 保留 | 明确哪些是当前阶段必须做，哪些是演进目标 |
| `docs/20-specs/engineering-conventions.md` | 仓库结构、命名、配置、测试、发布协作规范 | 很有价值，但与当前仓库现状尚未完全对齐 | 保留 | 增加当前仓库适配版，避免直接引用未来目录造成误导 |
| `docs/40-dev-loop/ai-coding-game-dev-loop-plan.md` | AI-first 游戏研发流程与多 Agent 编排 | 方法论完整，但依赖大量尚未存在资产 | 保留 | 定位为演进路线图，补充当前可执行最小版本 |
| `docs/40-dev-loop/loop-engineering-plan.md` | Loop Engineering 总方案、门禁、指标体系 | 治理设计较完整，但偏抽象 | 保留 | 与 `agent-loop-spec.md` 切分职责，避免双份描述同一流程 |
| `docs/40-dev-loop/issue-templates-loop-engineering.md` | Gate 和 Rule 改进的 Issue 模板 | 实用性强，可直接复用 | 保留 | 后续迁移到真实工程仓库的 Issue Template 目录 |
| `docs/40-dev-loop/log-schemas-loop-engineering.md` | 定义 session、CI、事故日志 schema | 结构清晰，适合作为观测标准 | 保留 | 补字段示例和日志采集入口，避免只停留在格式定义 |
| `docs/40-dev-loop/gate_registry.yaml` | 门禁注册表，记录成本、风险和生命周期 | 实用，但引用了当前仓库不存在的脚本和路径 | 保留 | 标注为目标态注册表，并补当前可用 gate 列表 |
| `docs/50-research/stack-research-ai-game-dev.md` | 引擎与整体技术栈选型论证 | 决策依据充分，但不适合做开发入口 | 保留 | 保留为调研归档，不再承载规范性内容 |
| `docs/50-research/service-stack-comparison.md` | 比较 Python、TypeScript、Rust 的服务端职责 | 结论明确，适合辅助技术决策 | 保留 | 保留为历史决策依据，并补最终结论摘要 |

## 建议维护方式

- 新增文档时，先判断它属于 `00-governance/`、`10-requirements/`、`20-specs/`、`30-api/`、`40-dev-loop/`、`50-research/` 中哪一层。
- 涉及执行约束的新增内容，优先进入 `20-specs/`，避免散落到背景文档。
- `10-requirements/` 中的文档不再重复维护接口、表结构、事件流等实现细节。
- `40-dev-loop/` 中的流程性文档，需要标记“当前可执行”和“目标态演进”边界。
- `50-research/` 中的调研文档只保留结论和依据，不承担实施规范角色。

## 已补齐的治理与参考文档

- `docs/00-governance/document-directory-spec.md`
  - 定义 `docs/` 的目录分层、命名方式和新增文档落位规则
- `docs/00-governance/document-change-process.md`
  - 定义文档新增、修订、迁移、重命名、删除和引用同步流程
- `docs/00-governance/spec-skill-mapping.md`
  - 统一维护 `20-specs/` 与 `.trae/skills/` 的上游下游关系
- `docs/00-governance/project-status.md`
  - 说明仓库当前处于什么阶段，以及哪些资产已经具备
- `docs/00-governance/quick-start.md`
  - 说明当前仓库怎么使用，以及从文档规划走向实施的最小路径
- `docs/30-api/api-overview.md`
  - 统一接口清单、服务边界、异步任务和事件索引
- `docs/30-api/api-permissions.md`
  - 统一接口角色、权限矩阵、敏感操作和审计要求
- `docs/30-api/api-error-codes.md`
  - 统一接口错误码、状态冲突约束和建议 HTTP 状态码

## 后续动作建议

1. 在 `README.md` 和 `docs/README.md` 中加入本文档入口。
2. 在 `10-requirements/` 各文档顶部增加说明：如与 `20-specs/` 冲突，以 `20-specs/` 为准。
3. 优先补接口样例、OpenAPI 草案和工程初始化说明，为工程实施做准备。

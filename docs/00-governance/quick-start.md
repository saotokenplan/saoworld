# Quick Start

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本文档用于帮助读者快速理解当前仓库怎么使用，以及当项目准备从文档规划阶段进入工程实施阶段时，应该先做哪些事。

## 适用范围

- 适用于第一次接触本仓库、需要快速上手阅读路径的读者。
- 适用于准备从文档阅读进入最小实施动作的协作场景。
- 不替代项目状态说明、目录规范或具体执行规范正文。

## 当前定位

- 本文档是“怎么开始使用这套文档”的操作入口。
- 本文档回答“先看什么、先做什么”，不替代 `20-specs/` 中的具体执行约束。
- 当需要判断项目成熟度或文档权威关系时，应分别查看状态说明和文档地图。

## 先说明当前状态

- 当前仓库是文档与规范仓库，不是可直接运行的业务工程仓库。
- 当前仓库里还没有 `game/`、`services/`、`workers/` 等目标态工程目录。
- 当前最适合做的事情是阅读、收敛规范、确定最小落地目标，而不是直接执行启动命令。

如果你想先判断项目目前做到哪一步，建议先看：

1. `docs/00-governance/document-map.md`
2. `docs/00-governance/project-status.md`
3. `docs/00-governance/document-lifecycle.md`
4. `docs/00-governance/document-template-spec.md`
5. `docs/00-governance/document-template-alignment-checklist.md`
6. `docs/00-governance/document-template-maintenance.md`
7. `docs/20-specs/README.md`

## 5 分钟上手

### 如果你是第一次看这个仓库

按下面顺序阅读：

1. `docs/00-governance/document-map.md`
   - 理解文档分层、权威关系和维护原则
2. `docs/00-governance/project-status.md`
   - 判断项目当前阶段、已确定事项和未落地资产
3. `docs/00-governance/document-lifecycle.md`
   - 理解哪些文档是草稿、当前生效、待废弃或已归档
4. `docs/00-governance/document-template-spec.md`
   - 理解后续新增治理文档、规范文档和 API 文档时应采用的标准章节结构
5. `docs/00-governance/document-template-alignment-checklist.md`
   - 确认当前文档体系已经完成模板对齐，以及后续复查应从哪里开始
6. `docs/00-governance/document-template-maintenance.md`
   - 理解模板全量对齐完成后，后续新增和改写时应如何持续保持
7. `docs/20-specs/README.md`
   - 进入执行规范入口
8. `docs/20-specs/product-spec.md`
   - 理解产品边界、MVP 和验收口径
9. `docs/20-specs/backend-data-spec.md`
   - 理解后端服务、数据模型和接口方向
10. `docs/00-governance/spec-skill-mapping.md`
   - 理解 `20-specs/` 和 `.trae/skills/` 的关系

### 如果你准备开始实施

按下面顺序推进：

1. 明确当前仓库角色
   - 先决定本仓库是否继续演进为主仓库，还是只保留为上游文档仓库
2. 选一个最小落地目标
   - 推荐只选一条主线能力，例如：
   - 最小投票链路
   - 最小内容生成链路
   - 最小客户端演示链路
3. 以 `docs/20-specs/` 为基线整理需求包
   - 背景和讨论看 `10-requirements/`
   - 执行边界和验收以 `20-specs/` 为准
4. 再决定工程初始化方式
   - 单仓
   - 多仓
   - 文档仓 + 工程仓分离

## 当前推荐阅读顺序

### 业务与产品

- `docs/10-requirements/open-world-ai-game-prd.md`
- `docs/10-requirements/需求概述.md`
- `docs/20-specs/product-spec.md`

### 技术与实施

- `docs/10-requirements/技术方案.md`
- `docs/20-specs/backend-data-spec.md`
- `docs/20-specs/engineering-conventions.md`

### 治理与执行

- `docs/00-governance/spec-skill-mapping.md`
- `docs/20-specs/agent-loop-spec.md`
- `docs/40-dev-loop/loop-engineering-plan.md`

## 当前能做的事

- 梳理和统一需求边界
- 基于 `20-specs/` 拆分首个最小落地目标
- 明确未来仓库结构与实施策略
- 维护 `.trae/skills/` 使其和 `20-specs/` 保持一致
- 补充接口总览、启动说明和任务拆分文档

## 当前不能直接做的事

- 不能直接启动客户端，因为还没有实际 Godot 工程
- 不能直接启动服务端，因为还没有真实服务代码
- 不能直接运行 CI，因为还没有真实流水线和测试套件
- 不能直接做部署验证，因为还没有基础设施配置和部署脚本

## 从文档到实施的最小路径

1. 确认首个落地目标
2. 从 `docs/20-specs/` 中抽出与该目标直接相关的规范
3. 生成第一版需求包
4. 确认仓库组织方式
5. 初始化最小工程骨架
6. 建立第一条测试和回滚链路

## 开工前检查清单

- 是否已经明确首个最小落地目标
- 是否已经确认以 `docs/20-specs/` 为执行基线
- 是否已经确认当前仓库角色
- 是否已经确认工程是单仓还是多仓
- 是否已经补充接口总览或最小任务拆分

## 后续建议补充

- `docs/30-api/api-examples-vote.md`
  - 统一投票链路的请求响应样例和状态说明
- `docs/30-api/openapi-draft.md`
  - 作为后续 OpenAPI 文档的集中草案入口
- 首个需求包目录
  - 例如 `docs/packages/first-slice/`
- 工程初始化说明
  - 如果后续开始建仓，应补充实际依赖安装、运行命令和目录说明

## 与其他文档的关系

- `docs/00-governance/project-status.md`
  - 说明当前阶段、已准备资产和未落地部分。
- `docs/00-governance/document-map.md`
  - 说明整套文档体系的分层与权威关系。
- `docs/00-governance/document-lifecycle.md`
  - 说明当前哪些文档处于可执行、草稿或归档状态。
- `docs/00-governance/document-template-maintenance.md`
  - 说明模板全量对齐完成后，后续新增和改写时应如何持续保持结构一致。
- `docs/20-specs/README.md`
  - 作为执行规范入口，承接阅读后进入实施的下一步。

# Quick Start

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本文档用于帮助读者快速理解当前仓库怎么使用，以及当项目处于实施准备阶段并准备进入工程实施时，应该先做哪些事。

## 适用范围

- 适用于第一次接触本仓库、需要快速上手阅读路径的读者。
- 适用于准备从文档阅读进入最小实施动作的协作场景。
- 不替代项目状态说明、目录规范或具体执行规范正文。

## 当前定位

- 本文档是“怎么开始使用这套文档”的操作入口。
- 本文档回答“先看什么、先做什么”，不替代 `20-specs/` 中的具体执行约束。
- 本文档只保留最小阅读路径和最小实施顺序；完整目录导航看 `docs/README.md`。
- 项目成熟度看 `docs/00-governance/project-status.md`，文档权威关系看 `docs/00-governance/document-map.md`。

## 先说明当前状态

- 当前仓库已经是单仓工程，包含 `docs/`、`game/`、`services/`、`workers/`、`tools/`、`infra/` 和 `telemetry/` 等目录。
- 当前阶段不是“从零决定要不要开工”，而是“核心研发链路已成型，正在推进灰度发布闭环与真实环境验证”。
- 当前最适合做的事情是先判断自己要做的是阅读规范、治理文档、运行服务、补验证还是推进发布，而不是默认把仓库视为纯文档仓。

如果你想先判断项目目前做到哪一步，优先看 `docs/00-governance/document-map.md`、`docs/00-governance/project-status.md` 和 `docs/20-specs/README.md`。

## 5 分钟上手

### 如果你是第一次看这个仓库

按下面顺序阅读：

1. `docs/00-governance/document-map.md`
   - 理解文档分层、权威关系和维护原则
2. `docs/00-governance/project-status.md`
   - 判断项目当前阶段、已确定事项和未落地资产
3. `docs/20-specs/README.md`
   - 进入执行规范目录入口
4. `docs/20-specs/product-spec.md`
   - 理解产品边界、MVP 和验收口径
5. `docs/20-specs/backend-data-spec.md`
   - 理解后端服务、数据模型和接口方向
6. `docs/00-governance/spec-skill-mapping.md`
   - 理解 `20-specs/` 和 `.trae/skills/` 的关系

### 如果你准备开始实施

按下面顺序推进：

1. 先确认当前阶段与阻塞
   - 优先看 `docs/00-governance/project-status.md`，确认是否在做灰度发布、运行时验证或后置治理
2. 再确认本次工作的权威来源
   - 产品与实现基线看 `docs/20-specs/`
   - 接口与权限参考看 `docs/30-api/`
   - 过程治理与 runbook 看 `docs/40-dev-loop/`
3. 按目标选择入口目录
   - 文档治理：从 `docs/00-governance/` 与 `docs/README.md` 开始
   - 服务开发：从 `services/<service>/README.md` 和对应 spec 开始
   - 工具与门禁：从 `tools/README.md` 与 `docs/40-dev-loop/` 开始
   - 本地运行：从 `infra/`、服务 README 和相关 runbook 开始
4. 最后再执行具体实现或验证
   - 优先完成与当前阶段相关的闭环事项，而不是无条件新增高风险功能

## 按主题继续阅读

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
- 基于 `20-specs/` 和 `30-api/` 推进服务实现或验证
- 运行已有服务、工具链与测试
- 推进灰度发布前的运行时验证、迁移验证和回滚演练
- 维护 `.trae/skills/` 使其和 `20-specs/` 保持一致
- 补充接口总览、启动说明和任务拆分文档

## 当前不能直接做的事

- 不能跳过 `docs/20-specs/` 直接把 README 当成正式约束
- 不能忽略灰度发布决策、运行时环境和回滚验证这些当前真实阻塞
- 不能把 `10-requirements/` 或专题阅读包当成新的正式规范源
- 不能在缺少环境条件时把“无法验证”误写成“已经验证完成”

## 从文档到实施的最小实施顺序

1. 确认当前阶段与目标任务
2. 从 `docs/20-specs/` 和 `docs/30-api/` 提取该任务的正式约束
3. 结合对应目录 README 与 runbook 进入实现或验证
4. 更新测试、门禁、文档和回滚说明
5. 回写项目状态或过程层材料

## 开工前检查清单

- 是否已经确认当前任务对应的阶段阻塞与目标
- 是否已经确认以 `docs/20-specs/` 为执行基线
- 是否已经找到对应的服务 README、工具 README 或 runbook
- 是否已经确认需要同步更新哪些入口文档
- 是否已经确认测试、门禁与回滚路径

## 后续建议补充

- `docs/30-api/api-examples-vote.md`
  - 统一投票链路的请求响应样例和状态说明
- `docs/30-api/openapi-draft.md`
  - 作为后续集中整理接口定义和样例收敛的入口文档
- 首个需求包目录
  - 例如 `docs/10-requirements/packages/first-slice/`
- 工程初始化说明
  - 如果后续开始建仓，应补充实际依赖安装、运行命令和目录说明

## 与其他文档的关系

- `docs/00-governance/project-status.md`
  - 当前阶段与资产完备度。
- `docs/00-governance/document-map.md`
  - 文档分层与权威关系。
- `docs/20-specs/README.md`
  - 执行规范目录入口。

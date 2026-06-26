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

- 当前仓库是文档与规范仓库，不是可直接运行的业务工程仓库。
- 当前仓库里还没有 `game/`、`services/`、`workers/` 等目标态工程目录。
- 当前最适合做的事情是阅读、收敛规范、确定首个最小落地目标，而不是直接执行启动命令。

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

1. 明确当前仓库角色
   - 先决定本仓库是否继续演进为主仓库，还是只保留为上游文档仓库
2. 确定首个最小落地目标
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
- 基于 `20-specs/` 拆分首个最小落地目标
- 明确未来仓库结构与实施策略
- 维护 `.trae/skills/` 使其和 `20-specs/` 保持一致
- 补充接口总览、启动说明和任务拆分文档

## 当前不能直接做的事

- 不能直接启动客户端，因为还没有实际 Godot 工程
- 不能直接启动服务端，因为还没有真实服务代码
- 不能直接运行 CI，因为还没有真实流水线和测试套件
- 不能直接做部署验证，因为还没有基础设施配置和部署脚本

## 从文档到实施的最小实施顺序

1. 确认首个最小落地目标
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
  - 作为后续集中整理接口定义和样例收敛的入口文档
- 首个需求包目录
  - 例如 `docs/packages/first-slice/`
- 工程初始化说明
  - 如果后续开始建仓，应补充实际依赖安装、运行命令和目录说明

## 与其他文档的关系

- `docs/00-governance/project-status.md`
  - 当前阶段与资产完备度。
- `docs/00-governance/document-map.md`
  - 文档分层与权威关系。
- `docs/20-specs/README.md`
  - 执行规范目录入口。

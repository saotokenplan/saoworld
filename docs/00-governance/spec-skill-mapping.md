# Spec 与 Skill 映射

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本文档用于明确 `docs/20-specs/` 与 `.trae/skills/` 的上下游关系，避免把 Skill 当成唯一规范，也避免规范更新后 Skill 漂移失效。

## 适用范围

- 适用于 `docs/20-specs/` 与 `.trae/skills/` 之间的规范来源映射和上下游关系说明。
- 适用于判断某份执行 Skill 应依赖哪些上游规范，以及规范变更后需要同步检查哪些 Skill。
- 不替代 `20-specs/` 的正式执行规范，也不替代各 `SKILL.md` 中的具体执行步骤。

## 当前定位

- 本文档是规范与 Skill 之间的治理映射文档，用于回答“哪个 Skill 依赖哪些上游规范、变更时应联动检查什么”。
- 本文档聚焦映射关系、更新触发和维护顺序，不单独定义产品边界、数据边界或执行规则。
- 当 `20-specs/` 或 `.trae/skills/` 发生结构性调整时，应优先回看本文档以确认同步范围。

## 基本原则

- `20-specs/` 是规范上游，负责定义边界、约束、验收和协作方式。
- `30-api/` 是接口收敛补充层，用于沉淀接口总览、样例、权限和 OpenAPI 草案，不高于 `20-specs/`。
- `.trae/skills/` 是执行下游，负责把规范转成 Agent 可复用的工作套路。
- Skill 不单独定义产品边界、数据边界和上线规则。
- 当 `20-specs/` 或相关 `30-api/` 文档更新时，必须检查受影响的 Skill 是否需要同步更新。

## 关系判断

- `10-requirements/`
  - 回答“为什么做”和“希望做成什么”
- `20-specs/`
  - 回答“按什么约束落地”和“什么算完成”
- `30-api/`
  - 回答“接口信息如何收敛、样例放在哪里，以及 OpenAPI 草案如何组织”
- `.trae/skills/`
  - 回答“Agent 应该按什么流程执行”

换句话说，推荐链路是：

`10-requirements -> 20-specs -> 30-api -> skills -> execution`

## 总体映射表

| 上游规范 | 主要作用 | 关联 Skill | 映射关系 | 维护建议 |
|---|---|---|---|---|
| `docs/20-specs/product-spec.md` | 定义产品边界、玩法闭环、投票治理、MVP、验收口径 | `requirement-package-builder` `system-design-package-builder` `godot-gameplay-implementer` `world-content-generator` | 提供产品目标、非目标、玩法和世界变化边界 | 产品规则有变更时，优先检查需求包、系统设计和客户端实现 Skill |
| `docs/20-specs/content-generation-spec.md` | 定义 AI 内容生成对象、输入输出结构、审核规则和生命周期 | `system-design-package-builder` `world-content-generator` `content-review-gate` `qa-acceptance-runner` `release-package-operator` | 提供生成对象 schema、生命周期状态和审核前提 | 任何生成字段、模板或生命周期调整，都要同步更新系统设计、内容生成、审核、QA 与发布相关 Skill |
| `docs/20-specs/backend-data-spec.md` | 定义服务边界、数据模型、API、事件流、异步任务 | `system-design-package-builder` `backend-service-builder` `godot-gameplay-implementer` `qa-acceptance-runner` `release-package-operator` | 提供接口契约、数据模型、内容包、回滚与事件基础 | 接口、表结构、状态流调整时，优先检查系统设计、后端、QA 和发布相关 Skill |
| `docs/20-specs/agent-loop-spec.md` | 定义 Agent 角色、需求包、门禁、日志、Issue、回滚流程 | `requirement-package-builder` `system-design-package-builder` `qa-acceptance-runner` `loop-gate-optimizer` `release-package-operator` | 提供需求包格式、门禁输入、日志分析和治理闭环 | Agent 流程和门禁机制变化时，重点更新需求包、系统设计、QA 与闭环优化 Skill |
| `docs/20-specs/engineering-conventions.md` | 定义仓库结构、命名、配置、测试、发布协作规范 | `system-design-package-builder` `backend-service-builder` `godot-gameplay-implementer` `qa-acceptance-runner` `release-package-operator` | 提供工程目录、命名和测试底线 | 工程规范更新后，检查设计类、实现类与 QA 类 Skill 的输出格式和目录约定 |
| `docs/30-api/openapi-draft.md` | 统一沉淀接口草案入口、样例收敛顺序和 OpenAPI 组织方式 | `requirement-package-builder` `system-design-package-builder` `backend-service-builder` `godot-gameplay-implementer` `content-review-gate` `qa-acceptance-runner` `release-package-operator` | 提供接口样例、审批/发布接口收敛和 OpenAPI 同步要求 | 接口路径、请求响应字段、权限或样例更新时，联动检查这些接口相关 Skill |

## Skill 逐项映射

### `requirement-package-builder`

- 主要上游：
  - `docs/20-specs/product-spec.md`
  - `docs/20-specs/agent-loop-spec.md`
- 次要上游：
  - `docs/20-specs/engineering-conventions.md`
  - `docs/30-api/openapi-draft.md`
- 作用：
  - 把产品目标和边界整理成后续 Agent 可直接执行的需求包
- 依赖原因：
  - `product-spec.md` 提供目标、范围、非目标和验收口径
  - `agent-loop-spec.md` 提供需求包与门禁的闭环要求
  - `engineering-conventions.md` 影响任务拆分时的工程边界
  - `openapi-draft.md` 约束接口相关需求包后续如何沉淀到 OpenAPI 草案
- 更新触发：
  - MVP 范围调整
  - 验收口径变化
  - 需求包格式变化
  - 接口约束或样例收敛方式变化

### `backend-service-builder`

- 主要上游：
  - `docs/20-specs/backend-data-spec.md`
  - `docs/20-specs/engineering-conventions.md`
- 次要上游：
  - `docs/20-specs/product-spec.md`
  - `docs/30-api/openapi-draft.md`
- 作用：
  - 生成或扩展后端服务、接口、模型、任务和测试
- 依赖原因：
  - `backend-data-spec.md` 是服务边界和数据契约的直接来源
  - `engineering-conventions.md` 约束目录、命名、配置和测试组织
  - `product-spec.md` 决定哪些能力属于产品边界内
  - `openapi-draft.md` 约束接口草案、请求响应样例和后续 OpenAPI 收敛入口
- 更新触发：
  - API 路由变化
  - 表结构或事件流变化
  - 发布与回滚流程变化
  - 请求响应 schema 或 OpenAPI 草案结构变化

### `system-design-package-builder`

- 主要上游：
  - `docs/20-specs/backend-data-spec.md`
  - `docs/20-specs/product-spec.md`
- 次要上游：
  - `docs/20-specs/content-generation-spec.md`
  - `docs/20-specs/engineering-conventions.md`
  - `docs/20-specs/agent-loop-spec.md`
  - `docs/30-api/openapi-draft.md`
- 作用：
  - 把产品目标与系统约束收敛成服务边界、模块接口、数据契约、事件流和版本策略设计包
- 依赖原因：
  - `backend-data-spec.md` 提供服务边界、核心实体、接口契约和事件流基础
  - `product-spec.md` 提供设计边界、产品闭环和非目标约束
  - `content-generation-spec.md` 提供模板、生命周期和规则版本背景
  - `engineering-conventions.md` 约束工程落位、命名和协作底线
  - `agent-loop-spec.md` 提供需求包承接、回滚影响和闭环交付要求
  - `openapi-draft.md` 提供对外接口样例和 OpenAPI 同步入口
- 更新触发：
  - 服务拆分或模块边界变化
  - 数据契约、事件流或版本策略变化
  - 接口样例或设计交付格式变化

### `godot-gameplay-implementer`

- 主要上游：
  - `docs/20-specs/product-spec.md`
  - `docs/20-specs/engineering-conventions.md`
- 次要上游：
  - `docs/20-specs/backend-data-spec.md`
  - `docs/30-api/openapi-draft.md`
- 作用：
  - 落实客户端玩法逻辑、场景结构、UI 与最小验证路径
- 依赖原因：
  - `product-spec.md` 提供玩法边界、投票入口、世界更新反馈等产品约束
  - `engineering-conventions.md` 提供工程组织和命名方式
  - `backend-data-spec.md` 提供接口契约和数据结构来源
  - `openapi-draft.md` 提供客户端接入所依赖的接口草案和样例收敛入口
- 更新触发：
  - 玩法闭环调整
  - 客户端与服务端契约变化
  - 工程目录和命名规范变化
  - OpenAPI 草案中的客户端相关接口变化

### `world-content-generator`

- 主要上游：
  - `docs/20-specs/content-generation-spec.md`
  - `docs/20-specs/product-spec.md`
- 次要上游：
  - `docs/20-specs/backend-data-spec.md`
- 作用：
  - 生成结构化 NPC、任务、聚落和事件草案
- 依赖原因：
  - `content-generation-spec.md` 是生成字段、模板和状态机的直接来源
  - `product-spec.md` 约束世界骨架、非目标和可变范围
  - `backend-data-spec.md` 提供对象存储、请求追踪和生命周期字段背景
- 更新触发：
  - 生成对象字段变化
  - 模板版本策略变化
  - 内容生命周期变化

### `content-review-gate`

- 主要上游：
  - `docs/20-specs/content-generation-spec.md`
  - `docs/20-specs/product-spec.md`
- 次要上游：
  - `docs/20-specs/agent-loop-spec.md`
  - `docs/20-specs/backend-data-spec.md`
  - `docs/30-api/openapi-draft.md`
- 作用：
  - 对生成结果做结构化审核，输出通过、驳回或人工复核结论
- 依赖原因：
  - `content-generation-spec.md` 提供被审核对象的结构和边界
  - `product-spec.md` 提供世界一致性和主线骨架不可突破的约束
  - `agent-loop-spec.md` 提供门禁与治理流程上下文
  - `backend-data-spec.md` 提供审核记录字段与状态迁移背景
  - `openapi-draft.md` 提供审核审批接口和返回结构的收敛入口
- 更新触发：
  - 审核维度变化
  - 风险等级定义变化
  - 内容状态流变化
  - 审批接口或返回字段变化

### `qa-acceptance-runner`

- 主要上游：
  - `docs/20-specs/agent-loop-spec.md`
  - `docs/20-specs/engineering-conventions.md`
- 次要上游：
  - `docs/20-specs/backend-data-spec.md`
  - `docs/20-specs/content-generation-spec.md`
  - `docs/30-api/openapi-draft.md`
- 作用：
  - 围绕需求包和改动范围执行验收检查、回归脚本和门禁汇总，输出可交付证据与失败摘要
- 依赖原因：
  - `agent-loop-spec.md` 提供验收、门禁、修复计划和失败反馈闭环
  - `engineering-conventions.md` 约束测试组织、协作方式和交付底线
  - `backend-data-spec.md` 提供接口、任务链路和性能基线相关检查背景
  - `content-generation-spec.md` 提供内容检查、生命周期和发布前置条件
  - `openapi-draft.md` 提供接口契约样例和 OpenAPI 同步检查入口
- 更新触发：
  - 验收格式或门禁流程变化
  - 测试组织和交付要求变化
  - 接口样例、内容检查或回归基线变化

### `loop-gate-optimizer`

- 主要上游：
  - `docs/20-specs/agent-loop-spec.md`
- 次要上游：
  - `docs/20-specs/engineering-conventions.md`
  - `docs/40-dev-loop/log-schemas-loop-engineering.md`
- 作用：
  - 从会话日志、CI 失败和事故中提炼门禁改进建议
- 依赖原因：
  - `agent-loop-spec.md` 提供 Agent 角色、门禁和闭环目标
  - 门禁清单与分类约定提供现有 gate 范围
  - `log-schemas-loop-engineering.md` 提供日志输入结构
- 更新触发：
  - 门禁分类变化
  - 日志 schema 变化
  - Issue 反馈流程变化

### `release-package-operator`

- 主要上游：
  - `docs/20-specs/backend-data-spec.md`
  - `docs/20-specs/agent-loop-spec.md`
- 次要上游：
  - `docs/20-specs/content-generation-spec.md`
  - `docs/20-specs/engineering-conventions.md`
  - `docs/30-api/openapi-draft.md`
- 作用：
  - 组织内容包打包、灰度、正式发布、回滚和发布记录
- 依赖原因：
  - `backend-data-spec.md` 提供内容包、上线状态和回滚记录的核心约束
  - `agent-loop-spec.md` 提供发布治理和回滚闭环要求
  - `content-generation-spec.md` 决定只有符合生命周期约束的对象才能进入发布链路
  - `openapi-draft.md` 提供发布、回滚和内容包查询接口的收敛入口
- 更新触发：
  - 内容包状态变化
  - 灰度与回滚规则变化
  - 发布摘要要求变化
  - 发布或回滚接口变化

## 维护规则

1. `20-specs/` 先改，涉及接口文档时再更新 `30-api/`，最后同步 `skills/`，不反过来。
2. 一个 Skill 至少要标清自己的主要上游规范。
3. 一个 spec 如果影响多个 Skill，优先维护映射表，再逐个更新 Skill。
4. Skill 中如果出现新的业务边界定义，应回收到 `20-specs/`，不要只留在 Skill 里。

## 建议操作

- 继续在新增或调整的 `SKILL.md` 中维护“规范来源”，避免映射关系回退到隐式状态。
- 后续若映射范围变化，应同步更新 `docs/00-governance/document-map.md`、`docs/README.md` 和相关入口文档。
- 若 `20-specs/` 有重大调整，先过一遍本文档，再决定需要更新哪些 Skill。

## 与其他文档的关系

- `docs/20-specs/README.md`
  - 作为执行规范目录入口，帮助读者定位本文档所映射的上游规范集合。
- `docs/00-governance/document-map.md`
  - 说明文档体系的分层和权威关系，本文档补充其中“规范到 Skill”的下游映射。
- `docs/00-governance/document-change-process.md`
  - 规定当规范路径、目录或引用变化时，应同步检查和更新本文档。
- `docs/00-governance/document-ownership.md`
  - 定义规范责任人、Skill 维护责任人和映射更新时的协同边界。
- `.trae/skills/*/SKILL.md`
  - 作为本文档的下游执行载体，应根据这里的映射结果维护各自的规范来源说明。

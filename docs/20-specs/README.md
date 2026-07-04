# 详细规范包

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

这一组文档是在既有 `10-requirements/`、`40-dev-loop/` 和 `50-research/` 的基础上继续细化出的执行规范。前面的文档解决“做什么”和“为什么这样做”，这里重点解决“具体按什么约束落地”。

## 适用范围

- 适用于后续拆任务、建仓库、写代码、接入 CI 和制定验收标准。
- 适用于需要把需求背景转化为可执行约束的协作场景。
- 不承担需求立项背景或技术选型归档角色，这两类内容分别保留在 `10-requirements/` 和 `50-research/`。

## 当前定位

- 本文档是 `20-specs/` 的入口说明，不替代各具体规范正文。
- `20-specs/` 是当前仓库中权威级别最高的执行规范目录。
- 当其他目录文档与本目录中的具体规范冲突时，以相应规范正文为准。

## 文档列表

- `product-spec.md`
  - 产品范围、玩法闭环、章节推进、投票治理与验收口径
- `content-generation-spec.md`
  - 世界骨架、AI 生成对象、输入输出结构、审核规则与内容生命周期
- `backend-data-spec.md`
  - 服务拆分、核心数据模型、API 约定、事件流与异步任务规范
- `agent-loop-spec.md`
  - Agent 角色、需求包格式、门禁体系、日志采集、Issue 反馈与回滚流程
- `engineering-conventions.md`
  - 仓库结构、命名、配置、版本、发布、代码与内容资源协作规范
- `async-tasks-and-events/`
  - 异步任务 payload、事件消息格式、重试策略、死信队列、全链路追踪与审计规范

## 建议使用顺序

1. 先读 `product-spec.md`，确认产品边界和 MVP 范围
2. 再读 `content-generation-spec.md`，确定世界内容与 AI 输出约束
3. 然后读 `backend-data-spec.md`，拆服务、表结构和接口
4. 再读 `agent-loop-spec.md`，建立 AI coding 的执行闭环
5. 最后读 `engineering-conventions.md`，统一仓库和协作方式

## 与其他文档的关系

- `10-requirements/`：保留需求背景、功能设计和高层技术方案
- `40-dev-loop/`：保留 Loop Engineering 主方案、门禁注册表和日志 schema
- `50-research/`：保留引擎与技术栈选型依据
- `20-specs/`：作为后续拆任务、建仓库、写代码和接 CI 的直接输入

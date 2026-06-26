# 详细规范包

## 目的

这一组文档是在既有 `10-requirements/`、`40-dev-loop/` 和 `50-research/` 的基础上继续细化出的执行规范。前面的文档解决“做什么”和“为什么这样做”，这里重点解决“具体按什么约束落地”。

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

## 建议使用顺序

1. 先读 `product-spec.md`，确认产品边界和 MVP 范围
2. 再读 `content-generation-spec.md`，确定世界内容与 AI 输出约束
3. 然后读 `backend-data-spec.md`，拆服务、表结构和接口
4. 再读 `agent-loop-spec.md`，建立 AI coding 的执行闭环
5. 最后读 `engineering-conventions.md`，统一仓库和协作方式

## 与已有文档的关系

- `10-requirements/`：保留需求背景、功能设计和高层技术方案
- `40-dev-loop/`：保留 Loop Engineering 主方案、门禁注册表和日志 schema
- `50-research/`：保留引擎与技术栈选型依据
- `20-specs/`：作为后续拆任务、建仓库、写代码和接 CI 的直接输入

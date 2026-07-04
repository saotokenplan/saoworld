# 异步任务与事件 Schema 规范

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 适用范围

- 适用于 Celery 异步任务的输入输出契约、事件消息格式、重试策略、死信处理。
- 适用于服务间异步通信、事件驱动架构、内容链路编排。
- 不替代各服务内部 API 接口规范、数据模型定义和业务流程规范。

## 当前定位

- 本文档是异步任务与事件的核心契约规范，用于回答"异步任务如何调用、事件如何传递、失败如何处理"。
- 本文档聚焦跨服务异步协作的统一标准，不单独定义具体业务逻辑或服务内部实现。
- 当具体实现与本规范冲突时，应优先以本规范为准。

## 目标

本规范定义异步任务的 payload schema、事件消息格式、重试策略、死信队列和全链路追踪要求。原则是"契约先行、幂等优先、可观测可回溯"，确保服务间异步协作的一致性和可靠性。

## 目录索引

| 文档 | 说明 |
|------|------|
| [task-payloads.md](./task-payloads.md) | 7 个核心异步任务的输入输出 schema |
| [event-schemas.md](./event-schemas.md) | 内部事件总线主题与消息格式 |
| [retry-and-dlq.md](./retry-and-dlq.md) | 重试策略与死信队列规范 |
| [trace-and-audit.md](./trace-and-audit.md) | 全链路追踪与审计字段规范 |

## 核心原则

### 1. 契约优先

所有异步任务和事件必须有明确的 schema 定义，包括：
- 字段名称、类型、是否必填
- 字段含义与约束
- 输入输出示例
- 错误码与异常类型

### 2. 幂等性

所有异步任务必须支持幂等执行：
- 同一任务重复执行不会产生副作用
- 关键操作使用幂等键（idempotency_key）去重
- 任务状态机严格遵循状态迁移约束

### 3. 全链路追踪

- 所有任务和事件必须携带 `trace_id`
- `trace_id` 在整个调用链中透传
- 日志、审计、监控都绑定 `trace_id`

### 4. 可观测可回溯

- 每个任务必须有明确的状态迁移记录
- 失败任务必须保留错误上下文
- 死信队列中的消息可追溯、可重放

## 任务队列划分

| 队列 | 职责 | 任务 |
|------|------|------|
| `generation` | AI 内容生成 | generate_content_batch |
| `review` | 内容审核 | run_world_consistency_review、run_balance_review |
| `packaging` | 内容打包 | package_content_batch |
| `release` | 发布与回滚 | release_content_package、rollback_content_package |
| `gate` | 门禁扫描 | daily_gate_scan |

## 事件总线主题

| 主题 | 触发时机 | 生产者 | 消费者 |
|------|----------|--------|--------|
| `vote.cycle.closed` | 投票周期关闭 | vote-service | generation-service、ops-service |
| `vote.result.finalized` | 投票结果确认 | vote-service | generation-service、content-service |
| `generation.request.created` | 生成请求创建 | generation-service | ops-service |
| `generation.batch.completed` | 批量生成完成 | generation-service | review-service、ops-service |
| `review.batch.completed` | 批量审核完成 | review-service | content-service、ops-service |
| `content.package.released` | 内容包发布 | content-service | ops-service、world-service |
| `content.package.rolled_back` | 内容包回滚 | content-service | ops-service、world-service |

## 与其他文档的关系

- `docs/20-specs/backend-data-spec.md`
  - 定义数据库表结构、状态机、索引和约束，为本规范中的 payload 字段提供数据来源。
- `docs/20-specs/content-generation-spec.md`
  - 定义内容生成的输入输出结构、模板约束和审核维度，支撑生成类任务的 payload。
- `docs/20-specs/agent-loop-spec.md`
  - 定义 Agent 角色、门禁体系和研发闭环，本规范是其在异步执行层的具体落地。
- `docs/30-api/api-overview.md`
  - 定义同步 API 接口规范，本规范是其异步补充。

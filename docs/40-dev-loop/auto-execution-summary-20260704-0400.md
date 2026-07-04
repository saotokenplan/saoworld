# 自动执行摘要 - 补充异步任务与事件 payload schema

> task_id: auto-20260704-0400
> 执行时间：2026-07-04 04:00 - 2026-07-04 05:00
> 工作分支：auto/auto-20260704-0400
> 任务状态：已完成

## 任务目标

根据 `project-status.md` 的"下一阶段建议"第 9 项，补充异步任务和事件的 payload schema 规范，为内容链路打通和服务间集成提供明确的契约规范。

## 本轮完成的工作清单

### 1. 创建规范目录结构
- 在 `docs/20-specs/` 下创建 `async-tasks-and-events/` 子目录
- 创建 5 个规范文档

### 2. 编写异步任务 payload schema（task-payloads.md）
为 7 个核心异步任务定义了详细的输入输出结构：
- **generate_content_batch** - 内容生成批量任务（generation 队列）
- **run_world_consistency_review** - 世界一致性审核（review 队列）
- **run_balance_review** - 数值平衡审核（review 队列）
- **package_content_batch** - 内容打包（packaging 队列）
- **release_content_package** - 内容发布（release 队列）
- **rollback_content_package** - 内容回滚（release 队列）
- **daily_gate_scan** - 每日门禁扫描（gate 队列）

每个任务都定义了：
- 任务名称、队列、重试策略
- 输入字段（名称、类型、必填、说明、示例）
- 输出字段（名称、类型、说明）
- 错误类型与重试策略
- 输入输出示例

### 3. 编写事件消息 schema（event-schemas.md）
定义了 7 个核心事件主题和消息格式：
- **vote.cycle.closed** - 投票周期关闭
- **vote.result.finalized** - 投票结果确认
- **generation.request.created** - 生成请求创建
- **generation.batch.completed** - 批量生成完成
- **review.batch.completed** - 批量审核完成
- **content.package.released** - 内容包发布
- **content.package.rolled_back** - 内容包回滚

每个事件定义了：
- 事件主题、触发时机、生产者、消费者
- Payload 字段说明
- Payload 示例
- 消费者处理逻辑

### 4. 编写重试策略与死信队列规范（retry-and-dlq.md）
- 错误分类：可重试错误 vs 不可重试错误
- 通用重试配置：最大重试 3 次，指数退避，基数 2 秒
- 死信队列（DLQ）：触发条件、消息结构、处理流程、管理要求
- 幂等性要求：幂等键、实现模式、状态机校验
- 任务状态机：pending → processing → succeeded / failed_retryable / failed_permanent
- 熔断与降级：熔断器模式、配置参数、降级策略

### 5. 编写全链路追踪与审计字段规范（trace-and-audit.md）
- 追踪 ID 规范：trace_id、request_id、task_id、event_id
- 追踪 ID 传递规则：全程透传、自动生成、日志绑定
- 审计日志表结构：12 个字段、CHECK 约束、4 个索引
- 操作类型命名规范：`<domain>.<action>` 格式
- 资源类型定义
- 结构化日志规范：structlog 配置、必备字段、日志事件命名
- 任务必须记录的审计点
- 日志级别使用规范

### 6. 更新规范引用
- 更新 `docs/20-specs/README.md`，添加 async-tasks-and-events 目录引用
- 更新 `docs/00-governance/document-map.md`，添加新规范的文档盘点

### 7. 更新项目状态
- 更新 `docs/00-governance/project-status.md`
  - 第 9 项标记为已完成（~~删除线~~）
  - 在"已准备好的资产"中添加异步任务与事件规范

## 修改的文件清单

**新增文件（5 个）：**
- `docs/20-specs/async-tasks-and-events/README.md` - 规范总览
- `docs/20-specs/async-tasks-and-events/task-payloads.md` - 任务 payload schema
- `docs/20-specs/async-tasks-and-events/event-schemas.md` - 事件消息格式
- `docs/20-specs/async-tasks-and-events/retry-and-dlq.md` - 重试与死信队列
- `docs/20-specs/async-tasks-and-events/trace-and-audit.md` - 追踪与审计
- `docs/40-dev-loop/auto-plan-20260704-0400.md` - 工作计划
- `docs/40-dev-loop/auto-execution-summary-20260704-0400.md` - 本执行摘要

**修改文件（3 个）：**
- `docs/20-specs/README.md` - 添加新规范引用
- `docs/00-governance/document-map.md` - 添加文档盘点
- `docs/00-governance/project-status.md` - 更新项目状态

## 遗留问题与下一步建议

### 遗留问题
- 事件总线尚未实际实现（当前规范是契约层，实际的消息队列实现待后续）
- 熔断器模式目前是规范定义，实际代码实现待后续
- DLQ 管理界面和重放机制待实现

### 下一步建议
1. **优先级 P1**：补充 CI/CD 配置（GitHub Actions / GitLab CI），建立代码门禁
2. **优先级 P1**：初始化 Godot 客户端工程骨架，建立最小可运行版本
3. **优先级 P2**：实现事件总线（RabbitMQ / Redis Streams），打通服务间异步通信
4. **优先级 P2**：打通内容链路端到端流程（生成 → 审核 → 打包 → 发布 → 回滚）
5. **优先级 P3**：补充数据库 ER 图和更详细的迁移策略

## 验收结果

所有 checklist 项均已完成 ✅：
- [x] schema 规范目录结构完整
- [x] 7 个核心异步任务的输入输出 schema 定义完整
- [x] 7 个核心事件主题的消息格式定义完整
- [x] 重试策略与死信队列规范定义清晰
- [x] 追踪与审计字段规范定义完整
- [x] 规范文档引用关系正确（20-specs README、document-map）
- [x] project-status.md 已同步更新，第 9 项标记为已完成

## 合并结果

- 合并状态：已成功合并
- 合并目标分支：feature-prd
- 工作分支：auto/auto-20260704-0400（已删除）
- 合并提交：0a49153
- 合并方式：--no-ff
- 冲突情况：无冲突

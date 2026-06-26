# backend-service-builder

## 目标

实现投票、生成、审核、内容投放和运营相关后端服务，默认技术栈为 Python、FastAPI、PostgreSQL、Celery。重点是服务边界清楚、接口可验证、长任务可追踪。

## 适用场景

- 新服务初始化
- 新 API、数据模型、任务队列能力开发
- 既有服务的增量扩展

## 规范来源

- 主要来源：
  - `docs/20-specs/backend-data-spec.md`
  - `docs/20-specs/engineering-conventions.md`
- 次要来源：
  - `docs/20-specs/product-spec.md`
  - `docs/30-api/openapi-draft.md`
- 说明：
  - 服务边界、数据模型、接口、事件流和任务约束以 `backend-data-spec.md` 为准
  - 工程目录、命名、配置和测试约束参考 `engineering-conventions.md`
  - 产品能力范围和非目标边界参考 `product-spec.md`
  - 接口契约收敛和 OpenAPI 草案落位参考 `openapi-draft.md`

## 输入

- 需求包
- 数据模型规范
- API 约定
- 事件流定义
- 权限与风控要求

## 输出

- 服务代码
- schema 与模型定义
- 数据迁移
- API 测试
- 任务定义
- 必要时更新 `docs/30-api/openapi-draft.md`
- 变更摘要

## 实现原则

- 路由层只做协议适配，不写复杂业务
- 所有输入输出必须有 schema
- 长任务必须进入队列
- 状态变更必须写入审计链
- 接口与任务必须支持幂等和重试

## 最低实现要求

### API

- 所有接口带 `/api/v1`
- 错误响应结构统一
- 鉴权和权限检查前置
- 若接口边界或 schema 发生变化，应同步更新 OpenAPI 草案入口

### 数据

- 强事务数据进入 PostgreSQL
- 半结构化对象使用 `jsonb`
- 所有关键表都有 `created_at`、`updated_at`
- 状态字段必须受控

### 任务

- 每个任务有明确 `task_id`
- 区分可重试失败与不可重试失败
- 任务状态可查询

## 硬约束

- 不在同步接口中执行生成、审核、打包和发布长任务
- 不跳过 schema 校验直接读写数据库
- 不把运营接口和玩家接口混在同一权限域
- 不把关键状态变更写成不可追踪的隐式逻辑

## 最低测试要求

以下能力改动时必须覆盖测试：

- 投票提交流程
- 投票结算流程
- 内容对象创建与审核状态迁移
- 内容包发布与回滚
- 权限和异常分支

## 不该做的事

- 不在一个服务里承载所有领域逻辑
- 不把灰度发布和回滚做成手工不可复现的操作

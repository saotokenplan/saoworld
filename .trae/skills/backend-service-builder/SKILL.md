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

### 新服务强制要求

**新建服务时必须同步创建测试目录和基础测试，不得先提交代码后补测试。**

新服务最低测试清单（同一次提交中必须包含）：
- `tests/conftest.py` — 测试客户端与数据库 fixture
- `tests/test_health.py` — 健康检查接口
- `tests/test_auth.py` — 鉴权与权限场景
- 至少 1 个核心接口的成功路径测试
- 至少 2 个异常/错误码场景测试

缺少测试的新服务提交将被 commit-msg hook 警告。

## 不该做的事

- 不在一个服务里承载所有领域逻辑
- 不把灰度发布和回滚做成手工不可复现的操作

## 提交规范

所有代码和文档提交必须遵守 `.trae/rules/40-git-workflow.md` 和 `.trae/rules/02-agent-loop-constraints.md`。

### 提交格式

`<type>(<scope>): <summary>`

- type: docs / feat / fix / refactor / test / chore
- summary: 使用祈使句（新增/补充/调整/修复/重构），具体描述改动，不超过100字符，不以句号结尾

### 提交规模限制

单次提交不得超过以下规模，超过时必须拆分：
- 文件数 ≤ 50 个（超过 100 个将被 hook 拦截）
- 新增行数 ≤ 2000 行（超过 5000 行将被 hook 拦截）
- 总变更行数 ≤ 3000 行（超过 8000 行将被 hook 拦截）

拆分原则（按优先级）：
1. 按服务拆分：不同微服务分别提交
2. 按层次拆分：领域模型 → 仓储层 → API 层 → 测试
3. 按主题拆分：独立功能点各自成提交
4. 规范先行：规范文档先提交，再提交实现

### type 与内容一致性

- `docs` type 下代码文件占比不得超过 30%（否则 hook 拦截）
- `feat` 用于新增功能，`fix` 用于修复缺陷，不得混用
- 主要为代码变更时禁止使用 `docs` type

### 提交前必须

1. 执行 `python tools/validate-commit-msg.py --message "type(scope): 摘要"` 预验证
2. 确认一次提交只包含一个主题，多个改动拆分多次提交
3. 确认无调试残留（pdb/breakpoint/debug print）、无冲突标记、无无关文件
4. 新服务必须附带测试文件，否则提交不完整
5. 提交后立即 `git push`（远程不可用时明确记录阻塞原因）

### 禁止的提交信息

- "update"、"fix bug"、"wip"、"一些修改"、"临时提交" 等模糊表述
- 照抄整段会话总结而非描述实际改动
- 一个提交混入多个不相关主题
- type 与实际变更性质严重不符

### 推荐 scope

- gateway
- player
- world
- vote
- generation
- review
- content
- ops
- infra
- api

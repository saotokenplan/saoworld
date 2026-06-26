# system-design-package-builder

## 目标

把产品目标、服务约束和内容规则收敛成可实施的系统设计包，明确服务边界、模块接口、数据契约、事件流和模板/规则版本策略。重点是先把“系统怎么拆、契约怎么定、版本怎么管”讲清楚，再交给实现类 Skill 落地。

## 适用场景

- 新能力准备进入实现前，需要先明确系统边界和模块协作
- 需求涉及多个服务、异步任务或事件流，不能直接进入编码
- 接口、数据结构和模板/规则版本需要统一设计口径
- 现有方案已讨论过方向，但还没有形成可供后续 Agent 承接的设计包

## 规范来源

- 主要来源：
  - `docs/20-specs/backend-data-spec.md`
  - `docs/20-specs/product-spec.md`
- 次要来源：
  - `docs/20-specs/content-generation-spec.md`
  - `docs/20-specs/engineering-conventions.md`
  - `docs/20-specs/agent-loop-spec.md`
  - `docs/30-api/openapi-draft.md`
- 说明：
  - 服务边界、数据模型、接口契约、异步任务和事件流以 `backend-data-spec.md` 为准
  - 产品目标、范围、非目标和玩法闭环边界以 `product-spec.md` 为准
  - 内容对象、模板机制、生命周期和版本约束参考 `content-generation-spec.md`
  - 工程目录、命名、配置和协作底线参考 `engineering-conventions.md`
  - 需求包、回滚影响和闭环交付要求参考 `agent-loop-spec.md`
  - 对外接口样例和 OpenAPI 草案收敛入口参考 `openapi-draft.md`

## 输入

- 产品目标与范围说明
- `spec.md`
- `acceptance.md`
- 已有系统上下文与现存服务清单
- 接口、数据或内容规则的待定问题
- 相关上游规范与约束文档

## 输出

- `system-design.md`
- `service-boundaries.md`
- `data-contracts.md`
- `event-flow.md`
- 必要时输出 `template-version-plan.md`
- 必要时输出 `api-sync-notes.md`
- 必要时输出 `rollback-impact.md`

## 工作流程

1. 先确认主目标、范围和非目标，避免设计包替代需求包
2. 按能力链路拆服务边界、领域职责和协作关系
3. 明确核心数据契约、状态流和异步任务边界
4. 识别对外接口、内部事件和模板/规则版本策略
5. 标注实现前置条件、回滚影响和待决策项
6. 输出可被实现类 Skill 直接承接的设计结论

## 设计原则

- 先定边界，再定接口，再定实现分工
- 设计包只回答“如何拆”和“如何协作”，不直接进入代码细节
- 对外接口、内部事件、数据状态和版本策略必须互相对齐
- 若接口要对外暴露，必须考虑是否需要同步到 `docs/30-api/openapi-draft.md`

## 最低输出要求

### `system-design.md`

至少包含：

- 目标能力
- 边界与非目标
- 受影响服务或模块
- 关键协作链路
- 待决策项

### `service-boundaries.md`

至少包含：

- 服务或模块名称
- 主要职责
- 不负责的内容
- 上下游依赖
- 触发的异步任务或事件

### `data-contracts.md`

至少包含：

- 核心实体
- 关键字段
- 状态流或生命周期
- 约束条件
- 兼容性与迁移注意事项

### `event-flow.md`

至少包含：

- 关键事件主题
- 生产者与消费者
- 触发条件
- 幂等与失败处理
- 审计或追踪要求

## 输出模板建议

### `system-design.md`

建议最小结构：

```md
# System Design

## 目标能力

## 范围与非目标

## 关键链路

## 受影响服务或模块

## 待决策项
```

### `service-boundaries.md`

建议最小结构：

```md
# Service Boundaries

## 服务列表

### <service_or_module_name>

- 主要职责
- 不负责内容
- 上游依赖
- 下游依赖
- 异步任务或事件
```

### `data-contracts.md`

建议最小结构：

```md
# Data Contracts

## 核心实体

### <entity_name>

- 关键字段
- 状态流或生命周期
- 约束条件
- 兼容性与迁移注意事项
```

### `event-flow.md`

建议最小结构：

```md
# Event Flow

## 关键事件

### <event_topic>

- 生产者
- 消费者
- 触发条件
- 幂等要求
- 失败处理
- 审计字段
```

### `template-version-plan.md`

若设计涉及模板或规则升级，至少补充：

- 版本对象
- 当前版本与目标版本
- 升级触发条件
- 兼容性策略
- 回滚策略

## 硬约束

- 不在设计包中重新定义已被上游规范明确写死的产品边界
- 不把实现细节伪装成系统设计结论
- 不遗漏回滚影响、状态迁移和跨服务协作前提
- 不在接口边界变化时漏掉 `docs/30-api/openapi-draft.md` 的同步判断
- 若仍存在关键未定项，不得输出“可直接实施”结论

## 不该做的事

- 不直接写服务代码或客户端实现
- 不把需求包、设计包和发布方案混成一个文档
- 不脱离上游规范单独发明服务、状态或规则

## 提交规范

所有代码和文档提交必须遵守 `docs/20-specs/engineering-conventions.md#git-提交规范` 和 `docs/20-specs/agent-loop-spec.md#ai-提交前自检清单强制执行`。

### 提交格式

`<type>(<scope>): <summary>`

- type: docs / feat / fix / refactor / test / chore
- summary: 使用祈使句（新增/补充/调整/修复/重构），具体描述改动，不超过100字符，不以句号结尾

### 提交前必须

1. 执行 `python tools/validate-commit-msg.py --message "type(scope): 摘要"` 预验证提交信息格式
2. 确认一次提交只包含一个主题，多个改动拆分多次提交
3. 确认无调试残留（pdb/breakpoint/debug print）、无冲突标记、无无关文件
4. 提交后立即 `git push`（远程不可用时明确记录阻塞原因）

### 禁止的提交信息

- "update"、"fix bug"、"wip"、"一些修改"、"临时提交" 等模糊表述
- 照抄整段会话总结而非描述实际改动
- 一个提交混入多个不相关主题

### 推荐 scope

- docs
- specs
- api

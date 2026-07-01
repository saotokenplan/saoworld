# SAO World 项目规则索引

> 本目录包含项目各领域的工程执行规则，所有代码、文档、配置变更必须遵循对应领域的规则。
> 规则来源：`docs/20-specs/` 下的执行规范文档。

## 规则优先级

- 所有规则冲突时，以更高层级编号前的通用规则为基础，专项规则优先于通用规则
- **文档权威层级**：`docs/20-specs/` > 本目录规则 > `docs/10-requirements/` > 其他文档

## 规则文件列表

### 00-09 项目基础与Agent规则

| 文件 | 内容 | 适用角色 | 类型 |
|------|------|----------|------|
| [00-project-overview.md](./00-project-overview.md) | 项目定位、核心玩法、任务完成定义、快速启动 | 全员 | 业务规范 |
| [01-repository-structure.md](./01-repository-structure.md) | 仓库目录结构、命名规范、ID前缀约定 | 全员 | 业务规范 |
| [02-agent-loop-constraints.md](./02-agent-loop-constraints.md) | AI Agent循环约束、权限边界、异常处理 | AI Agent | Agent约束 |

### 10-29 后端开发规则

| 文件 | 内容 | 适用角色 | 类型 |
|------|------|----------|------|
| [10-python-backend.md](./10-python-backend.md) | Python技术栈、代码风格、配置管理、日志规范 | 后端开发 | 业务规范 |
| [11-database.md](./11-database.md) | 数据库约定、状态机约束、关键表特殊规则 | 后端开发、DBA | 业务规范 |
| [12-api-design.md](./12-api-design.md) | API通用约定、响应格式、错误码、权限Scope | 后端开发、前端开发 | 业务规范 |

### 30-39 客户端规则

| 文件 | 内容 | 适用角色 | 类型 |
|------|------|----------|------|
| [30-godot-client.md](./30-godot-client.md) | Godot 4客户端场景、脚本、数据规范 | 客户端开发 | 业务规范 |

### 40-49 工作流规则

| 文件 | 内容 | 适用角色 | 类型 |
|------|------|----------|------|
| [40-git-workflow.md](./40-git-workflow.md) | Git提交规范、分支策略、版本管理 | 全员 | 业务规范 |
| [41-testing.md](./41-testing.md) | 服务端/客户端/内容测试规范 | 开发、QA | 业务规范 |
| [42-release-rollback.md](./42-release-rollback.md) | 发布前检查、灰度策略、回滚规范 | DevOps、运营 | 业务规范 |

### 50-59 专项规则

| 文件 | 内容 | 适用角色 | 类型 |
|------|------|----------|------|
| [50-security.md](./50-security.md) | 接口安全、风控、审计、密钥管理 | 后端开发、安全 | 业务规范 |
| [51-ai-content-generation.md](./51-ai-content-generation.md) | AI生成边界、质量门槛、审核流程 | 内容、AI开发 | 业务规范 |
| [52-documentation.md](./52-documentation.md) | 文档分层、模板、维护更新规则 | 全员 | 业务规范 |

## 快速查找指南

### 业务场景

- 我是新成员，从哪开始？ → [00-project-overview.md](./00-project-overview.md)
- 我要写后端接口？ → [10-python-backend.md](./10-python-backend.md) + [11-database.md](./11-database.md) + [12-api-design.md](./12-api-design.md)
- 我要提交代码？ → [40-git-workflow.md](./40-git-workflow.md)
- 我要写测试？ → [41-testing.md](./41-testing.md)
- 我要做AI内容生成？ → [51-ai-content-generation.md](./51-ai-content-generation.md)
- 我要发布上线？ → [42-release-rollback.md](./42-release-rollback.md) + [50-security.md](./50-security.md)

### Agent执行场景

- 我要执行复杂任务？ → 先阅读 [02-agent-loop-constraints.md](./02-agent-loop-constraints.md) 了解循环约束和权限边界
- 我要生成内容包？ → 遵循 [51-ai-content-generation.md](./51-ai-content-generation.md) + [02-agent-loop-constraints.md](./02-agent-loop-constraints.md) 第三章节
- 我要发布灰度？ → 遵循 [42-release-rollback.md](./42-release-rollback.md) + [02-agent-loop-constraints.md](./02-agent-loop-constraints.md) 第三章节

## 规则类型说明

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| **业务规范** | 项目业务逻辑、技术选型、流程约束的规则 | 所有人员执行业务任务时必须遵守 |
| **Agent约束** | AI Agent执行任务时的循环控制、权限边界、异常处理规则 | Agent自动化执行任务时的强制约束 |

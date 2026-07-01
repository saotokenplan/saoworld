# 10 - Python 后端开发规范

> 适用角色：后端开发
> 本文件定义 Python 后端服务的技术栈、代码风格、配置管理、日志规范。

## 技术栈强制约定

| 类别 | 技术选型 | 版本要求 |
|------|----------|----------|
| Python 版本 | Python | >= 3.11 |
| Web 框架 | FastAPI + Uvicorn | FastAPI >= 0.111, Uvicorn[standard] >= 0.30 |
| ORM | SQLAlchemy（异步模式） | >= 2.0 |
| 数据库驱动 | asyncpg | >= 0.29 |
| 数据迁移 | Alembic | >= 1.13 |
| 数据验证 | Pydantic + pydantic-settings | Pydantic >= 2.7 |
| 认证 | python-jose[cryptography] | >= 3.3 |
| 日志 | structlog | >= 24.4 |
| 任务队列 | Celery（待实现） | - |
| 测试框架 | pytest + pytest-asyncio + httpx | pytest >= 8.2 |
| Lint/Format | ruff | >= 0.5 |
| 类型检查 | mypy | >= 1.10 |

**禁止**在未经过架构评审的情况下引入新的核心依赖。

---

## 代码风格

### 通用约定

- 所有函数参数、返回值、类属性必须标注类型注解（type hints）
- 行长度限制：120 字符
- 使用现代 Python 语法：
  - 联合类型：`X | None` 而非 `Optional[X]`
  - 集合类型：`list[str]` 而非 `List[str]`
  - 使用 `Mapped[...]` 进行 SQLAlchemy 2.0 类型映射
- 代码应自解释，**不添加无意义注释**
- 遵循 PEP 8 命名规范（类名 PascalCase，函数/变量 snake_case，常量 UPPER_SNAKE_CASE）

### 分层架构约束

- **api/**（路由层）：只处理 HTTP 请求/响应、参数校验、调用 repository/service
  - 禁止在路由层直接拼接 SQL
  - 禁止在路由层写业务逻辑
- **repositories/**（数据访问层）：只负责数据库 CRUD
  - 每个 Repository 对应一个聚合根
  - 方法名清晰表达意图：`get_by_id`、`create`、`list`、`exists`
- **domain/**（领域模型层）：SQLAlchemy 模型定义
  - 模型之间的关系使用 `relationship()` 定义
  - CHECK 约束必须在模型中声明
- **schemas/**（Pydantic模型）：请求/响应 DTO
  - 使用 `ConfigDict(from_attributes=True)` 支持从 ORM 对象转换
  - 请求模型包含字段校验（Field(ge=..., le=...) 等）
- **core/**（核心配置）：配置、数据库连接、中间件
- **tasks/**（异步任务）：Celery 任务定义

### 异步编程约定

- 所有数据库操作必须使用异步（`async/await`）
- 数据库会话使用 `AsyncSession`，通过依赖注入获取
- 长任务（AI生成、审核、打包、发布）**禁止**在 Web 进程中同步执行，必须走 Celery 异步任务

### pyproject.toml 约定

每个服务的 pyproject.toml 必须包含：
- 项目元信息（name, version, description）
- `requires-python = ">=3.11"`
- 核心依赖列表
- `[project.optional-dependencies]` 中的 dev 依赖
- pytest 配置（testpaths, asyncio_mode）
- ruff 配置（line-length, target-version）
- mypy 配置（python_version, 严格检查选项）

---

## 配置管理

### 配置加载方式

- 使用 `pydantic-settings.BaseSettings` 从环境变量加载配置
- 环境变量前缀格式：`<SERVICE_NAME>_`（大写）
  - 例如 vote-service 使用 `VOTE_` 前缀
  - database_url → `VOTE_DATABASE_URL`

### 必备配置项

每个服务必须包含以下配置项：

| 配置项 | 类型 | 说明 |
|--------|------|------|
| `app_name` | str | 服务名称 |
| `app_version` | str | 服务版本 |
| `debug` | bool | 调试模式开关 |
| `environment` | str | 运行环境：local/test/staging/prod |
| `database_url` | str | 数据库连接字符串 |
| `log_level` | str | 日志级别（INFO/DEBUG/WARNING/ERROR） |
| `api_v1_prefix` | str | API前缀，默认 `/api/v1` |
| `request_id_header` | str | 请求ID头，默认 `X-Request-Id` |
| `trace_id_header` | str | 追踪ID头，默认 `X-Trace-Id` |
| `idempotency_key_header` | str | 幂等键头，默认 `Idempotency-Key` |

### 配置分层

| 环境 | 说明 |
|------|------|
| `default` | 默认安全配置，硬编码在代码中 |
| `local` | 本地开发配置，使用 `.env` 文件 |
| `test` | 自动化测试配置，使用内存数据库或测试库 |
| `staging` | 预发布环境配置 |
| `prod` | 生产环境配置 |

### 配置安全要求

- **禁止将密钥、凭证提交到仓库**
- 敏感配置（JWT密钥、数据库密码等）必须通过环境变量注入
- 提供 `.env.example` 作为配置模板，不含真实密钥
- JWT 密钥等敏感配置生产环境必须替换，禁止使用默认值 `change-me-in-production`
- 所有关键开关（发布、灰度、回滚阈值）必须配置化，不能硬编码

---

## 日志规范

### 日志库

- 必须使用 structlog 输出结构化 JSON 日志
- 日志配置在应用启动时完成（`main.py` lifespan 中）

### 日志处理器配置

structlog 必须配置以下 processors：
- `TimeStamper(fmt="iso")` - ISO格式时间戳
- `add_log_level` - 日志级别
- `StackInfoRenderer()` - 栈信息
- `format_exc_info` - 异常格式化
- `JSONRenderer()` - JSON输出

### 请求追踪

- 所有HTTP请求必须经过日志中间件，自动绑定 `request_id` 和 `trace_id` 到日志上下文
- 必须实现 `X-Request-Id` 和 `X-Trace-Id` 请求头/响应头传递
- 如果请求头中没有 request_id，服务端自动生成（格式：`req_<uuid4 hex前12位>`）
- 响应头中必须返回 `X-Request-Id` 和 `X-Trace-Id`（如果有）

### 必备日志字段

每条日志必须包含：
- `timestamp`：ISO 8601 时间戳
- `level`：日志级别
- `request_id`：请求ID（请求上下文中）
- `trace_id`：全链路追踪ID（如有）
- `method`：HTTP方法（请求上下文中）
- `path`：请求路径（请求上下文中）

### 关键业务操作必须记录审计日志

以下操作必须记录审计日志（包含操作人、操作类型、资源ID、原因等）：
- 投票提交
- 投票周期创建/状态变更
- 内容审核批准/拒绝
- 内容发布
- 内容回滚
- 其他敏感运营操作

### 日志事件命名规范

使用 snake_case 命名事件，例如：
- `service_starting` / `service_stopping`
- `request_started` / `request_completed` / `request_failed`
- `db_tables_created`
- `http_exception`
- `vote_submitted`
- `content_released`
- `content_rolled_back`

---

## 相关规则

- 数据库设计规范 → [11-database.md](./11-database.md)
- API 设计规范 → [12-api-design.md](./12-api-design.md)
- 安全规范 → [50-security.md](./50-security.md)
- 测试规范 → [41-testing.md](./41-testing.md)

# Backend Agent 技术规范

> 文档状态：active
> 适用阶段：P2（多代理协同期）
> 维护要求：持续维护

## 职责定义

Backend Agent 负责编写投票服务、生成服务、审核服务和运营后台接口。它将 System Designer Agent 的设计方案转化为可运行的后端代码。

## 输入

| 输入来源 | 格式 | 说明 |
|---------|------|------|
| design-note.md | markdown | 技术设计文档（服务端部分） |
| 现有代码 | Python | 当前服务实现 |
| API 规范 | yaml | OpenAPI 定义 |
| 数据结构 | JSON | 数据模型定义 |

### 输入数据结构

**设计任务输入**：
```json
{
  "design_id": "DESIGN-001",
  "task_id": "TASK-001",
  "title": "新增区域创建接口",
  "type": "api",
  "target_service": "world-service",
  "requirements": [
    "实现 POST /api/v1/world/regions",
    "实现 GET /api/v1/world/regions",
    "实现 GET /api/v1/world/regions/{region_id}",
    "添加权限校验 world:read/world:write",
    "实现统一响应 envelope"
  ],
  "data_model": {
    "model_name": "Region",
    "table_name": "regions",
    "fields": [...]
  }
}
```

**API 规范输入**：
```json
{
  "endpoint": "/api/v1/world/regions",
  "method": "POST",
  "scope": "world:write",
  "request": {
    "name": "CreateRegionRequest",
    "fields": [
      {"name": "name", "type": "string", "required": true},
      {"name": "description", "type": "string", "required": false},
      {"name": "region_scope", "type": "object", "required": true}
    ]
  },
  "response": {
    "name": "RegionResponse",
    "fields": [
      {"name": "region_id", "type": "string"},
      {"name": "name", "type": "string"},
      {"name": "status", "type": "string"}
    ]
  },
  "errors": [
    {"code": "REGION_ALREADY_EXISTS", "status": 409},
    {"code": "INVALID_REGION_SCOPE", "status": 400}
  ]
}
```

**数据结构输入**：
```json
{
  "model_name": "Region",
  "table_name": "regions",
  "fields": [
    {"name": "region_id", "type": "UUID", "primary_key": true},
    {"name": "name", "type": "VARCHAR(255)", "nullable": false},
    {"name": "status", "type": "VARCHAR(32)", "check": ["locked", "active", "unstable", "archived"]},
    {"name": "region_scope", "type": "JSONB", "nullable": false},
    {"name": "schema_version", "type": "INTEGER", "default": 1},
    {"name": "created_at", "type": "TIMESTAMPTZ", "server_default": "now()"},
    {"name": "updated_at", "type": "TIMESTAMPTZ", "server_default": "now()", "onupdate": "now()"}
  ],
  "constraints": [{"type": "UNIQUE", "fields": ["name"]}],
  "indexes": [{"name": "regions_status_idx", "fields": ["status"]}]
}
```

## 输出

| 输出产物 | 格式 | 说明 |
|---------|------|------|
| 路由文件 | Python | routes.py |
| 模型文件 | Python | models.py |
| 仓库文件 | Python | repositories/*.py |
| Schema 文件 | Python | schemas/*.py |
| 测试文件 | Python | tests/*.py |
| 迁移脚本 | Python | Alembic 迁移脚本 |

### 输出数据结构

**实现输出元数据**：
```json
{
  "implementation_id": "IMPLEMENT-001",
  "design_id": "DESIGN-001",
  "task_id": "TASK-001",
  "service": "world-service",
  "files": [
    {"path": "app/api/routes.py", "type": "modified", "description": "新增区域相关路由"},
    {"path": "app/domain/models.py", "type": "modified", "description": "新增 Region 模型"},
    {"path": "app/repositories/world_repo.py", "type": "modified", "description": "新增区域数据访问方法"},
    {"path": "app/schemas/world.py", "type": "modified", "description": "新增区域 schemas"},
    {"path": "tests/test_world_regions.py", "type": "new", "description": "新增区域测试用例"},
    {"path": "alembic/versions/xxx_init_regions.py", "type": "new", "description": "新增区域表迁移脚本"}
  ],
  "version": "1.0",
  "status": "completed",
  "created_at": "2026-07-07T16:00:00Z"
}
```

**测试结果输出**：
```json
{
  "test_results": {
    "service": "world-service",
    "tests": {
      "passed": 25,
      "failed": 0,
      "total": 25
    },
    "lint": {"passed": true, "errors": []},
    "typecheck": {"passed": true, "errors": []}
  }
}
```

## 核心流程

### 步骤 1：分析设计文档
- 读取 design-note.md 中服务端相关部分
- 理解 API 接口需求
- 识别数据模型和业务逻辑需求

### 步骤 2：检查现有代码
- 分析现有服务结构（routes/models/repositories/schemas）
- 识别可复用的模式和工具
- 评估改动对现有系统的影响

### 步骤 3：实现数据模型
- 根据数据结构定义更新 models.py
- 添加 SQLAlchemy 模型和关系
- 添加 CHECK 约束和索引
- 确保符合 11-database.md 规范

### 步骤 4：实现数据访问层
- 更新 repositories/*.py
- 实现 CRUD 方法
- 添加事务处理
- 确保使用 AsyncSession

### 步骤 5：实现 Pydantic Schemas
- 更新 schemas/*.py
- 实现请求/响应数据模型
- 添加字段校验（Field(ge=..., le=...)）
- 使用 ConfigDict(from_attributes=True)

### 步骤 6：实现 API 路由
- 更新 routes.py
- 实现 HTTP 端点
- 添加权限校验（JWT + Scope）
- 实现统一响应 envelope
- 添加错误处理

### 步骤 7：生成迁移脚本
- 使用 Alembic 生成迁移脚本
- 验证迁移脚本正确性
- 确保包含审计字段

### 步骤 8：编写测试用例
- 创建 tests/*.py
- 编写单元测试和集成测试
- 使用 pytest + pytest-asyncio
- 使用 httpx.AsyncClient 进行 API 测试

### 步骤 9：运行测试验证
- 执行 pytest
- 执行 ruff lint
- 执行 mypy 类型检查
- 分析失败原因，修复问题
- 重新运行测试直到全部通过

### 步骤 10：交付成果
- 将代码和测试提交到版本控制
- 通知 QA Agent 进行回归测试

## 关键能力

- FastAPI 开发
- SQLAlchemy 异步开发
- Pydantic 数据验证
- 测试驱动开发
- Alembic 数据迁移

## 协作机制

### 与 System Designer Agent
- **输入**：design-note.md（服务端部分）、接口定义、数据结构
- **输出**：实现反馈、技术问题、变更请求
- **触发条件**：服务端设计完成后

### 与 QA Agent
- **输出**：测试用例、代码变更
- **输入**：测试结果、失败摘要
- **触发条件**：测试执行完成后

### 与 Gateway Service
- **输出**：路由配置、接口定义
- **输入**：路由注册结果、代理配置
- **触发条件**：新增或修改接口后

### 与 Event Bus
- **输出**：事件发布逻辑、事件定义
- **输入**：事件发布结果
- **触发条件**：需要发布事件时

## 错误处理和异常情况

### 设计不完整
- **检测**：设计文档缺少关键信息
- **处理**：向 System Designer Agent 请求补充
- **通知**：记录设计缺失日志

### 模型冲突
- **检测**：数据模型与现有表结构冲突
- **处理**：分析冲突原因，调整模型或迁移脚本
- **通知**：记录模型冲突日志

### SQLAlchemy 错误
- **检测**：模型定义或查询语句错误
- **处理**：修复 SQLAlchemy 代码
- **通知**：记录 SQLAlchemy 错误日志

### 测试失败
- **检测**：pytest 测试未通过
- **处理**：分析失败原因，修复代码
- **通知**：记录测试失败日志

### 类型检查失败
- **检测**：mypy 类型检查未通过
- **处理**：修复类型注解或代码逻辑
- **通知**：记录类型检查错误日志

## 约束条件

- 必须遵循 10-python-backend.md 规范
- 必须遵循 11-database.md 规范
- 必须遵循 12-api-design.md 规范
- 必须编写测试用例
- 所有数据库操作必须使用异步（async/await）
- 必须使用统一响应 envelope 格式
- 必须添加 JWT 认证和 Scope 校验
- 必须记录审计日志
- 必须添加业务指标埋点

## 验收标准

- ruff 检查通过
- mypy 类型检查通过
- pytest 测试通过
- 接口响应符合 envelope 格式
- 数据模型符合数据库设计规范
- API 接口符合 API 设计规范
- 迁移脚本正确生成和执行
- 测试用例覆盖核心逻辑
- 输出格式符合规范，可被其他代理直接使用
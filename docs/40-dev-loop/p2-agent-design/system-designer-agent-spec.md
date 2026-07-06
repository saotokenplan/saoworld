# System Designer Agent 技术规范

> 文档状态：active
> 适用阶段：P2（多代理协同期）
> 维护要求：持续维护

## 职责定义

System Designer Agent 负责设计玩法系统、模块边界、数据结构和接口约束。作为连接产品需求和技术实现的桥梁，它将 version_brief.md 转化为可执行的技术方案。

## 输入

| 输入来源 | 格式 | 说明 |
|---------|------|------|
| version_brief.md | markdown | 版本需求文档 |
| 优先级矩阵 | JSON | 任务优先级排序 |
| 现有代码 | 代码 | 当前系统实现 |
| 规则库 | yaml/json | 世界规则和约束 |

### 输入数据结构

**任务输入**：
```json
{
  "task_id": "TASK-001",
  "title": "新增区域：迷雾森林",
  "priority": "P1",
  "description": "根据玩家投票结果，新增迷雾森林区域",
  "requirements": [
    "包含3个新NPC",
    "包含2个主线任务和3个支线任务",
    "支持探索和战斗玩法"
  ],
  "dependencies": [],
  "assignee": "world"
}
```

**规则库输入**：
```json
{
  "world_rules": {
    "max_region_level": 10,
    "npc_count_per_region": {"min": 2, "max": 8},
    "quest_count_per_region": {"min": 3, "max": 10}
  },
  "constraints": {
    "forbidden_tags": ["adult", "violence"],
    "reward_limits": {"gold": {"min": 10, "max": 1000}}
  }
}
```

## 输出

| 输出产物 | 格式 | 说明 |
|---------|------|------|
| design-note.md | markdown | 技术设计文档 |
| 接口定义 | yaml | API 接口规范 |
| 数据结构 | JSON | 数据模型定义 |
| 改动计划 | JSON | 模块改动清单 |
| 架构校验报告 | JSON | 设计合理性校验结果 |

### 输出数据结构

**设计文档元数据**：
```json
{
  "design_id": "DESIGN-001",
  "task_id": "TASK-001",
  "title": "迷雾森林区域设计",
  "version": "1.0",
  "status": "approved",
  "created_at": "2026-07-07T10:00:00Z",
  "author": "system-designer-agent"
}
```

**数据结构定义**：
```json
{
  "model_name": "Region",
  "table_name": "regions",
  "fields": [
    {
      "name": "region_id",
      "type": "UUID",
      "primary_key": true,
      "default": "uuid4()"
    },
    {
      "name": "name",
      "type": "VARCHAR(255)",
      "nullable": false
    },
    {
      "name": "status",
      "type": "VARCHAR(32)",
      "check": ["locked", "active", "unstable", "archived"],
      "default": "locked"
    },
    {
      "name": "region_scope",
      "type": "JSONB",
      "nullable": false
    },
    {
      "name": "schema_version",
      "type": "INTEGER",
      "default": 1
    }
  ],
  "constraints": [
    {"type": "UNIQUE", "fields": ["name"]}
  ],
  "indexes": [
    {"name": "regions_status_idx", "fields": ["status"]}
  ]
}
```

**接口定义**：
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
  }
}
```

**改动计划**：
```json
{
  "design_id": "DESIGN-001",
  "modules": [
    {
      "name": "world-service",
      "changes": [
        {"type": "add", "file": "app/domain/models.py", "description": "新增 Region 模型"},
        {"type": "add", "file": "app/schemas/world.py", "description": "新增 Region schemas"},
        {"type": "add", "file": "app/api/routes.py", "description": "新增区域创建接口"}
      ]
    },
    {
      "name": "game",
      "changes": [
        {"type": "add", "file": "scenes/world/fog_forest.tscn", "description": "新增迷雾森林场景"},
        {"type": "add", "file": "scripts/world/fog_forest.gd", "description": "新增场景脚本"}
      ]
    }
  ],
  "migrations": [
    {"type": "alembic", "description": "新增 regions 表字段"}
  ],
  "dependencies": ["world-service", "game"]
}
```

## 核心流程

### 步骤 1：分析需求
- 读取 version_brief.md 和优先级矩阵
- 理解每个任务的业务需求
- 识别跨模块需求和潜在冲突

### 步骤 2：检查现有系统
- 分析现有代码结构和模块边界
- 识别可复用的组件和接口
- 评估改动对现有系统的影响

### 步骤 3：设计系统架构
- 确定新增模块或修改范围
- 定义模块间的接口和依赖关系
- 设计数据流和状态管理

### 步骤 4：定义数据结构
- 根据需求设计数据库模型
- 定义 JSONB 字段的 schema
- 添加必要的约束和索引
- 设计审计日志字段

### 步骤 5：定义 API 接口
- 设计 RESTful API 端点
- 定义请求/响应数据结构
- 配置权限 Scope
- 定义错误码

### 步骤 6：生成改动计划
- 列出需要修改的文件清单
- 确定改动类型（新增/修改/删除）
- 规划迁移脚本
- 评估工作量和风险

### 步骤 7：架构校验
- 检查设计是否符合技术规范
- 验证接口设计是否符合 API 规范
- 检查数据结构是否符合数据库规范
- 识别潜在的性能和安全问题

### 步骤 8：交付设计文档
- 将 design-note.md 和相关输出传递给编码代理
- 等待实现反馈

## 关键能力

- 系统架构设计
- 数据结构设计
- 接口规范定义
- 模块边界划分
- 技术可行性评估

## 协作机制

### 与 Product Agent
- **输入**：version_brief.md、优先级矩阵、里程碑计划
- **输出**：设计反馈、技术可行性评估
- **触发条件**：版本目标确定后

### 与 Gameplay Agent
- **输出**：design-note.md（客户端部分）、数据结构定义
- **输入**：实现反馈、技术问题
- **触发条件**：客户端设计完成后

### 与 Backend Agent
- **输出**：design-note.md（服务端部分）、接口定义、数据结构
- **输入**：实现反馈、技术问题
- **触发条件**：服务端设计完成后

### 与 World Agent
- **输出**：design-note.md（内容部分）、规则约束
- **输入**：内容生成反馈、规则冲突
- **触发条件**：内容设计完成后

## 错误处理和异常情况

### 需求不明确
- **检测**：需求描述模糊或缺少关键信息
- **处理**：向 Product Agent 请求澄清
- **通知**：记录需求澄清日志

### 技术不可行
- **检测**：设计方案在现有技术栈下无法实现
- **处理**：提出替代方案，与 Product Agent 协商
- **通知**：生成技术风险报告

### 模块冲突
- **检测**：设计方案与现有模块存在冲突
- **处理**：分析冲突原因，调整设计方案
- **通知**：记录模块冲突日志

### 性能风险
- **检测**：设计方案存在性能隐患
- **处理**：优化设计，添加缓存或异步处理
- **通知**：生成性能风险评估报告

## 约束条件

- 设计必须符合项目技术栈约束
- 接口必须符合 API 设计规范（12-api-design.md）
- 数据结构必须符合数据库设计规范（11-database.md）
- 必须考虑向后兼容性
- 必须遵循 MVP 原则，避免过度设计

## 验收标准

- design-note.md 包含：改动模块清单、数据结构变化、接口增量、风险说明
- 接口定义符合 12-api-design.md 规范
- 数据结构符合 11-database.md 规范
- 改动计划清晰，可被编码代理直接执行
- 架构校验报告显示设计合理
- 输出格式符合规范，可被其他代理直接使用
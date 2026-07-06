# Orchestrator 技术规范

> 文档状态：active
> 适用阶段：P2（多代理协同期）
> 维护要求：持续维护

## 职责定义

Orchestrator 负责统一调度所有代理，管理任务状态和执行流程。它不是写业务代码，而是负责任务分配、状态管理、失败处理和门禁校验。

## 输入

| 输入来源 | 格式 | 说明 |
|---------|------|------|
| 需求包 | markdown | version_brief.md |
| 门禁结果 | JSON | CI/CD 门禁状态 |
| 代理状态 | JSON | 各代理的执行状态 |
| 任务定义 | JSON | 任务与代理的映射 |

### 输入数据结构

**需求包输入**：
```json
{
  "version_brief_id": "VB-001",
  "version": "0.2.0",
  "objectives": ["新增迷雾森林区域", "优化投票提交性能"],
  "milestones": [
    {"id": "M1", "name": "设计完成", "due_date": "2026-07-10"},
    {"id": "M2", "name": "开发完成", "due_date": "2026-07-18"},
    {"id": "M3", "name": "测试完成", "due_date": "2026-07-22"},
    {"id": "M4", "name": "发布", "due_date": "2026-07-25"}
  ],
  "tasks": [
    {"id": "TASK-001", "title": "设计迷雾森林区域", "priority": "P1", "assignee": "system-designer"},
    {"id": "TASK-002", "title": "实现区域创建接口", "priority": "P1", "assignee": "backend"},
    {"id": "TASK-003", "title": "创建区域场景", "priority": "P1", "assignee": "gameplay"},
    {"id": "TASK-004", "title": "生成区域内容", "priority": "P1", "assignee": "world"},
    {"id": "TASK-005", "title": "优化投票提交性能", "priority": "P0", "assignee": "backend"}
  ]
}
```

**门禁结果输入**：
```json
{
  "gate_results": {
    "world-service": {
      "lint": {"status": "pass", "timestamp": "2026-07-07T16:00:00Z"},
      "typecheck": {"status": "pass", "timestamp": "2026-07-07T16:05:00Z"},
      "tests": {"status": "pass", "timestamp": "2026-07-07T16:15:00Z"}
    },
    "game": {
      "tests": {"status": "pass", "timestamp": "2026-07-07T17:00:00Z"}
    }
  }
}
```

**代理状态输入**：
```json
{
  "agent_status": {
    "product-agent": {"status": "idle", "current_task": null},
    "system-designer-agent": {"status": "busy", "current_task": "TASK-001"},
    "gameplay-agent": {"status": "idle", "current_task": null},
    "world-agent": {"status": "idle", "current_task": null},
    "backend-agent": {"status": "busy", "current_task": "TASK-005"},
    "qa-agent": {"status": "idle", "current_task": null},
    "build-agent": {"status": "idle", "current_task": null},
    "ops-agent": {"status": "running", "current_task": "health_check"}
  }
}
```

**任务定义输入**：
```json
{
  "task_definitions": [
    {
      "task_id": "TASK-001",
      "title": "设计迷雾森林区域",
      "type": "design",
      "agent": "system-designer-agent",
      "inputs": ["version_brief.md"],
      "outputs": ["design-note.md"],
      "dependencies": [],
      "status": "in_progress"
    },
    {
      "task_id": "TASK-002",
      "title": "实现区域创建接口",
      "type": "implementation",
      "agent": "backend-agent",
      "inputs": ["design-note.md"],
      "outputs": ["routes.py", "models.py", "tests.py"],
      "dependencies": ["TASK-001"],
      "status": "pending"
    }
  ]
}
```

## 输出

| 输出产物 | 格式 | 说明 |
|---------|------|------|
| 任务分配 | JSON | 任务与代理的映射 |
| 执行日志 | JSON | 任务执行记录 |
| 失败处理 | JSON | 失败任务和重试策略 |
| 进度报告 | JSON | 整体进度和状态 |

### 输出数据结构

**任务分配输出**：
```json
{
  "assignment_id": "ASSIGN-001",
  "task_id": "TASK-002",
  "agent": "backend-agent",
  "inputs": {
    "design_note": "design-note/DESIGN-001.md",
    "api_spec": "api-spec/REGION-API.yaml",
    "data_model": "data-model/REGION.json"
  },
  "deadline": "2026-07-12T23:59:59Z",
  "priority": "P1",
  "status": "assigned",
  "assigned_at": "2026-07-07T16:00:00Z"
}
```

**执行日志输出**：
```json
{
  "log_id": "LOG-001",
  "task_id": "TASK-001",
  "agent": "system-designer-agent",
  "events": [
    {"timestamp": "2026-07-07T10:00:00Z", "event": "task_started", "details": "开始设计迷雾森林区域"},
    {"timestamp": "2026-07-07T12:00:00Z", "event": "progress", "details": "完成数据结构设计"},
    {"timestamp": "2026-07-07T14:00:00Z", "event": "progress", "details": "完成接口定义"},
    {"timestamp": "2026-07-07T16:00:00Z", "event": "task_completed", "details": "设计完成"}
  ],
  "status": "completed",
  "duration": "6h"
}
```

**失败处理输出**：
```json
{
  "failure_id": "FAIL-001",
  "task_id": "TASK-002",
  "agent": "backend-agent",
  "error": {
    "type": "test_failure",
    "message": "pytest 测试未通过",
    "details": "test_create_region_success: AssertionError"
  },
  "retry_count": 2,
  "max_retries": 3,
  "retry_strategy": "exponential_backoff",
  "next_retry_time": "2026-07-07T18:00:00Z",
  "status": "retrying"
}
```

**进度报告输出**：
```json
{
  "report_id": "PROGRESS-001",
  "version": "0.2.0",
  "timestamp": "2026-07-07T22:00:00Z",
  "tasks": {
    "total": 5,
    "completed": 1,
    "in_progress": 2,
    "pending": 2,
    "failed": 0
  },
  "milestones": [
    {"id": "M1", "name": "设计完成", "status": "completed", "progress": 100},
    {"id": "M2", "name": "开发完成", "status": "in_progress", "progress": 40},
    {"id": "M3", "name": "测试完成", "status": "pending", "progress": 0},
    {"id": "M4", "name": "发布", "status": "pending", "progress": 0}
  ],
  "overall_progress": 30,
  "risks": []
}
```

## 核心流程

### 步骤 1：接收需求包
- 从 Product Agent 获取 version_brief.md
- 解析需求包内容
- 提取任务列表和里程碑

### 步骤 2：分析任务依赖
- 构建任务依赖图
- 识别依赖关系
- 检测循环依赖

### 步骤 3：分配任务
- 根据任务类型选择合适的代理
- 考虑代理当前状态和负载
- 分配任务并设置截止时间

### 步骤 4：执行任务
- 通知代理开始执行任务
- 监控代理执行状态
- 收集执行日志

### 步骤 5：检查门禁
- 在关键节点检查门禁状态
- 如果门禁未通过，阻断继续推进
- 如果门禁通过，继续下一个任务

### 步骤 6：处理失败
- 当任务失败时，根据重试策略处理
- 如果重试次数用尽，升级为高风险任务
- 记录失败原因和处理过程

### 步骤 7：更新进度
- 更新任务状态
- 更新里程碑进度
- 生成进度报告

### 步骤 8：完成阶段
- 当所有任务完成时，通知相关代理
- 生成阶段总结报告
- 准备下一阶段

## 关键能力

- 任务调度和分配
- 状态管理
- 失败处理和重试
- 门禁校验和阻断
- 进度跟踪

## 协作机制

### 与 Product Agent
- **输入**：version_brief.md、优先级矩阵
- **输出**：进度报告、需求反馈
- **触发条件**：版本目标确定后

### 与 System Designer Agent
- **输入**：设计任务分配
- **输出**：设计完成通知、设计文档
- **触发条件**：设计任务分配后

### 与 Gameplay Agent
- **输入**：客户端开发任务分配
- **输出**：开发完成通知、代码变更
- **触发条件**：客户端开发任务分配后

### 与 Backend Agent
- **输入**：服务端开发任务分配
- **输出**：开发完成通知、代码变更
- **触发条件**：服务端开发任务分配后

### 与 World Agent
- **输入**：内容生成任务分配
- **输出**：内容生成完成通知、内容包
- **触发条件**：内容生成任务分配后

### 与 QA Agent
- **输入**：测试任务分配
- **输出**：测试报告、失败摘要
- **触发条件**：测试任务分配后

### 与 Build Agent
- **输入**：构建任务分配
- **输出**：构建报告、版本信息
- **触发条件**：构建任务分配后

### 与 Ops Agent
- **输入**：运维任务分配
- **输出**：健康报告、告警汇总
- **触发条件**：运维任务分配后

## 错误处理和异常情况

### 任务分配失败
- **检测**：无法分配任务给任何代理
- **处理**：等待代理空闲或调整任务优先级
- **通知**：记录任务分配失败日志

### 代理无响应
- **检测**：代理在超时时间内未响应
- **处理**：重试或切换到备用代理
- **通知**：记录代理无响应日志

### 门禁失败
- **检测**：CI/CD 门禁未通过
- **处理**：阻断继续推进，通知相关代理修复
- **通知**：记录门禁失败日志

### 任务超时
- **检测**：任务执行时间超过截止时间
- **处理**：提醒代理或重新分配任务
- **通知**：记录任务超时日志

### 循环依赖
- **检测**：任务之间存在循环依赖
- **处理**：分析依赖关系，打破循环
- **通知**：记录循环依赖日志

## 约束条件

- 必须确保任务有序执行
- 必须处理依赖关系
- 必须支持重试和回滚
- 必须提供可观测性
- 必须在门禁不通过时阻断继续推进
- 必须记录所有执行日志
- 必须支持任务优先级

## 验收标准

- 任务正确分配给对应代理
- 执行流程有序推进
- 失败任务正确重试或阻断
- 执行日志完整可追溯
- 进度报告准确反映当前状态
- 门禁检查正确执行
- 输出格式符合规范，可被其他代理直接使用
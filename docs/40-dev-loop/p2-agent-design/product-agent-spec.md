# Product Agent 技术规范

> 文档状态：active
> 适用阶段：P2（多代理协同期）
> 维护要求：持续维护

## 职责定义

Product Agent 负责读取目标、玩家反馈和路线图，输出版本需求和优先级。作为研发闭环的入口，它将高层愿景转化为具体可执行的版本计划。

## 输入

| 输入来源 | 格式 | 说明 |
|---------|------|------|
| 愿景文档 | markdown | 项目长期愿景和目标 |
| 版本状态 | JSON | 当前版本状态和进度 |
| 玩家投票结果 | JSON | 玩家投票数据和结果 |
| 线上数据 | JSON | 玩家行为数据和指标 |
| 问题列表 | JSON | 待修复问题和改进建议 |
| 路线图 | JSON | 长期发展规划 |

### 输入数据结构

**版本状态输入**：
```json
{
  "version": "0.1.0",
  "status": "in_progress",
  "completed_tasks": 45,
  "total_tasks": 60,
  "blockers": ["BLOCKER-001"],
  "milestones": [
    {
      "id": "M1",
      "name": "投票链路完成",
      "due_date": "2026-07-10",
      "completed": true
    }
  ]
}
```

**玩家投票结果输入**：
```json
{
  "vote_cycle_id": "vc_20260701",
  "winning_candidate_id": "candidate_003",
  "results": [
    {"candidate_id": "candidate_001", "votes": 150, "percentage": 30},
    {"candidate_id": "candidate_002", "votes": 200, "percentage": 40},
    {"candidate_id": "candidate_003", "votes": 150, "percentage": 30}
  ],
  "total_voters": 500
}
```

**线上数据输入**：
```json
{
  "metrics": {
    "daily_active_users": 1200,
    "vote_participation_rate": 0.65,
    "task_completion_rate": 0.72,
    "new_content_stay_time": 45,
    "crash_rate": 0.015
  },
  "trends": {
    "user_growth": "up",
    "engagement": "stable",
    "content_consumption": "up"
  }
}
```

**问题列表输入**：
```json
{
  "issues": [
    {
      "id": "ISSUE-001",
      "title": "投票提交响应慢",
      "severity": "high",
      "type": "performance",
      "status": "open"
    },
    {
      "id": "ISSUE-002",
      "title": "NPC 对话重复",
      "severity": "medium",
      "type": "content",
      "status": "open"
    }
  ]
}
```

## 输出

| 输出产物 | 格式 | 说明 |
|---------|------|------|
| version_brief.md | markdown | 版本需求文档 |
| 优先级矩阵 | JSON | 任务优先级排序 |
| 里程碑计划 | JSON | 版本里程碑和时间线 |

### 输出数据结构

**优先级矩阵输出**：
```json
{
  "version": "0.2.0",
  "tasks": [
    {
      "id": "TASK-001",
      "title": "优化投票提交性能",
      "priority": "P0",
      "size": "small",
      "dependencies": [],
      "estimated_hours": 8,
      "assignee": "backend"
    },
    {
      "id": "TASK-002",
      "title": "新增区域：迷雾森林",
      "priority": "P1",
      "size": "large",
      "dependencies": [],
      "estimated_hours": 40,
      "assignee": "world"
    }
  ]
}
```

**里程碑计划输出**：
```json
{
  "version": "0.2.0",
  "milestones": [
    {
      "id": "M1",
      "name": "性能优化完成",
      "due_date": "2026-07-15",
      "tasks": ["TASK-001"],
      "status": "pending"
    },
    {
      "id": "M2",
      "name": "新区域上线",
      "due_date": "2026-07-25",
      "tasks": ["TASK-002"],
      "status": "pending"
    }
  ]
}
```

## 核心流程

### 步骤 1：收集输入数据
- 从知识库读取愿景文档和路线图
- 从项目管理系统获取当前版本状态
- 从 vote-service 获取最新投票结果
- 从监控系统获取线上数据指标
- 从 issue 追踪系统获取待修复问题

### 步骤 2：分析当前状态
- 评估当前版本进度和阻塞问题
- 分析玩家投票倾向和需求
- 识别线上数据中的异常和趋势
- 综合问题列表的严重程度

### 步骤 3：确定版本目标
- 基于投票结果确定本轮核心方向
- 根据线上数据识别优化重点
- 结合问题列表确定修复优先级
- 定义"做什么"和"不做什么"

### 步骤 4：生成 version_brief.md
- 编写本期目标（3-5条核心目标）
- 编写不做什么（明确范围边界）
- 定义核心指标（成功标准）
- 列出关键风险和应对策略
- 定义验收口径

### 步骤 5：拆解任务并排序
- 将版本目标拆分为可执行任务
- 评估任务依赖关系
- 按优先级排序（P0 > P1 > P2 > P3）
- 估算任务工作量

### 步骤 6：生成里程碑计划
- 将任务按时间线分组
- 定义每个里程碑的完成标准
- 设定截止日期
- 识别关键路径任务

### 步骤 7：交付给 System Designer Agent
- 将 version_brief.md 和优先级矩阵传递给 System Designer Agent
- 等待设计反馈和确认

## 关键能力

- 需求分析和优先级评估
- 玩家反馈分析
- 版本规划和里程碑制定
- 跨团队协调
- 风险识别和评估

## 协作机制

### 与 System Designer Agent
- **输出**：version_brief.md、优先级矩阵、里程碑计划
- **输入**：设计反馈、技术可行性评估
- **触发条件**：版本目标确定后

### 与 Ops Agent
- **输入**：异常报告、改进建议
- **触发条件**：线上数据采集周期结束后

### 与 World Agent
- **输入**：内容生成需求反馈
- **触发条件**：投票结果可用后

## 错误处理和异常情况

### 输入数据缺失
- **检测**：检查输入数据完整性
- **处理**：使用默认值或历史数据
- **通知**：记录警告日志，通知 Ops Agent

### 数据冲突
- **检测**：投票结果与线上数据趋势不一致
- **处理**：进行二次验证，优先信任投票结果
- **通知**：记录冲突日志，通知 Product Owner

### 目标无法实现
- **检测**：评估后发现资源不足或技术不可行
- **处理**：调整目标或延长时间线
- **通知**：生成风险报告，通知管理层

### 紧急问题插入
- **检测**：严重线上问题需要立即处理
- **处理**：重新评估优先级，插入紧急任务
- **通知**：更新版本计划，通知相关代理

## 约束条件

- 输出必须符合项目规范格式
- 任务粒度控制在可执行范围内（每项 < 1 天规模）
- 必须考虑资源限制和依赖关系
- 版本目标必须与长期路线图对齐
- 必须遵循 MVP 原则，避免功能膨胀

## 验收标准

- version_brief.md 包含：本期目标、不做什么、核心指标、关键风险、验收口径
- 优先级矩阵合理，关键任务优先
- 里程碑计划可行，时间线合理
- 任务依赖关系清晰，无循环依赖
- 输出格式符合规范，可被其他代理直接使用
# Ops Agent 技术规范

> 文档状态：active
> 适用阶段：P2（多代理协同期）
> 维护要求：持续维护

## 职责定义

Ops Agent 负责读取监控和线上数据，归纳问题并形成下一轮输入。它确保系统稳定运行，并将运维数据转化为产品改进需求。

## 输入

| 输入来源 | 格式 | 说明 |
|---------|------|------|
| 监控数据 | JSON | Prometheus/Grafana 指标 |
| 日志数据 | JSON | 结构化日志 |
| 线上异常 | JSON | 崩溃、错误、性能问题 |
| 玩家反馈 | JSON | 玩家报告和建议 |

### 输入数据结构

**监控数据输入**：
```json
{
  "metrics": {
    "services": {
      "vote-service": {
        "http_requests_total": 100000,
        "http_errors_total": 50,
        "http_request_duration_seconds": {"p95": 0.3, "p99": 0.5},
        "vote_submissions_total": 50000,
        "vote_cycles_by_status": {"open": 1, "closed": 10}
      },
      "world-service": {
        "http_requests_total": 80000,
        "http_errors_total": 30,
        "http_request_duration_seconds": {"p95": 0.2, "p99": 0.4}
      }
    },
    "system": {
      "cpu_usage": 60,
      "memory_usage": 75,
      "disk_usage": 45,
      "network_latency": 50
    },
    "gameplay": {
      "daily_active_users": 1200,
      "vote_participation_rate": 0.65,
      "task_completion_rate": 0.72,
      "new_content_stay_time": 45,
      "crash_rate": 0.015
    }
  },
  "timestamp": "2026-07-07T22:00:00Z"
}
```

**日志数据输入**：
```json
{
  "logs": [
    {
      "timestamp": "2026-07-07T22:00:00Z",
      "level": "ERROR",
      "service": "vote-service",
      "request_id": "req_abc123",
      "error_code": "INTERNAL_ERROR",
      "message": "Database connection failed",
      "stack_trace": "..."
    },
    {
      "timestamp": "2026-07-07T22:01:00Z",
      "level": "WARNING",
      "service": "gateway-service",
      "request_id": "req_abc124",
      "message": "Rate limit exceeded for player_xxx"
    }
  ]
}
```

**线上异常输入**：
```json
{
  "exceptions": [
    {
      "exception_id": "EXC-001",
      "type": "crash",
      "service": "client",
      "platform": "windows",
      "count": 15,
      "impacted_users": 12,
      "stack_trace": "...",
      "first_occurrence": "2026-07-07T20:00:00Z",
      "last_occurrence": "2026-07-07T22:00:00Z"
    },
    {
      "exception_id": "EXC-002",
      "type": "performance",
      "service": "vote-service",
      "endpoint": "/api/v1/votes/submit",
      "avg_response_time": 2.5,
      "threshold": 1.0,
      "impacted_users": 500,
      "first_occurrence": "2026-07-07T21:00:00Z",
      "last_occurrence": "2026-07-07T22:00:00Z"
    }
  ]
}
```

**玩家反馈输入**：
```json
{
  "feedback_items": [
    {
      "feedback_id": "FB-001",
      "player_id": "player_xxx",
      "type": "bug",
      "title": "投票提交失败",
      "description": "点击提交按钮后没有反应",
      "severity": "high",
      "status": "open",
      "created_at": "2026-07-07T21:30:00Z"
    },
    {
      "feedback_id": "FB-002",
      "player_id": "player_yyy",
      "type": "feature_request",
      "title": "希望增加地图标记功能",
      "description": "在世界地图上标记已探索区域",
      "severity": "medium",
      "status": "pending",
      "created_at": "2026-07-07T20:00:00Z"
    }
  ]
}
```

## 输出

| 输出产物 | 格式 | 说明 |
|---------|------|------|
| 异常报告 | markdown | 线上异常分析报告 |
| 改进建议 | JSON | 下一轮需求输入 |
| 告警汇总 | JSON | 告警统计和趋势 |
| 服务健康报告 | JSON | 各服务健康状态 |

### 输出数据结构

**异常报告输出**：
```json
{
  "report_id": "EXCEPTION-REPORT-001",
  "timestamp": "2026-07-07T22:00:00Z",
  "exceptions": [
    {
      "exception_id": "EXC-001",
      "type": "crash",
      "service": "client",
      "description": "Windows 客户端崩溃",
      "impact": {"users": 12, "count": 15},
      "root_cause": "内存泄漏",
      "suggestion": "优化内存使用，添加内存监控",
      "priority": "high"
    },
    {
      "exception_id": "EXC-002",
      "type": "performance",
      "service": "vote-service",
      "description": "投票提交响应慢",
      "impact": {"users": 500, "avg_time": "2.5s"},
      "root_cause": "数据库查询优化不足",
      "suggestion": "添加索引，优化查询",
      "priority": "high"
    }
  ],
  "summary": {"total_exceptions": 2, "high_priority": 2, "medium_priority": 0}
}
```

**改进建议输出**：
```json
{
  "suggestions": [
    {
      "suggestion_id": "SUGG-001",
      "title": "优化投票提交性能",
      "description": "投票提交接口响应时间超过阈值，需要优化数据库查询",
      "priority": "P0",
      "source": "performance_monitor",
      "data_support": {"avg_response_time": 2.5, "threshold": 1.0, "impacted_users": 500},
      "target_agent": "backend"
    },
    {
      "suggestion_id": "SUGG-002",
      "title": "增加地图标记功能",
      "description": "玩家希望在世界地图上标记已探索区域",
      "priority": "P2",
      "source": "player_feedback",
      "data_support": {"votes": 150},
      "target_agent": "gameplay"
    }
  ]
}
```

**告警汇总输出**：
```json
{
  "alert_summary": {
    "timestamp": "2026-07-07T22:00:00Z",
    "period": "24h",
    "alerts": {
      "total": 15,
      "critical": 2,
      "high": 5,
      "medium": 6,
      "low": 2
    },
    "trends": {
      "increasing": ["vote-service_errors", "client_crashes"],
      "decreasing": ["world-service_errors"],
      "stable": ["gateway-service_errors"]
    },
    "top_alerts": [
      {"service": "vote-service", "type": "performance", "count": 5},
      {"service": "client", "type": "crash", "count": 3}
    ]
  }
}
```

**服务健康报告输出**：
```json
{
  "health_report": {
    "timestamp": "2026-07-07T22:00:00Z",
    "services": {
      "vote-service": {"status": "healthy", "errors": 50, "latency": "0.3s"},
      "world-service": {"status": "healthy", "errors": 30, "latency": "0.2s"},
      "content-service": {"status": "degraded", "errors": 100, "latency": "0.8s"},
      "gateway-service": {"status": "healthy", "errors": 20, "latency": "0.1s"}
    },
    "overall_status": "degraded",
    "issues": ["content-service 错误率过高"]
  }
}
```

## 核心流程

### 步骤 1：采集监控数据
- 从 Prometheus 获取指标数据
- 从日志系统获取结构化日志
- 从异常追踪系统获取线上异常
- 从玩家反馈系统获取反馈

### 步骤 2：分析异常模式
- 识别异常类型（崩溃、错误、性能）
- 分析异常发生频率和趋势
- 识别受影响的用户范围
- 关联相关日志和指标

### 步骤 3：归纳问题和趋势
- 按服务和类型分组问题
- 识别问题之间的关联
- 分析趋势（增加、减少、稳定）
- 评估问题严重程度

### 步骤 4：生成异常报告
- 编写问题描述
- 分析根因
- 提供改进建议
- 设定优先级

### 步骤 5：形成改进建议
- 将问题转化为需求
- 评估需求优先级
- 确定目标代理
- 提供数据支持

### 步骤 6：生成告警汇总
- 统计告警数量和等级
- 分析告警趋势
- 识别高频告警
- 生成告警统计报告

### 步骤 7：生成服务健康报告
- 评估各服务健康状态
- 识别降级服务
- 生成整体健康状态
- 提供问题列表

### 步骤 8：提交给 Product Agent
- 将改进建议传递给 Product Agent
- 作为下一轮需求输入
- 等待 Product Agent 反馈

## 关键能力

- 监控数据分析
- 日志分析
- 异常检测和分类
- 趋势分析
- 报告生成

## 协作机制

### 与 Product Agent
- **输出**：异常报告、改进建议
- **输入**：需求反馈、优先级确认
- **触发条件**：数据采集周期结束后

### 与 Build Agent
- **输入**：部署请求、目标环境
- **输出**：部署结果、服务状态
- **触发条件**：部署执行前

### 与 Orchestrator
- **输入**：运维任务分配
- **输出**：健康报告、告警汇总
- **触发条件**：运维检查完成后

### 与监控系统
- **输入**：监控指标、日志、异常
- **输出**：查询请求、配置更新
- **触发条件**：定期数据采集

## 错误处理和异常情况

### 数据采集失败
- **检测**：无法从监控系统获取数据
- **处理**：重试或使用缓存数据
- **通知**：记录数据采集失败日志

### 数据不一致
- **检测**：不同数据源的数据不一致
- **处理**：验证数据，优先信任更可靠的数据源
- **通知**：记录数据不一致日志

### 告警风暴
- **检测**：短时间内大量告警
- **处理**：合并相似告警，抑制重复告警
- **通知**：记录告警风暴日志

### 分析失败
- **检测**：无法完成异常分析
- **处理**：使用简化分析或跳过
- **通知**：记录分析失败日志

### 报告生成失败
- **检测**：无法生成报告
- **处理**：使用默认报告模板或简化报告
- **通知**：记录报告生成失败日志

## 约束条件

- 必须遵循 telemetry/ 规范
- 报告必须结构化
- 必须关联到具体问题
- 必须提供可操作的建议
- 必须定期执行数据采集和分析
- 必须支持告警阈值配置
- 必须提供趋势分析

## 验收标准

- 异常报告包含：问题描述、影响范围、根因分析、建议
- 改进建议可被 Product Agent 使用
- 告警汇总准确反映系统状态
- 服务健康报告准确评估各服务状态
- 报告生成及时，符合周期要求
- 输出格式符合规范，可被其他代理直接使用
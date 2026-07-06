# QA Agent 技术规范

> 文档状态：active
> 适用阶段：P2（多代理协同期）
> 维护要求：持续维护

## 职责定义

QA Agent 负责编写和执行自动化测试、试玩脚本、回归检查。它确保所有代码变更和内容生成都经过充分验证。

## 输入

| 输入来源 | 格式 | 说明 |
|---------|------|------|
| 需求文档 | markdown | version_brief.md |
| 验收用例 | markdown | acceptance.md |
| 代码变更 | 代码 | 新增或修改的代码 |
| 设计文档 | markdown | design-note.md |

### 输入数据结构

**测试任务输入**：
```json
{
  "test_task_id": "TEST-001",
  "design_id": "DESIGN-001",
  "task_id": "TASK-001",
  "title": "区域创建接口测试",
  "target_service": "world-service",
  "test_type": "integration",
  "requirements": [
    "测试区域创建成功",
    "测试区域名称重复",
    "测试权限校验",
    "测试响应 envelope 格式"
  ],
  "code_changes": [
    {"path": "app/api/routes.py", "type": "modified"},
    {"path": "app/domain/models.py", "type": "modified"}
  ]
}
```

**验收用例输入**：
```json
{
  "acceptance_id": "ACC-001",
  "task_id": "TASK-001",
  "title": "区域创建验收",
  "scenarios": [
    {
      "id": "SCENARIO-001",
      "description": "管理员创建区域",
      "steps": [
        {"action": "POST /api/v1/world/regions", "data": {"name": "迷雾森林"}},
        {"expected": "status_code == 200"},
        {"expected": "response contains region_id"}
      ]
    },
    {
      "id": "SCENARIO-002",
      "description": "普通玩家创建区域",
      "steps": [
        {"action": "POST /api/v1/world/regions", "data": {"name": "迷雾森林"}},
        {"expected": "status_code == 403"}
      ]
    }
  ]
}
```

**代码变更输入**：
```json
{
  "changes": [
    {
      "file": "services/world/app/api/routes.py",
      "type": "modified",
      "diff": "...",
      "commit_hash": "abc123"
    },
    {
      "file": "services/world/tests/test_world_regions.py",
      "type": "new",
      "diff": "...",
      "commit_hash": "abc123"
    }
  ]
}
```

## 输出

| 输出产物 | 格式 | 说明 |
|---------|------|------|
| 单元测试 | Python/.gd | 单元测试用例 |
| 集成测试 | Python/.gd | 集成测试用例 |
| E2E 测试 | Python | 端到端测试用例 |
| 测试报告 | JSON/markdown | 测试结果报告 |
| 失败摘要 | JSON | 失败分析和修复建议 |

### 输出数据结构

**测试用例输出**：
```json
{
  "test_file": "tests/test_world_regions.py",
  "tests": [
    {
      "name": "test_create_region_success",
      "description": "验证区域创建成功",
      "type": "integration",
      "steps": [
        {"action": "create test client"},
        {"action": "send POST /api/v1/world/regions"},
        {"assert": "response.status_code == 200"},
        {"assert": "response.data.region_id is not None"}
      ]
    },
    {
      "name": "test_create_region_duplicate",
      "description": "验证区域名称重复返回错误",
      "type": "integration",
      "steps": [
        {"action": "create test client"},
        {"action": "send POST /api/v1/world/regions (first)"},
        {"action": "send POST /api/v1/world/regions (second)"},
        {"assert": "response.status_code == 409"},
        {"assert": "response.code == 'REGION_ALREADY_EXISTS'"}
      ]
    }
  ]
}
```

**测试报告输出**：
```json
{
  "report_id": "REPORT-001",
  "test_task_id": "TEST-001",
  "timestamp": "2026-07-07T18:00:00Z",
  "results": {
    "world-service": {
      "unit_tests": {"passed": 15, "failed": 0, "total": 15},
      "integration_tests": {"passed": 10, "failed": 0, "total": 10},
      "lint": {"passed": true, "errors": []},
      "typecheck": {"passed": true, "errors": []}
    }
  },
  "summary": {
    "overall_status": "pass",
    "total_passed": 25,
    "total_failed": 0,
    "total_tests": 25
  }
}
```

**失败摘要输出**：
```json
{
  "failure_id": "FAILURE-001",
  "test_name": "test_create_region_success",
  "service": "world-service",
  "error_type": "AssertionError",
  "error_message": "Expected status_code == 200, got 500",
  "stack_trace": "...",
  "suggestion": "检查数据库连接配置，可能是测试数据库未正确初始化",
  "related_tests": ["test_create_region_duplicate"],
  "priority": "high"
}
```

## 核心流程

### 步骤 1：分析需求和代码变更
- 读取需求文档和验收用例
- 分析代码变更内容
- 识别需要测试的功能点

### 步骤 2：编写测试用例
- 根据验收用例编写测试
- 覆盖正常路径和异常路径
- 编写单元测试和集成测试
- 确保测试用例可重复执行

### 步骤 3：运行测试
- 执行 pytest（后端）或 GUT（客户端）
- 执行 lint 和 typecheck
- 收集测试结果

### 步骤 4：分析测试结果
- 统计通过和失败的测试
- 分析失败原因
- 生成失败摘要

### 步骤 5：触发修复流程
- 将失败摘要发送给对应编码代理
- 等待修复完成
- 重新运行失败的测试

### 步骤 6：生成测试报告
- 汇总测试结果
- 生成结构化报告
- 通知 Orchestrator 测试结果

### 步骤 7：回归测试
- 在代码变更后执行回归测试
- 确保现有功能不受影响
- 生成回归测试报告

## 关键能力

- 测试用例编写
- 测试执行和报告
- 失败分析和摘要生成
- 回归测试管理

## 协作机制

### 与 Gameplay Agent
- **输入**：测试用例、代码变更
- **输出**：测试结果、失败摘要
- **触发条件**：客户端代码变更后

### 与 Backend Agent
- **输入**：测试用例、代码变更
- **输出**：测试结果、失败摘要
- **触发条件**：服务端代码变更后

### 与 World Agent
- **输入**：内容包、审核结果
- **输出**：内容测试结果、失败摘要
- **触发条件**：内容生成完成后

### 与 Orchestrator
- **输入**：测试任务分配
- **输出**：测试报告、失败摘要
- **触发条件**：测试执行完成后

## 错误处理和异常情况

### 测试环境问题
- **检测**：测试数据库未启动或配置错误
- **处理**：等待环境就绪或修复配置
- **通知**：记录环境错误日志

### 测试用例缺失
- **检测**：核心功能缺少测试覆盖
- **处理**：编写补充测试用例
- **通知**：记录测试覆盖不足日志

### 测试不稳定
- **检测**：测试结果不一致（flaky tests）
- **处理**：分析原因，修复不稳定的测试
- **通知**：记录 flaky tests 日志

### 测试超时
- **检测**：测试执行时间超过阈值
- **处理**：优化测试或增加超时时间
- **通知**：记录测试超时日志

### 修复失败
- **检测**：编码代理多次修复仍未通过测试
- **处理**：升级为高优先级问题，通知人工介入
- **通知**：记录修复失败日志

## 约束条件

- 测试必须覆盖核心功能
- 必须遵循 41-testing.md 规范
- 测试必须可重复执行
- 失败必须可追溯
- 测试报告必须结构化
- 失败摘要必须包含修复建议
- 回归测试必须覆盖所有关键路径

## 验收标准

- 测试用例覆盖核心功能
- 测试全部通过
- 测试报告清晰完整
- 失败摘要结构化
- 回归测试覆盖所有关键路径
- 测试执行时间在合理范围内
- 输出格式符合规范，可被其他代理直接使用
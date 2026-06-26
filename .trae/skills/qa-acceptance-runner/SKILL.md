# qa-acceptance-runner

## 目标

围绕需求包、改动范围和现有门禁，组织验收检查、回归脚本和结果归档，输出可追踪的通过、失败或阻塞结论。重点是让“这轮改动是否达到可交付状态”有结构化证据，而不是只给口头判断。

## 适用场景

- 功能开发后需要做最小验收与回归
- 接口、数据模型或内容对象变更后需要选择并运行相关门禁
- 提交前需要整理测试证据、失败摘要和阻塞项
- 某轮改动需要确认是否满足 `acceptance.md`、内容检查和回滚前置条件

## 规范来源

- 主要来源：
  - `docs/20-specs/agent-loop-spec.md`
  - `docs/20-specs/engineering-conventions.md`
- 次要来源：
  - `docs/20-specs/backend-data-spec.md`
  - `docs/20-specs/content-generation-spec.md`
  - `docs/30-api/openapi-draft.md`
  - `docs/40-dev-loop/gate_registry.yaml`
- 说明：
  - 验收、门禁、修复计划和失败反馈闭环以 `agent-loop-spec.md` 为准
  - 测试组织、仓库协作和交付底线参考 `engineering-conventions.md`
  - 服务接口、任务链路和性能基线相关检查参考 `backend-data-spec.md`
  - 内容对象、生命周期和内容检查相关门禁参考 `content-generation-spec.md`
  - 接口契约、请求响应样例和 OpenAPI 草案同步检查参考 `openapi-draft.md`
  - 现有 gate 范围和触发预算参考 `gate_registry.yaml`

## 输入

- `spec.md`
- `acceptance.md`
- `tasks.md`
- 当前改动范围或受影响模块
- 相关测试套件、脚本和 gate 清单
- 当前 CI、本地或预发运行日志
- 涉及接口或内容变更时的契约文档

## 输出

- `acceptance-report.md`
- `regression-report.md`
- `gate-run-summary.md`
- `failing-cases.md`
- 必要时输出 `fix-plan.md`
- 若发现重复失败模式，输出 `gate-improvement-input.md`

## 工作流程

1. 读取需求包，确认本轮要覆盖的验收语句
2. 根据改动范围映射最小充分测试集和 gate 集
3. 优先执行高价值、低成本的检查，再补高风险专项门禁
4. 记录通过、失败、阻塞和未覆盖项
5. 若失败可直接修复，则给出修复建议；若重复出现，则整理改进输入
6. 输出面向人类与后续 Agent 的验收结论和证据摘要

## 验收原则

- 验收语句必须映射到可观察的测试信号、门禁结果或结构化检查结果
- 回归范围优先按改动影响面选择，不默认全量跑完所有门禁
- 代码、内容和接口变更应分别选择对应检查，不混成单一结论
- 发现文档、样例或 OpenAPI 草案未同步时，必须在结果中明确标注

## 最低检查要求

### 代码与接口

- 至少覆盖受影响模块的直接测试或门禁
- 接口改动时检查请求响应结构、错误分支和鉴权前置
- 长任务相关改动时检查任务状态、重试或队列链路

### 内容与发布前置

- 内容对象改动时检查生命周期状态和内容门禁结果
- 发布前至少确认审核通过记录、内容包前置条件和回滚路径

### 非功能与稳定性

- 若改动影响关键链路，至少说明是否需要补跑性能、构建时间或可玩性基线
- 若未执行高成本 gate，必须记录原因和剩余风险

## 输出模板建议

### `acceptance-report.md`

建议最小结构：

```md
# Acceptance Report

## 本轮目标

## 覆盖的验收语句

## 通过项

## 失败项

## 阻塞项

## 交付结论
```

### `regression-report.md`

建议最小结构：

```md
# Regression Report

## 改动范围

## 选择的回归集

## 已执行检查

## 未执行检查与原因

## 剩余风险
```

### `gate-run-summary.md`

建议最小结构：

```md
# Gate Run Summary

## Gate 清单

| gate_id | 结果 | 证据 | 备注 |
|---|---|---|---|
| gate_xxx | pass/fail/blocked | 日志或命令 | 风险说明 |
```

### `failing-cases.md`

建议最小结构：

```md
# Failing Cases

## 失败用例列表

### <case_name>

- 失败信号
- 复现条件
- 影响范围
- 初步判断
- 是否需要修复计划
```

### `fix-plan.md`

若存在待修复问题，至少补充：

- 问题名称
- 受影响模块
- 修复方向
- 需要补跑的检查
- 回归确认点

## 硬约束

- 不编造“已通过”结论，所有结果必须有日志、门禁或测试证据
- 不跳过失败门禁后仍直接给出“可发布”结论
- 不把未执行的检查包装成“默认没问题”
- 不为追求通过率而删除高价值失败证据
- 若接口契约已变化但 `docs/30-api/openapi-draft.md` 未同步，必须明确标注为交付缺口或待补项

## 不该做的事

- 不替代 `loop-gate-optimizer` 去设计长期门禁策略
- 不直接发布内容包或服务
- 不脱离需求包额外扩写大范围测试体系

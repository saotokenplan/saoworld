# loop-gate-optimizer

## 目标

从 Agent 会话日志、CI 失败日志和线上事故中提炼门禁缺口、规则漂移和改进方向，输出 Gate Improvement Issue 或 Rule Improvement 输入。

## 适用场景

- 日常扫描 AI coding 闭环运行质量
- 某类问题反复出现
- 线上事故发生但现有 gate 没挡住
- 误报过高导致研发效率明显下降

## 规范来源

- 主要来源：
  - `docs/specs/agent-loop-spec.md`
- 次要来源：
  - `docs/specs/engineering-conventions.md`
  - `docs/dev-loop/gate_registry.yaml`
  - `docs/dev-loop/log-schemas-loop-engineering.md`
- 说明：
  - Agent 角色、门禁目标、Issue 反馈和闭环要求以 `agent-loop-spec.md` 为准
  - 工程协作和门禁落地方式参考 `engineering-conventions.md`
  - 现有 gate 清单参考 `gate_registry.yaml`
  - 日志输入结构参考 `log-schemas-loop-engineering.md`

## 输入

- `agent_session_log.jsonl`
- `ci_failures.jsonl`
- `prod_incidents.jsonl`
- 现有 gate 注册表
- 既有规则与阈值

## 输出

- `gate-improvement-report.md`
- `rule-improvement-report.md`
- 新 issue 草案
- 门禁退役建议

## 分析维度

### 缺失问题

- 某类错误只在执行中暴露，说明缺 gate

### 覆盖不足

- 问题被发现了，但发现得太晚，说明 gate 深度不够

### 误报过高

- gate 拦截多但有效问题少，说明信噪比低

### 规则老化

- 某类日志模式持续变化，旧规则开始漏报

## 输出要求

### Gate Improvement

至少包含：

- 症状
- 现有 gate 为何没挡住
- 建议 gate
- 成本与风险
- 验收指标

### Rule Improvement

至少包含：

- 规则名称
- 误报或漏报证据
- 建议阈值或样本更新
- 预期效果

## 硬约束

- 不直接修改生产 gate，先给出改进建议
- 不凭主观经验编造缺口，必须引用日志和失败模式
- 不只关注拦截数量，必须同时关注 gate 成本和价值

## 不该做的事

- 不直接发布代码
- 不把单次偶发问题包装成长期 gate

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
  - `docs/20-specs/agent-loop-spec.md`
- 次要来源：
  - `docs/20-specs/engineering-conventions.md`
  - `docs/40-dev-loop/gate_registry.yaml`
  - `docs/40-dev-loop/log-schemas-loop-engineering.md`
- 说明：
  - Agent 角色、门禁目标、Issue 反馈和闭环要求以 `agent-loop-spec.md` 为准
  - 工程协作和门禁落地方式参考 `engineering-conventions.md`
  - 现有 gate 清单参考 `docs/40-dev-loop/gate_registry.yaml`
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

## 提交规范

所有代码和文档提交必须遵守 `docs/20-specs/engineering-conventions.md#git-提交规范` 和 `docs/20-specs/agent-loop-spec.md#ai-提交前自检清单强制执行`。

### 提交格式

`<type>(<scope>): <summary>`

- type: docs / feat / fix / refactor / test / chore
- summary: 使用祈使句（新增/补充/调整/修复/重构），具体描述改动，不超过100字符，不以句号结尾

### 提交前必须

1. 执行 `python tools/validate-commit-msg.py --message "type(scope): 摘要"` 预验证提交信息格式
2. 确认一次提交只包含一个主题，多个改动拆分多次提交
3. 确认无调试残留（pdb/breakpoint/debug print）、无冲突标记、无无关文件
4. 提交后立即 `git push`（远程不可用时明确记录阻塞原因）

### 禁止的提交信息

- "update"、"fix bug"、"wip"、"一些修改"、"临时提交" 等模糊表述
- 照抄整段会话总结而非描述实际改动
- 一个提交混入多个不相关主题

### 推荐 scope

- gates
- dev-loop
- rules

# Loop Engineering Issue 模板

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

这份文件提供两类 Issue 模板：

1. `Gate Improvement Issue`：二层 Loop 的输出（提升门禁质量）
2. `Rule Improvement Issue`：三层 Loop 的输出（提升偏差发现规则质量）

你可以把它们复制到 GitHub/GitLab 的 Issue 模板里使用，或由 Agent 直接按模板创建 Issue。

---

## Gate Improvement Issue（门禁改进）

**Title（建议）**：`[Gate] <新增/修复/降噪/退役> - <gate_name> - <symptom>`  
例：`[Gate] 新增 - Typecheck - Agent 多次在执行中才发现类型错误`

### 1. Symptom（现象）

- 发生时间段：
- 影响范围（PR/分支/模块）：
- 失败信号：
- 日志证据（粘贴关键片段即可）：

```text
<ci_failures / agent_session_log / prod_incidents 的关键片段>
```

### 2. Root Cause Hypothesis（原因假设）

- 为什么现有 gate 没挡住：
- 这属于哪类缺口：
  - 缺 gate
  - gate 未接入必跑
  - gate 覆盖不足（路径/环境/数据）
  - gate 信噪比低（误报/抖动）

### 3. Proposed Gate（改进方案）

| 项目 | 内容 |
|------|------|
| gate 类型 | static / unit / integration / e2e / nonfunctional / content |
| gate 名称 |  |
| 触发策略 | on_pr / nightly / manual |
| 命令/脚本 |  |
| 覆盖风险标签 | 例如：type-safety / world-consistency / reward-boundary |
| 预期耗时（秒） |  |
| 可接受抖动率 | 例如：0.5% |

### 4. Acceptance（验收标准）

- 新 gate 生效后，以下模式不应再以“执行中才发现”的方式出现：
  - <模式 A>
  - <模式 B>
- 误报控制：
  - 30 天误报次数 ≤ <阈值>
- CI 预算：
  - PR 总耗时增加 ≤ <阈值>

### 5. Risk（风险与副作用）

- 可能误伤：
- 可能增加耗时：
- 可能增加抖动：

### 6. Rollout Plan（上线策略）

- 先在 nightly 跑 3 天观察 → 再切 on_pr 必跑（如适用）
- 若误报/抖动超过阈值，自动降级为 warn 或退回 nightly

---

## Rule Improvement Issue（偏差发现规则改进）

**Title（建议）**：`[Rule] <新增/修复/调阈值> - <rule_name> - <metric_change>`  
例：`[Rule] 调阈值 - MissingGateDetector - 误报率从 35% 降到 < 15%`

### 1. Context（上下文）

- 规则名称 / 版本：
- 触发来源（定时任务/手动扫描/事件触发）：
- 相关 Issue：
  - 采纳的：<链接>
  - 拒绝的：<链接>

### 2. Observed Drift（规则老化表现）

- 误报特征（False Positive）：
- 漏报特征（False Negative）：
- 受影响的门禁域：
  - static / e2e / content / nonfunctional

### 3. Proposed Change（改动提案）

| 项目 | 内容 |
|------|------|
| 改动类型 | 新增规则 / 调整规则 / 调整阈值 / 新增样本 |
| 规则文件 | `patterns/<name>.yaml` |
| 阈值文件 | `thresholds.yaml` |
| 样本集 | `golden_cases/` |

### 4. Acceptance（验收标准）

- Issue 采纳率提升：
  - 近 30 天采纳率 ≥ <阈值>
- 无效 Issue 降低：
  - 近 30 天无效率 ≤ <阈值>
- 延迟降低：
  - 偏差出现到提出 issue 的平均时间 ≤ <阈值>

### 5. Validation Data（验证数据）

附上 3–10 条典型正例/反例，确保改动可复现：

```json
{"case":"positive","...":"..."}
{"case":"negative","...":"..."}
```

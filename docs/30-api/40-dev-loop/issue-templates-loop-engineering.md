# Loop Engineering Issue 模板

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 适用范围

- 适用于 Loop Engineering 中 `Gate Improvement Issue` 与 `Rule Improvement Issue` 的模板化创建和治理。
- 适用于人工或 Agent 在二层、三层 Loop 中提交标准化改进 issue。
- 不替代 Loop 方案本身、日志 schema 或正式执行规范，而是作为问题输入载体。

## 当前定位

- 本文档是研发闭环层的 issue 模板文档，用于回答“门禁改进和规则改进 issue 应该如何标准化表达”。
- 本文档聚焦字段结构、模板内容和验收信息组织，不单独定义哪些 gate 必须存在或哪些规则应如何实现。
- 当 issue 模板与正式 loop 规则冲突时，应优先以 `docs/20-specs/agent-loop-spec.md` 和 `loop-engineering-plan.md` 为准。

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

## 与其他文档的关系

- `docs/40-dev-loop/loop-engineering-plan.md`
  - 定义二层、三层 Loop 的整体机制，本文档为其输出提供标准 issue 模板。
- `docs/40-dev-loop/log-schemas-loop-engineering.md`
  - 提供 issue 中 `evidence`、`failure_signature` 和验证数据所依赖的日志结构来源。
- `docs/20-specs/agent-loop-spec.md`
  - 定义 Gate Improvement Issue 与 Rule Improvement Issue 在正式闭环中的位置和用途。
- `docs/20-specs/engineering-conventions.md`
  - 提供 issue 驱动改动进入提交、测试和发布流程时需要遵循的工程约束。
- `docs/00-governance/document-change-process.md`
  - 约束后续如果模板字段或路径变化时，应如何同步更新本文档和相关引用。

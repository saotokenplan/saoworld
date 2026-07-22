# Loop Engineering 日志采集 Schema（JSONL）

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 适用范围

- 适用于 Loop Engineering 中 `agent_session_log.jsonl`、`ci_failures.jsonl`、`prod_incidents.jsonl` 等结构化日志采集。
- 适用于二层、三层 Loop 的偏差发现、聚类归因和 issue 自动生成输入。
- 不替代 Loop 方案本身和 issue 模板，而是提供底层结构化数据口径。

## 当前定位

- 本文档是研发闭环层的日志 schema 文档，用于回答“哪些日志需要采集、字段如何组织、如何支持自动消费”。
- 本文档聚焦 JSONL 字段、示例和签名规则，不单独定义门禁策略或 issue 模板内容。
- 当日志 schema 与正式 loop 规则冲突时，应优先以 `docs/20-specs/agent-loop-spec.md` 和 `loop-engineering-plan.md` 为准。

目标：把“AI 执行过程”压缩成可被二层/三层 Loop 自动消费的结构化信号。建议所有日志都采用 **JSON Lines**（一行一个 JSON）。

---

## 1) `agent_session_log.jsonl`

### 字段（建议）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `ts` | string | 是 | ISO 时间，例如 `2026-06-24T10:12:33+08:00` |
| `session_id` | string | 是 | Agent 会话唯一 id |
| `agent_name` | string | 是 | 例如 `Gameplay Agent` |
| `repo` | string | 否 | 仓库名/项目名 |
| `task_id` | string | 是 | 对应任务卡或 issue id |
| `stage` | string | 是 | `plan` / `implement` / `test` / `fix` / `release` |
| `event` | string | 是 | `start` / `end` / `tool_call` / `ci_result` / `error` |
| `summary` | string | 否 | 一句话摘要（便于人快速扫） |
| `artifacts` | object | 否 | 产物列表（文件、PR、commit） |
| `signals` | object | 否 | 结构化信号（例如测试结果、覆盖率、耗时） |
| `error` | object | 否 | 错误信息（仅当 event=error） |

### 示例

```json
{"ts":"2026-06-24T10:12:33+08:00","session_id":"S-20260624-001","agent_name":"Backend Agent","task_id":"TASK-142","stage":"implement","event":"start","summary":"开始实现投票结算接口"}
{"ts":"2026-06-24T10:20:01+08:00","session_id":"S-20260624-001","agent_name":"Backend Agent","task_id":"TASK-142","stage":"test","event":"ci_result","signals":{"gate_id":"G-STATIC-002","status":"failed","duration_s":92,"failure_signature":"TS2322 type mismatch"}}
{"ts":"2026-06-24T10:24:11+08:00","session_id":"S-20260624-001","agent_name":"Backend Agent","task_id":"TASK-142","stage":"fix","event":"end","summary":"修复类型错误并补齐类型测试","artifacts":{"commit":"abc123","changed_files":["services/vote/handler.ts"]}}
```

---

## 2) `ci_failures.jsonl`

### 字段（建议）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `ts` | string | 是 | ISO 时间 |
| `pipeline_id` | string | 是 | CI 流水线 id |
| `run_type` | string | 是 | `on_pr` / `nightly` / `manual` |
| `branch` | string | 否 | 分支名 |
| `pr_id` | string | 否 | PR id |
| `commit` | string | 否 | commit sha |
| `gate_id` | string | 是 | 与当前 gate 清单或 registry 约定对齐 |
| `gate_name` | string | 是 | 可读名称 |
| `status` | string | 是 | `failed` / `flaky` / `timeout` |
| `duration_s` | number | 是 | 执行耗时 |
| `failure_signature` | string | 是 | 可用于聚类的“签名” |
| `log_excerpt` | string | 否 | 关键日志片段（控制长度） |
| `suspected_category` | string | 否 | 初步归类：`missing_gate` / `coverage_gap` / `gate_noise` |
| `related_task_id` | string | 否 | 关联任务 |

### 示例

```json
{"ts":"2026-06-24T10:20:01+08:00","pipeline_id":"CI-8891","run_type":"on_pr","branch":"feature/vote","pr_id":"PR-77","commit":"abc123","gate_id":"G-STATIC-002","gate_name":"Typecheck","status":"failed","duration_s":92,"failure_signature":"TS2322 type mismatch","log_excerpt":"src/vote.ts:32 TS2322 ...","related_task_id":"TASK-142"}
```

---

## 3) `prod_incidents.jsonl`

### 字段（建议）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `ts` | string | 是 | ISO 时间 |
| `env` | string | 是 | `prod` / `staging` / `gray` |
| `version` | string | 是 | 发布版本号 |
| `incident_id` | string | 是 | 事件 id |
| `severity` | string | 是 | `sev1`/`sev2`/`sev3` |
| `symptom` | string | 是 | 面向人的简述 |
| `signal` | object | 否 | 指标/告警触发信息 |
| `suspected_gate_gap` | object | 否 | 初步判断缺失的 gate（如果能判断） |
| `rollback` | object | 否 | 回滚信息（是否回滚、回滚到哪版） |
| `links` | object | 否 | 监控/日志/工单链接 |

### 示例

```json
{"ts":"2026-06-24T22:10:45+08:00","env":"gray","version":"v0.3.2","incident_id":"INC-301","severity":"sev2","symptom":"新区域任务链无法完成，完成率从 61% 降到 12%","signal":{"metric":"quest_complete_rate","from":0.61,"to":0.12},"suspected_gate_gap":{"type":"e2e","reason":"关键路径自动试玩未覆盖该任务链"},"rollback":{"performed":true,"to_version":"v0.3.1"}}
```

---

## 4) 二层 Loop 的输出：`gate_improvement_issues.jsonl`（可选）

如果你希望“扫描任务”直接输出结构化 issue，而不是立刻创建平台 issue，可以先落地在本地文件：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `ts` | string | 是 | ISO 时间 |
| `issue_type` | string | 是 | `gate_improvement` |
| `priority` | string | 是 | `p0`/`p1`/`p2` |
| `symptom` | string | 是 | 现象 |
| `evidence` | array | 是 | 引用的日志条目（session/pipeline/incident） |
| `proposed_gate` | object | 是 | 对齐 gate_registry 字段子集 |
| `acceptance` | array | 是 | 验收条件 |

---

## 5) 聚类与签名规则建议

为了让二层/三层 Loop “不靠大模型也能跑”，建议对 `failure_signature` 使用简单稳定的规则：

1. 静态错误：编译器/解释器错误码（如 `TS2322`、`E11000`）
2. 测试失败：`TestSuite::TestName` + 断言类型
3. 运行时崩溃：异常类型 + top 3 stack frames
4. 内容审核：规则 id（如 `WORLD_RULE_017`、`REWARD_BUDGET_003`）

这样可以快速聚类，且不容易被日志微小变化干扰。

## 与其他文档的关系

- `docs/40-dev-loop/loop-engineering-plan.md`
  - 定义这些日志如何进入二层、三层 Loop 的归因和改进流程。
- `docs/40-dev-loop/issue-templates-loop-engineering.md`
  - 使用本文档中的日志字段和证据作为标准 issue 模板的输入。
- `docs/20-specs/agent-loop-spec.md`
  - 规定正式闭环中应采集哪些日志和如何把它们转成问题反馈与规则改进。
- `docs/20-specs/engineering-conventions.md`
  - 约束日志、审计和发布相关工程资产如何纳入仓库和交付流程。
- `docs/00-governance/document-template-spec.md`
  - 提供本文档当前补齐所遵循的标准章节结构模板。

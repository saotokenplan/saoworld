# 状态枚举定义

> 版本：v1.0.0
> 创建时间：2026-07-04

## 通用约定

### 存储方式
- 使用 VARCHAR(32) 存储状态值
- 通过 CHECK 约束限制合法值
- 不使用 PostgreSQL native enum 类型（避免迁移锁表风险）

### 命名规范
- 使用小写英文单词
- 多个单词用下划线分隔（snake_case）

---

## 投票周期状态（vote_cycles.status）

| 状态值 | 说明 | 允许操作 |
|--------|------|----------|
| draft | 草稿状态，正在配置投票周期 | 编辑、计划（scheduled） |
| scheduled | 已计划，等待开放时间 | 取消、开放（open） |
| open | 开放投票，玩家可提交投票 | 关闭（closed） |
| closed | 已关闭，正在计票 | 重新开放、结算（finalized） |
| finalized | 已结算，结果已确认 | 查看结果 |

### 状态迁移路径

```
draft → scheduled → open → closed → finalized
                             ↑
                             └── 管理员可重新开放（需审计）
```

### CHECK 约束

```sql
CHECK (status IN ('draft', 'scheduled', 'open', 'closed', 'finalized'))
```

---

## 投票候选项状态（vote_candidates.status）

| 状态值 | 说明 |
|--------|------|
| active | 有效候选项，玩家可投票 |
| withdrawn | 已撤回，玩家不可投票 |
| selected | 已当选，获胜候选项 |

### CHECK 约束

```sql
CHECK (status IN ('active', 'withdrawn', 'selected'))
```

---

## 区域状态（regions.status）

| 状态值 | 说明 |
|--------|------|
| locked | 未解锁，玩家不可访问 |
| active | 活跃，玩家可正常访问 |
| unstable | 不稳定，区域处于变化中 |
| archived | 归档，历史区域 |

### CHECK 约束

```sql
CHECK (status IN ('locked', 'active', 'unstable', 'archived'))
```

---

## 任务状态（player_quests.status）

| 状态值 | 说明 |
|--------|------|
| available | 可接取，玩家尚未接取 |
| active | 进行中，玩家正在完成 |
| completed | 已完成 |
| failed | 失败 |

### CHECK 约束

```sql
CHECK (status IN ('available', 'active', 'completed', 'failed'))
```

---

## 审核结果（review_records.result）

| 状态值 | 说明 |
|--------|------|
| approved | 自动通过 |
| rejected | 拒绝 |
| manual_review | 人工复核 |

### CHECK 约束

```sql
CHECK (result IN ('approved', 'rejected', 'manual_review'))
```

---

## 风险等级（review_records.risk_level）

| 状态值 | 说明 |
|--------|------|
| low | 低风险 |
| medium | 中风险 |
| high | 高风险 |
| critical | 严重风险 |

### CHECK 约束

```sql
CHECK (risk_level IN ('low', 'medium', 'high', 'critical'))
```

---

## 发布模式（release_records.release_mode）

| 状态值 | 说明 |
|--------|------|
| gray | 灰度发布 |
| full | 全量发布 |

### CHECK 约束

```sql
CHECK (release_mode IN ('gray', 'full'))
```

---

## 发布状态（release_records.status / rollback_records.status）

| 状态值 | 说明 |
|--------|------|
| queued | 排队中 |
| running | 执行中 |
| completed | 已完成 |
| failed | 失败 |

### CHECK 约束

```sql
CHECK (status IN ('queued', 'running', 'completed', 'failed'))
```

---

## 生成任务状态（generation_requests.status）

| 状态值 | 说明 |
|--------|------|
| pending | 等待处理 |
| processing | 处理中 |
| succeeded | 成功 |
| failed_retryable | 失败（可重试） |
| failed_permanent | 失败（不可重试） |

### CHECK 约束

```sql
CHECK (status IN ('pending', 'processing', 'succeeded', 'failed_retryable', 'failed_permanent'))
```

---

## 生成对象状态（generated_objects.status）

| 状态值 | 说明 |
|--------|------|
| pending_review | 等待审核 |
| approved | 已批准 |
| rejected | 已拒绝 |
| needs_revision | 需要修订 |

### CHECK 约束

```sql
CHECK (status IN ('pending_review', 'approved', 'rejected', 'needs_revision'))
```

---

## 内容包状态（content_packages.status）

| 状态值 | 说明 |
|--------|------|
| packaged | 已打包，等待发布 |
| gray | 灰度发布中 |
| live | 全量上线 |
| archived | 归档，历史版本 |
| rolled_back | 已回滚，终态 |

### 状态迁移路径

```
packaged → gray → live → archived
                 ↑  ↓
                 rolled_back
```

### CHECK 约束

```sql
CHECK (status IN ('packaged', 'gray', 'live', 'archived', 'rolled_back'))
```

---

## 操作者角色（audit_logs.operator_role）

| 角色值 | 说明 |
|--------|------|
| player | 普通玩家 |
| ops | 运营人员 |
| reviewer | 审核人员 |
| system | 系统/自动化任务 |

### CHECK 约束

```sql
CHECK (operator_role IN ('player', 'ops', 'reviewer', 'system'))
```

---

## 操作类型（audit_logs.action）

| action 值 | 说明 |
|-----------|------|
| vote_submit | 玩家提交投票 |
| vote_cycle_create | 创建投票周期 |
| vote_cycle_scheduled | 计划投票周期 |
| vote_cycle_opened | 开放投票 |
| vote_cycle_closed | 关闭投票 |
| vote_cycle_finalized | 结算投票 |
| content_release | 发布内容包 |
| content_rollback | 回滚内容包 |
| review_approve | 审核批准 |

---

## 资源类型（audit_logs.resource_type）

| resource_type 值 | 说明 |
|------------------|------|
| vote | 投票记录 |
| vote_cycle | 投票周期 |
| vote_candidate | 投票候选项 |
| content_package | 内容包 |
| generated_object | 生成对象 |
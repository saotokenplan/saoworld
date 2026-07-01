# 42 - 发布与回滚规范

> 适用角色：DevOps、运营、后端开发
> 本文件定义发布前检查、灰度发布策略、回滚流程。

---

## 微服务列表

后端规划 8 个核心服务：

| 服务 | 职责 |
|------|------|
| `gateway-service` | 客户端统一入口、鉴权、限流、会话上下文 |
| `player-service` | 账号、角色、成长、声望、章节进度 |
| `world-service` | 区域状态、阵营状态、地图与任务可见性 |
| `vote-service` | 候选池、投票资格、投票记录、结算 |
| `generation-service` | AI生成请求组织、模板加载、结果落库 |
| `review-service` | 结构化校验、风险判断、人工复核流转 |
| `content-service` | 内容包、灰度投放、版本归档、回滚 |
| `ops-service` | 后台运营入口、指标汇总、Issue 触发 |

---

## 发布前检查清单

**代码发布前必须满足：**

- [ ] 代码流水线全绿（ruff lint、mypy 类型检查、pytest 全部通过）
- [ ] 内容流水线全绿（一致性、数值、安全、重复度四项检查通过）
- [ ] 发布说明（Release Notes）生成完成
- [ ] 回滚路径验证通过
- [ ] 上一个稳定版本已保留并可快速切换
- [ ] 数据库迁移脚本已评审并在预发布环境验证
- [ ] 配置项变更已同步到所有环境
- [ ] 相关监控和告警已配置

---

## 发布策略

### 灰度优先原则

**所有发布必须优先灰度，禁止直接全量发布。**

灰度发布流程：
1. 打包内容/服务版本，标记为 `packaged` 状态
2. 发布到灰度环境/灰度用户组（状态 `gray`）
3. 观测关键指标**至少一个完整窗口期**（建议24小时或一个投票周期）
4. 灰度期间无异常 → 扩大到全量（状态 `live`）
5. 灰度期间发现异常 → 立即暂停扩大范围，评估回滚或修复

### 灰度范围配置

灰度范围通过 `gray_scope_jsonb` 字段配置：
```json
{
  "region_ids": ["region_wasteland_01"],
  "player_percent": 10,
  "player_ids": ["player_xxx"]
}
```
支持按区域、按玩家百分比、按指定玩家列表进行灰度。

### 发布后要求

发布完成后必须记录以下信息：
- 版本号/内容包号
- 操作人
- 发布时间
- 发布结果（成功/失败）
- 关键指标快照
- 简短复盘摘要

---

## 回滚规范

### 回滚原则

- 回滚是一等公民，必须在发布前验证回滚路径
- 回滚最小单位：`content_package_id`（内容包级别）
- 已上线内容必须保留上一个稳定版本，可随时回滚

### 回滚触发条件

出现以下情况时必须立即评估回滚：
- 关键错误率突增（5xx > 1%）
- 投票/核心玩法不可用
- 内容出现严重世界观冲突或安全问题
- 数值异常导致经济系统失衡
- 关键指标在灰度期间异常

### 回滚流程

1. 暂停发布/灰度扩大
2. 评估影响范围（受影响玩家、区域、数据）
3. 执行回滚操作（状态迁移到 `rolled_back`）
4. 记录回滚信息：
   - 回滚原因
   - 影响范围
   - 对应 `trace_id` 和日志链接
   - 操作人
   - 回滚时间
5. 通知相关人员
6. 产出回滚复盘

### 回滚限制

- `rolled_back` 是**终态**，回滚后的内容包不可再向 `live`/`gray` 迁移
- 同类内容连续回滚超过 **2 次**时，**暂停对应模板使用**，必须经过评审修复后才能重新启用
- 服务回滚后必须确认数据库迁移是否兼容，必要时做数据回滚

---

## 异步任务推荐清单

以下长任务必须通过 Celery 异步执行，禁止在 Web 进程同步处理：

| 任务名 | 说明 |
|--------|------|
| `generate_content_batch` | AI批量内容生成 |
| `run_world_consistency_review` | 世界一致性审核 |
| `run_balance_review` | 数值平衡审核 |
| `package_content_batch` | 内容打包 |
| `release_content_package` | 内容发布 |
| `rollback_content_package` | 内容回滚 |
| `daily_gate_scan` | 每日门禁扫描 |

异步任务要求：
- 每个任务必须有 `task_id`
- 支持重试与幂等
- 必须写入状态迁移日志
- 必须区分"可重试失败"和"不可重试失败"

---

## 事件流推荐

内部事件总线建议至少包含以下主题：

| 事件 | 触发时机 |
|------|----------|
| `vote.cycle.closed` | 投票周期关闭 |
| `vote.result.finalized` | 投票结果结算完成 |
| `generation.request.created` | 生成请求创建 |
| `generation.batch.completed` | 批量生成完成 |
| `review.batch.completed` | 批量审核完成 |
| `content.package.released` | 内容包发布 |
| `content.package.rolled_back` | 内容包回滚 |

事件消息必须包含：`event_id`、`event_type`、`occurred_at`、`trace_id`、`producer`、`payload`。

---

## 相关规则

- Git 工作流 → [40-git-workflow.md](./40-git-workflow.md)
- 数据库状态机 → [11-database.md](./11-database.md)
- 安全规范 → [50-security.md](./50-security.md)

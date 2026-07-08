# Runbook: 内容包回滚

> operation_id: OP-RELEASE-003
> operation_name: Content Package Rollback
> operation_type: rollback
> owner: Ops Agent

## 1. 操作概述

内容包回滚是将已发布的内容包（gray 或 live 状态）撤回到 rolled_back 终态，使玩家不再看到该内容包的操作。本 Runbook 描述内容包回滚的完整操作流程、触发条件和事后复盘要求。

**操作基本信息**：
- **操作名称**：内容包回滚
- **操作 ID**：OP-RELEASE-003
- **操作类型**：rollback（回滚）
- **负责人**：Ops Agent

**适用场景**：
- 灰度发布期间发现严重问题
- 全量发布后发现严重问题
- 内容安全问题紧急下架
- 数值平衡严重失衡

**回滚触发条件**（满足任一即可触发）：

| 级别 | 触发条件 | 响应时间 |
|------|---------|---------|
| P0 | 核心玩法完全不可用 / 严重数据丢失 | 立即回滚 |
| P1 | 5xx 错误率 > 1% 持续 5 分钟 / 严重内容安全问题 | 15 分钟内回滚 |
| P2 | 体验严重下降 / 部分功能异常 | 评估后决定是否回滚 |
| P3 | 轻微问题 / 文案错误 | 不回滚，下版本修复 |

**预期耗时**：5 分钟（操作本身）+ 30 分钟（验证）

**风险等级**：high（回滚本身也有风险，需谨慎操作）

---

## 2. 操作步骤

### 2.1 回滚前评估

**步骤 1：确认问题严重性**

- [ ] 收集错误日志和监控数据
- [ ] 评估影响范围（玩家数量、区域、功能模块）
- [ ] 判断是否符合回滚触发条件
- [ ] 确认是否有更轻量的修复方案
- [ ] 如符合 P0/P1 条件，立即启动回滚

**步骤 2：确认内容包当前状态**

```bash
# 查看内容包详情
curl -X GET "http://ops-service:8007/api/v1/ops/content-packages/{package_id}" \
  -H "Authorization: Bearer $TOKEN"
```

**检查项**：
- [ ] 内容包状态为 `gray` 或 `live`
- [ ] 确认内容包 ID 正确
- [ ] 确认上一个稳定版本存在且状态正常

**步骤 3：确认回滚影响**

| 状态 | 影响范围 | 恢复方式 |
|------|---------|---------|
| `gray` | 仅灰度用户 | 灰度用户不再可见 |
| `live` | 所有玩家 | 所有玩家不再可见 |

---

### 2.2 执行回滚

**步骤 4：执行回滚操作**

```bash
# 执行回滚
curl -X POST "http://ops-service:8007/api/v1/ops/content-packages/{package_id}/rollback" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Trace-Id: $TRACE_ID" \
  -H "Idempotency-Key: $ROLLBACK_IDEMPOTENCY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "发现严重数值平衡问题",
    "rollback_reason": "balance_issue",
    "affected_scope": "all_players",
    "incident_reference": "INCIDENT-2026-001"
  }'
```

**回滚原因枚举**：
- `critical_bug`：严重 Bug
- `balance_issue`：数值平衡问题
- `content_safety`：内容安全问题
- `lore_conflict`：世界观冲突
- `performance`：性能问题
- `other`：其他原因

**步骤 5：验证回滚结果**

```bash
# 验证内容包状态
curl -X GET "http://ops-service:8007/api/v1/ops/content-packages/{package_id}" \
  -H "Authorization: Bearer $TOKEN"

# 验证玩家端不可见
curl -X GET "http://content-service:8003/api/v1/content/updates" \
  -H "Authorization: Bearer $PLAYER_TOKEN" \
  -H "X-Player-Id: $PLAYER_ID"

# 查看回滚记录
curl -X GET "http://ops-service:8007/api/v1/ops/rollback-records/{record_id}" \
  -H "Authorization: Bearer $TOKEN"
```

**验证项**：
- [ ] 内容包状态变为 `rolled_back`
- [ ] 玩家不再看到该内容包
- [ ] 回滚记录已创建
- [ ] 审计日志已记录
- [ ] 错误率开始下降

> 重要：`rolled_back` 是终态，回滚后的内容包不可再向 `live`/`gray` 迁移。

---

### 2.3 回滚后处理

**步骤 6：保存现场**

回滚后立即保存以下信息：
- [ ] 错误日志快照
- [ ] 监控指标截图（错误率、延迟、业务指标）
- [ ] 受影响玩家数量估算
- [ ] 问题发生时间线

**步骤 7：通知相关人员**

回滚完成后通知：
- 产品负责人
- 后端开发团队
- 内容团队
- 客服团队（如影响玩家）

**步骤 8：生成回滚复盘报告**

回滚后 24 小时内完成复盘报告，包含：
- 事件时间线
- 根本原因分析
- 影响范围评估
- 改进措施
- 重新发布计划

---

## 3. 特殊情况处理

### 3.1 连续回滚

**规则**：同类内容连续回滚超过 2 次时，暂停对应模板使用。

**处理步骤**：
1. 标记对应模板为 "暂停使用"
2. 组织专项评审
3. 修复根本问题
4. 评审通过后重新启用模板

### 3.2 数据库迁移回滚

如果回滚涉及数据库迁移（不常见，内容包发布通常不涉及 schema 变更）：

```bash
# 回滚到上一个版本
cd services/<service> && alembic downgrade -1

# 回滚到指定版本
cd services/<service> && alembic downgrade <revision_id>
```

> 注意：数据库迁移回滚风险高，必须经过技术负责人审批。

### 3.3 多内容包联动回滚

如果问题涉及多个内容包，需要按依赖关系逆序回滚：
1. 先回滚最新发布的内容包
2. 再依次回滚更早的内容包
3. 最后验证整体状态

---

## 4. 常见问题与解决方案

### 4.1 回滚失败

**现象**：回滚接口返回错误。

**可能原因**：
1. 内容包状态不是 `gray` 或 `live`
2. 内容包已经是 `rolled_back` 状态
3. 存在进行中的发布操作

**解决方案**：
```bash
# 1. 检查当前状态
curl -X GET "http://ops-service:8007/api/v1/ops/content-packages/{package_id}" \
  -H "Authorization: Bearer $TOKEN"

# 2. 如果状态异常，检查是否有进行中的任务
# 查看 ops-service 日志
kubectl logs -l app=ops-service --tail=200
```

### 4.2 回滚后玩家仍看到旧内容

**现象**：回滚后部分玩家仍能看到已回滚的内容包。

**可能原因**：
1. 客户端缓存未过期
2. CDN 缓存未刷新
3. 内容包 ID 引用错误

**解决方案**：
```bash
# 1. 强制刷新 CDN 缓存
# 2. 客户端下次启动时会重新拉取内容列表
# 3. 如果问题严重，可推送强制更新通知
```

### 4.3 回滚后数据不一致

**现象**：玩家进度、任务状态等数据与回滚后的内容不匹配。

**处理步骤**：
1. 评估数据影响范围
2. 如果影响小，在下个版本修复
3. 如果影响大，考虑数据回滚或补偿脚本
4. 通知受影响玩家

---

## 5. 相关链接

- 发布与回滚规范：`.trae/rules/42-release-rollback.md`
- 灰度发布 Runbook：`gray-release.md`
- 全量发布 Runbook：`full-release.md`
- 回滚脚本：`tools/rollback.sh`
- 状态机规范：`.trae/rules/11-database.md`
- 事件列表：`docs/20-specs/async-tasks-and-events/`

# Runbook: 内容包全量发布

> operation_id: OP-RELEASE-002
> operation_name: Full Release
> operation_type: release
> owner: Ops Agent

## 1. 操作概述

全量发布是将灰度验证通过的内容包发布给所有玩家的操作。本 Runbook 描述内容包从灰度到全量的完整发布流程。

**操作基本信息**：
- **操作名称**：内容包全量发布
- **操作 ID**：OP-RELEASE-002
- **操作类型**：release（发布）
- **负责人**：Ops Agent

**适用场景**：
- 灰度发布观察期结束，确认无问题
- 内容包全量上线
- 紧急修复内容包全量发布（需特别审批）

**前置条件**：
- 内容包当前状态为 `gray`
- 灰度观察期至少 24 小时（或一个完整投票周期）
- 灰度期间无 P0/P1 级问题
- 关键指标正常（错误率 < 0.1%，延迟正常）
- 已准备好回滚方案
- 已获得发布授权

**预期耗时**：15 分钟

**风险等级**：high（全量发布影响所有玩家）

---

## 2. 操作步骤

### 2.1 发布前检查

**步骤 1：确认灰度观察结果**

| 检查项 | 标准 | 状态 |
|--------|------|------|
| 灰度时长 | ≥ 24 小时或 1 个完整投票周期 | [ ] |
| 5xx 错误率 | < 0.1% | [ ] |
| P95 延迟 | < 300ms | [ ] |
| 严重内容问题 | 0 | [ ] |
| 玩家投诉量 | 正常范围 | [ ] |
| 核心玩法可用性 | 100% | [ ] |

**步骤 2：检查内容包状态**

```bash
# 查看内容包详情
curl -X GET "http://ops-service:8007/api/v1/ops/content-packages/{package_id}" \
  -H "Authorization: Bearer $TOKEN"
```

**检查项**：
- [ ] 内容包状态为 `gray`
- [ ] 灰度发布记录完整
- [ ] 内容包 payload 无变更

**步骤 3：确认系统健康状态**

```bash
# 查看系统状态
curl -X GET "http://ops-service:8007/api/v1/ops/system/status" \
  -H "Authorization: Bearer $TOKEN"
```

**检查项**：
- [ ] 所有服务状态正常
- [ ] 数据库连接正常
- [ ] 缓存服务正常
- [ ] 无未处理的 P0/P1 告警

**步骤 4：准备回滚方案**

全量发布前必须确认：
- [ ] 上一个稳定版本的内容包状态为 `live`
- [ ] 回滚操作已验证可用
- [ ] 回滚责任人已确认

---

### 2.2 执行全量发布

**步骤 5：执行全量发布**

```bash
# 全量发布（从 gray 升级到 live）
curl -X POST "http://ops-service:8007/api/v1/ops/content-packages/{package_id}/release" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Trace-Id: $TRACE_ID" \
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "release_mode": "full",
    "reason": "灰度观察期通过，全量发布",
    "gray_observation_summary": "灰度24小时，错误率0.05%，无严重问题"
  }'
```

**预期结果**：
- 内容包状态从 `gray` 变为 `live`
- 旧版本内容包状态变为 `archived`
- 返回 release_record_id

**步骤 6：验证发布结果**

```bash
# 查看内容包状态
curl -X GET "http://ops-service:8007/api/v1/ops/content-packages/{package_id}" \
  -H "Authorization: Bearer $TOKEN"

# 验证所有玩家可见
curl -X GET "http://content-service:8003/api/v1/content/updates" \
  -H "Authorization: Bearer $PLAYER_TOKEN" \
  -H "X-Player-Id: $ANY_PLAYER_ID"
```

**验证项**：
- [ ] 内容包状态为 `live`
- [ ] 任意玩家都能看到新内容包
- [ ] 旧版本已归档（状态为 `archived`）
- [ ] 发布记录完整

---

### 2.3 发布后监控

**步骤 7：发布后 1 小时密集监控**

全量发布后的第一个小时是高风险期，需重点监控：

| 时间点 | 监控内容 |
|--------|---------|
| 发布后 5 分钟 | 错误率、延迟、服务可用性 |
| 发布后 15 分钟 | 业务指标（内容访问、投票量） |
| 发布后 30 分钟 | 错误日志、异常告警 |
| 发布后 60 分钟 | 全面指标回顾 |

**步骤 8：记录发布结果**

发布完成后记录以下信息：
- 发布时间
- 操作人
- 发布结果（成功/失败）
- 灰度观察期总结
- 发布后关键指标快照
- 简短复盘

---

## 3. 回滚方案

### 3.1 触发回滚的条件

全量发布后出现以下情况应立即回滚：
- 5xx 错误率 > 1% 且持续 5 分钟以上
- 核心玩法完全不可用
- 严重内容安全问题
- 数据一致性问题
- 大规模玩家投诉

### 3.2 回滚操作步骤

```bash
# 执行回滚
curl -X POST "http://ops-service:8007/api/v1/ops/content-packages/{package_id}/rollback" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Trace-Id: $TRACE_ID" \
  -H "Idempotency-Key: $ROLLBACK_IDEMPOTENCY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "全量发布后发现严重问题",
    "rollback_reason": "critical_bug",
    "affected_players": "all"
  }'
```

**回滚验证**：
- [ ] 内容包状态变为 `rolled_back`
- [ ] 所有玩家不再看到该内容包
- [ ] 上一个稳定版本恢复为 `live`
- [ ] 回滚记录已创建
- [ ] 通知已发送给相关人员

### 3.3 回滚后处理

回滚完成后必须：
1. 保存现场（日志、指标快照）
2. 分析根本原因
3. 生成回滚复盘报告
4. 修复问题后重新走灰度发布流程

> 注意：同类内容连续回滚超过 2 次时，暂停对应模板使用，必须经过评审修复后才能重新启用。

---

## 4. 常见问题与解决方案

### 4.1 全量发布失败

**现象**：全量发布接口返回错误。

**可能原因**：
1. 内容包状态不是 `gray`
2. 存在未完成的发布记录
3. 数据库事务冲突

**解决方案**：
```bash
# 1. 检查当前状态
curl -X GET "http://ops-service:8007/api/v1/ops/content-packages/{package_id}" \
  -H "Authorization: Bearer $TOKEN"

# 2. 查看发布记录
curl -X GET "http://ops-service:8007/api/v1/ops/release-records?package_id={package_id}" \
  -H "Authorization: Bearer $TOKEN"

# 3. 如果状态异常，联系后端开发排查
```

### 4.2 旧版本未正确归档

**现象**：全量发布后，旧版本内容包状态仍为 `live`。

**风险**：玩家可能看到重复或冲突的内容。

**解决方案**：
```bash
# 1. 手动归档旧版本
curl -X POST "http://ops-service:8007/api/v1/ops/content-packages/{old_package_id}/archive" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Trace-Id: $TRACE_ID" \
  -H "Content-Type: application/json" \
  -d '{"reason": "新版本全量发布，旧版本归档"}'

# 2. 验证归档结果
curl -X GET "http://ops-service:8007/api/v1/ops/content-packages/{old_package_id}" \
  -H "Authorization: Bearer $TOKEN"
```

### 4.3 发布后性能下降

**现象**：全量发布后系统延迟升高、错误率上升。

**处理步骤**：
1. 立即检查错误日志定位问题
2. 如果问题严重且无法快速定位，执行回滚
3. 如果问题较轻，先扩容再排查
4. 记录性能指标变化用于后续优化

---

## 5. 相关链接

- 灰度发布 Runbook：`gray-release.md`
- 回滚 Runbook：`rollback.md`
- 发布脚本：`tools/deploy.sh`
- 发布验证脚本：`tools/verify-release.sh`
- 状态机规范：`.trae/rules/11-database.md`
- 发布与回滚规范：`.trae/rules/42-release-rollback.md`

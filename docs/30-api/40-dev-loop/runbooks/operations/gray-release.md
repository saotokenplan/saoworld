# Runbook: 内容包灰度发布

> operation_id: OP-RELEASE-001
> operation_name: Gray Release
> operation_type: release
> owner: Ops Agent

## 1. 操作概述

灰度发布是将新内容包先发布给一小部分玩家（灰度用户组），观察一段时间确认无问题后再全量发布的发布策略。本 Runbook 描述内容包灰度发布的完整操作流程。

**操作基本信息**：
- **操作名称**：内容包灰度发布
- **操作 ID**：OP-RELEASE-001
- **操作类型**：release（发布）
- **负责人**：Ops Agent

**适用场景**：
- 首期内容包上线
- 新版本内容包发布
- 重大内容更新发布

**前置条件**：
- 内容包已通过所有门禁（lint、typecheck、单元测试、内容检查、E2E 测试）
- 内容包状态为 `packaged`
- 已确认灰度范围（玩家白名单 / 百分比 / 区域）
- 已准备好回滚方案
- 监控告警已配置并正常工作

**预期耗时**：30 分钟

**风险等级**：medium（灰度发布影响范围有限）

---

## 2. 操作步骤

### 2.1 发布前检查

**步骤 1：确认内容包状态**

```bash
# 通过 ops-service API 查看内容包状态
curl -X GET "http://ops-service:8007/api/v1/ops/content-packages/{package_id}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Trace-Id: $TRACE_ID"
```

**检查项**：
- [ ] 内容包状态为 `packaged`
- [ ] 内容包 schema_version 正确
- [ ] 内容包 payload 完整
- [ ] 关联的 region_id / chapter_id 正确

**步骤 2：验证系统健康状态**

```bash
# 查看系统状态
curl -X GET "http://ops-service:8007/api/v1/ops/system/status" \
  -H "Authorization: Bearer $TOKEN"
```

**检查项**：
- [ ] 所有 8 个后端服务状态为 `ok`
- [ ] PostgreSQL 连接正常
- [ ] Redis 连接正常
- [ ] 监控指标正常（无异常告警）

**步骤 3：确认灰度范围配置**

灰度范围支持三种配置方式（优先级从高到低）：
1. `player_ids`：指定玩家 ID 白名单
2. `player_percent`：按玩家百分比随机抽取
3. `region_ids`：按区域灰度

```json
{
  "region_ids": ["region_core_01"],
  "player_percent": 10,
  "player_ids": ["player_xxx", "player_yyy"]
}
```

---

### 2.2 执行灰度发布

**步骤 4：执行灰度发布**

```bash
# 通过 ops-service API 执行灰度发布
curl -X POST "http://ops-service:8007/api/v1/ops/content-packages/{package_id}/release" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Trace-Id: $TRACE_ID" \
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "release_mode": "gray",
    "gray_scope": {
      "region_ids": ["region_core_01"],
      "player_percent": 10
    },
    "reason": "首期内容包灰度发布"
  }'
```

**预期结果**：
- 内容包状态从 `packaged` 变为 `gray`
- 返回 release_record_id
- 发布记录已创建

**步骤 5：验证发布结果**

```bash
# 查看内容包状态
curl -X GET "http://ops-service:8007/api/v1/ops/content-packages/{package_id}" \
  -H "Authorization: Bearer $TOKEN"

# 查看发布记录
curl -X GET "http://ops-service:8007/api/v1/ops/release-records/{record_id}" \
  -H "Authorization: Bearer $TOKEN"
```

**验证项**：
- [ ] 内容包状态为 `gray`
- [ ] gray_scope_jsonb 配置正确
- [ ] 发布记录状态为 `completed`
- [ ] 审计日志已记录

---

### 2.3 发布后验证

**步骤 6：验证灰度可见性**

```bash
# 使用灰度范围内的玩家 ID 验证可见性
curl -X GET "http://content-service:8003/api/v1/content/updates" \
  -H "Authorization: Bearer $PLAYER_TOKEN" \
  -H "X-Player-Id: $GRAY_PLAYER_ID"

# 使用灰度范围外的玩家 ID 验证不可见
curl -X GET "http://content-service:8003/api/v1/content/updates" \
  -H "Authorization: Bearer $PLAYER_TOKEN" \
  -H "X-Player-Id: $NON_GRAY_PLAYER_ID"
```

**验证项**：
- [ ] 灰度范围内玩家可见新内容包
- [ ] 灰度范围外玩家不可见新内容包
- [ ] 内容包元数据正确

**步骤 7：监控关键指标**

灰度发布后至少观察 24 小时（或一个完整投票周期），重点监控：

| 指标类型 | 具体指标 | 告警阈值 |
|---------|---------|---------|
| 错误率 | 5xx 错误率 | > 1% |
| 延迟 | P95 响应时间 | > 500ms |
| 业务指标 | 内容包访问量 | 预期范围 |
| 业务指标 | 投票提交量 | 预期范围 |
| 内容安全 | 内容安全告警 | > 0 |

**步骤 8：记录发布结果**

在发布记录中补充：
- 发布时间
- 操作人
- 灰度范围
- 发布结果（成功/失败）
- 关键指标快照

---

## 3. 回滚方案

### 3.1 触发回滚的条件

出现以下情况时应立即回滚：
- 关键错误率突增（5xx > 1%）
- 核心玩法不可用（投票、任务、区域探索）
- 内容出现严重世界观冲突或安全问题
- 数值异常导致经济系统失衡
- 关键指标在灰度期间异常

### 3.2 回滚操作步骤

```bash
# 执行回滚
curl -X POST "http://ops-service:8007/api/v1/ops/content-packages/{package_id}/rollback" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Trace-Id: $TRACE_ID" \
  -H "Idempotency-Key: $ROLLBACK_IDEMPOTENCY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "灰度期间发现严重问题",
    "rollback_reason": "critical_bug"
  }'
```

**回滚验证**：
- [ ] 内容包状态变为 `rolled_back`
- [ ] 灰度玩家不再看到该内容包
- [ ] 回滚记录已创建
- [ ] 审计日志已记录

> 注意：`rolled_back` 是终态，回滚后的内容包不可再向 `live`/`gray` 迁移。

---

## 4. 常见问题与解决方案

### 4.1 发布失败

**现象**：发布接口返回错误，内容包状态未变更。

**可能原因**：
1. 内容包状态不正确（不是 `packaged`）
2. 灰度范围配置无效
3. 数据库连接异常
4. 幂等键冲突

**解决方案**：
```bash
# 1. 检查内容包当前状态
curl -X GET "http://ops-service:8007/api/v1/ops/content-packages/{package_id}" \
  -H "Authorization: Bearer $TOKEN"

# 2. 检查发布记录详情
curl -X GET "http://ops-service:8007/api/v1/ops/release-records?package_id={package_id}" \
  -H "Authorization: Bearer $TOKEN"

# 3. 查看服务错误日志
kubectl logs -l app=ops-service --tail=100
```

### 4.2 灰度范围不生效

**现象**：灰度范围外的玩家也能看到内容包。

**可能原因**：
1. 灰度范围配置错误
2. 内容包状态不是 `gray`
3. 缓存未刷新

**解决方案**：
```bash
# 1. 验证内容包状态和 gray_scope
curl -X GET "http://ops-service:8007/api/v1/ops/content-packages/{package_id}" \
  -H "Authorization: Bearer $TOKEN" | jq '.data.gray_scope_jsonb'

# 2. 检查灰度判断逻辑（content-service）
# 查看 content-service 日志确认灰度判断逻辑
```

### 4.3 监控告警风暴

**现象**：灰度发布后短时间内大量告警。

**处理步骤**：
1. 保持冷静，先确认是否为真实问题
2. 检查错误日志定位根本原因
3. 如确认是严重问题，立即执行回滚
4. 如为误报，调整告警阈值后继续观察

---

## 5. 相关链接

- 规范文档：`docs/20-specs/content-generation-spec.md`
- 发布脚本：`tools/gray-release.sh`
- 发布验证脚本：`tools/verify-release.sh`
- 状态机规范：`.trae/rules/11-database.md`
- 内容服务 API：`docs/30-api/content-api-examples.md`
- 运营服务 API：`docs/30-api/ops-api-examples.md`

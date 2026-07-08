# Runbook: 数据库迁移

> operation_id: OP-INFRA-002
> operation_name: Database Migration
> operation_type: infrastructure
> owner: Backend Agent

## 1. 操作概述

数据库迁移是使用 Alembic 对数据库 schema 进行版本化管理的操作。本 Runbook 描述数据库迁移的完整流程，包括前置检查、迁移执行、验证和回滚方案。

**操作基本信息**：
- **操作名称**：数据库迁移
- **操作 ID**：OP-INFRA-002
- **操作类型**：infrastructure（基础设施）
- **负责人**：Backend Agent

**适用场景**：
- 新增数据表
- 修改表结构（加字段、加索引）
- 数据迁移
- 约束变更

**前置条件**：
- 已备份数据库（强烈建议）
- 迁移脚本已在测试环境验证通过
- 已评估迁移对性能的影响
- 已确认回滚方案可用
- 已通知相关团队

**预期耗时**：
- 小迁移（加字段、加索引）：10 分钟
- 大迁移（数据迁移、表重构）：30 分钟 - 数小时

**风险等级**：high（数据库迁移不可逆风险高）

---

## 2. 操作步骤

### 2.1 迁移前准备

**步骤 1：备份数据库**

```bash
# 备份整个数据库
pg_dump -h <host> -U <user> -d <database> -F c -f backup_$(date +%Y%m%d_%H%M).dump

# 验证备份文件
pg_restore -l backup_$(date +%Y%m%d_%H%M).dump
```

**检查项**：
- [ ] 备份文件已生成
- [ ] 备份文件大小合理
- [ ] 备份文件可正常读取

**步骤 2：检查迁移脚本**

```bash
# 查看待执行的迁移
cd services/<service> && alembic heads

# 查看当前版本
cd services/<service> && alembic current

# 查看迁移历史
cd services/<service> && alembic history
```

**检查项**：
- [ ] 迁移脚本已在测试环境验证通过
- [ ] 迁移脚本包含 downgrade 方法
- [ ] 已评估迁移对性能的影响
- [ ] 大表迁移已确认执行时间窗口

**步骤 3：检查数据库状态**

```bash
# 检查数据库连接
psql -h <host> -U <user> -d <database> -c "SELECT 1;"

# 检查当前连接数
psql -h <host> -U <user> -d <database> -c "SELECT count(*) FROM pg_stat_activity;"

# 检查长事务
psql -h <host> -U <user> -d <database> -c "SELECT pid, now() - xact_start AS duration, query FROM pg_stat_activity WHERE state = 'active' AND now() - xact_start > interval '5 minutes';"
```

**检查项**：
- [ ] 数据库连接正常
- [ ] 无超长事务
- [ ] 连接数在正常范围内

**步骤 4：通知相关方**

迁移前通知：
- [ ] 产品团队（可能的服务中断）
- [ ] 后端团队（迁移期间避免发布）
- [ ] 客服团队（玩家可能受影响）

---

### 2.2 执行迁移

**步骤 5：执行迁移（小迁移）**

对于小迁移（加字段、加索引等）：

```bash
# 执行迁移
cd services/<service> && alembic upgrade head

# 验证迁移结果
cd services/<service> && alembic current
```

**步骤 5：执行迁移（大迁移 - 推荐低峰期）**

对于大数据量迁移（数据迁移、表重构）：

```bash
# 1. 先在只读事务中预检
cd services/<service> && alembic upgrade head --sql > migration.sql

# 2. 检查生成的 SQL
cat migration.sql | less

# 3. 执行迁移
cd services/<service> && alembic upgrade head

# 4. 监控迁移进度
# 在另一个终端查看数据库锁和活动
watch -n 5 "psql -h <host> -U <user> -d <database> -c 'SELECT pid, state, query FROM pg_stat_activity WHERE state = 'active';'"
```

**步骤 6：验证迁移结果**

```bash
# 检查当前 alembic 版本
cd services/<service> && alembic current

# 检查表是否存在
psql -h <host> -U <user> -d <database> -c "\dt"

# 检查字段是否存在
psql -h <host> -U <user> -d <database> -c "\d <table_name>"

# 检查索引是否存在
psql -h <host> -U <user> -d <database> -c "\di"
```

**验证项**：
- [ ] Alembic 版本已更新
- [ ] 表结构变更正确
- [ ] 数据迁移正确（如适用）
- [ ] 索引已创建
- [ ] 约束已生效

---

### 2.3 迁移后验证

**步骤 7：功能验证**

| 验证项 | 验证方法 |
|--------|---------|
| 服务启动正常 | 重启服务并检查健康检查 |
| 核心接口正常 | 调用关键 API 验证 |
| 数据完整性 | 抽查数据正确性 |
| 查询性能 | 检查慢查询日志 |

**步骤 8：监控关键指标**

迁移后 24 小时内监控：

| 指标 | 告警阈值 | 说明 |
|------|---------|------|
| 慢查询数 | 突增 100% | 性能影响 |
| 错误率 | > 1% | 功能异常 |
| 数据库连接数 | > 80% 上限 | 连接泄漏 |
| 磁盘使用率 | 突增 | 数据膨胀 |

**步骤 9：记录迁移结果**

迁移完成后记录：
- 迁移时间
- 操作人
- 服务名称
- 迁移版本
- 迁移内容简述
- 执行时长
- 迁移结果（成功/失败）
- 是否需要后续优化

---

## 3. 回滚方案

### 3.1 触发回滚的条件

迁移后出现以下情况应立即回滚：
- 迁移脚本执行失败
- 核心功能完全不可用
- 数据严重损坏
- 性能严重下降

### 3.2 回滚操作步骤

```bash
# 回滚到上一个版本
cd services/<service> && alembic downgrade -1

# 回滚到指定版本
cd services/<service> && alembic downgrade <revision_id>

# 验证回滚结果
cd services/<service> && alembic current
```

> 注意：部分迁移（如 DROP TABLE）无法通过 downgrade 恢复数据，必须从备份恢复。

### 3.3 从备份恢复（严重情况）

如果迁移导致数据丢失或严重损坏：

```bash
# 1. 停止应用服务
docker compose stop <service-name>

# 2. 从备份恢复
pg_restore -h <host> -U <user> -d <database> -c backup_<timestamp>.dump

# 3. 验证恢复结果
psql -h <host> -U <user> -d <database> -c "SELECT count(*) FROM <important_table>;"

# 4. 重启服务
docker compose up -d <service-name>
```

### 3.4 回滚后处理

1. 保存迁移失败日志
2. 分析失败原因
3. 修复迁移脚本
4. 在测试环境重新验证
5. 安排下次迁移时间

---

## 4. 常见问题与解决方案

### 4.1 迁移锁等待超时

**现象**：alembic 卡住或报锁等待超时。

**原因**：有其他事务持有表锁。

**解决方案**：
```bash
# 1. 查看持锁事务
psql -h <host> -U <user> -d <database> -c "SELECT pid, now() - xact_start AS duration, query FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC LIMIT 5;"

# 2. 如果是空闲事务，考虑终止
SELECT pg_terminate_backend(<pid>);
```

### 4.2 迁移执行失败

**现象**：alembic upgrade 报错。

**处理步骤**：
1. 查看错误信息
2. 判断迁移是否部分执行
3. 如果已部分执行，考虑手动修复后继续
4. 如果无法修复，执行回滚

### 4.3 大表加索引锁表

**现象**：加索引期间表被锁定，写入阻塞。

**解决方案**：
```sql
-- 使用 CONCURRENTLY 选项加索引（不锁表，但时间更长）
CREATE INDEX CONCURRENTLY idx_name ON table_name (column);
```

> 注意：CREATE INDEX CONCURRENTLY 不能在事务中使用，Alembic 中需要特殊处理。

### 4.4 迁移后性能下降

**现象**：迁移后查询变慢。

**可能原因**：
1. 索引未正确创建
2. 统计信息过期
3. 查询计划改变

**解决方案**：
```sql
-- 更新统计信息
ANALYZE <table_name>;

-- 检查索引使用情况
SELECT schemaname, tablename, indexname, idx_scan 
FROM pg_stat_user_indexes 
WHERE tablename = '<table_name>';
```

---

## 5. 相关链接

- 迁移脚本目录：`services/<service>/alembic/versions/`
- 迁移配置：`services/<service>/alembic.ini`
- 批量迁移脚本：`tools/migrate-all.sh`
- 数据库设计规范：`.trae/rules/11-database.md`
- 服务部署 Runbook：`service-deployment.md`

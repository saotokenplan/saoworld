# Runbook: 服务部署

> operation_id: OP-INFRA-001
> operation_name: Service Deployment
> operation_type: infrastructure
> owner: Ops Agent

## 1. 操作概述

服务部署是将后端服务或 Worker 的新版本部署到生产环境的操作。本 Runbook 描述服务部署的完整流程，包括前置检查、部署执行、健康验证和回滚方案。

**操作基本信息**：
- **操作名称**：服务部署
- **操作 ID**：OP-INFRA-001
- **操作类型**：infrastructure（基础设施）
- **负责人**：Ops Agent

**适用场景**：
- 后端服务版本升级
- Worker 版本升级
- 配置变更部署
- 紧急修复部署

**前置条件**：
- Docker 镜像已构建并推送到镜像仓库
- 配置文件已更新并验证
- 数据库迁移已执行（如需要）
- 已确认回滚方案可用
- 监控告警已配置

**预期耗时**：30 分钟

**风险等级**：high（服务部署影响所有玩家）

---

## 2. 操作步骤

### 2.1 部署前检查

**步骤 1：验证镜像可用性**

```bash
# 检查镜像是否存在
docker pull <registry>/<service-name>:<version>
docker images | grep <service-name>
```

**检查项**：
- [ ] 镜像标签正确
- [ ] 镜像大小在预期范围内
- [ ] 镜像摘要与构建记录一致

**步骤 2：检查当前服务状态**

```bash
# 查看服务状态
curl -X GET "http://ops-service:8007/api/v1/ops/system/status" \
  -H "Authorization: Bearer $TOKEN"

# 查看当前版本
curl -X GET "http://<service>:<port>/api/v1/health"
```

**检查项**：
- [ ] 所有服务当前状态正常
- [ ] 当前版本号已记录
- [ ] 数据库连接正常

**步骤 3：确认配置变更**

```bash
# 对比新旧配置差异
diff .env.prod .env.prod.new

# 验证配置格式
# 检查所有必需的环境变量是否存在
```

**检查项**：
- [ ] 配置变更内容已确认
- [ ] 敏感配置已通过安全渠道传递
- [ ] 配置格式正确

**步骤 4：准备回滚方案**

部署前必须确认：
- [ ] 上一个稳定版本的镜像可用
- [ ] 上一个版本的配置已备份
- [ ] 数据库迁移回滚方案已准备（如适用）
- [ ] 回滚操作步骤已验证

---

### 2.2 执行部署

**步骤 5：执行灰度部署（推荐）**

对于无状态服务，推荐使用滚动更新或蓝绿部署：

```bash
# Docker Compose 滚动更新
docker compose up -d --no-deps <service-name>

# 或使用 Kubernetes
kubectl rollout update deployment/<service-name> --image=<registry>/<service-name>:<version>
```

**滚动更新策略**：
1. 先启动新实例
2. 健康检查通过后，逐步切换流量
3. 停止旧实例
4. 监控新实例状态

**步骤 6：验证部署结果**

```bash
# 检查服务健康状态
curl -X GET "http://<service>:<port>/api/v1/health"

# 检查版本号
curl -X GET "http://<service>:<port>/api/v1/health" | jq '.data.version'

# 检查容器状态
docker ps | grep <service-name>
```

**验证项**：
- [ ] 服务健康检查通过
- [ ] 版本号正确
- [ ] 日志无异常错误
- [ ] 指标正常（错误率、延迟）

**步骤 7：全量部署（如使用灰度）**

如果灰度验证通过：
```bash
# 将所有实例更新到新版本
# Docker Compose: docker compose up -d
# Kubernetes: kubectl scale deployment/<service-name> --replicas=<original>
```

---

### 2.3 部署后验证

**步骤 8：功能验证**

| 验证项 | 验证方法 | 预期结果 |
|--------|---------|---------|
| 健康检查 | 调用 `/api/v1/health` | 返回 200 |
| 核心接口 | 调用关键 API | 返回正确 |
| 数据库连接 | 检查日志 | 无连接错误 |
| 缓存连接 | 检查日志 | 无连接错误 |
| 事件发布 | 触发事件 | 正常发布 |

**步骤 9：监控关键指标**

部署后 1 小时内重点监控：

| 指标 | 告警阈值 | 说明 |
|------|---------|------|
| 5xx 错误率 | > 1% | 服务错误率 |
| P95 延迟 | > 500ms | 响应延迟 |
| CPU 使用率 | > 80% | 资源使用 |
| 内存使用率 | > 85% | 资源使用 |
| 错误日志数 | 突增 50% | 异常情况 |

**步骤 10：记录部署结果**

部署完成后记录：
- 部署时间
- 操作人
- 服务名称
- 旧版本 → 新版本
- 配置变更内容
- 部署结果（成功/失败）
- 关键指标快照

---

## 3. 回滚方案

### 3.1 触发回滚的条件

部署后出现以下情况应立即回滚：
- 健康检查不通过
- 5xx 错误率 > 5% 且持续 3 分钟
- 核心功能完全不可用
- 数据库连接异常
- 内存/CPU 持续飙升

### 3.2 回滚操作步骤

```bash
# Docker Compose 回滚
docker compose up -d --no-deps <service-name>:<previous-version>

# Kubernetes 回滚
kubectl rollout undo deployment/<service-name>
```

**回滚验证**：
- [ ] 服务恢复到上一个版本
- [ ] 健康检查通过
- [ ] 错误率下降到正常水平
- [ ] 核心功能恢复

### 3.3 回滚后处理

1. 保存部署失败日志和指标
2. 分析失败原因
3. 修复问题后重新走部署流程
4. 记录到部署失败台账

---

## 4. 常见问题与解决方案

### 4.1 服务启动失败

**现象**：容器启动后立即退出。

**可能原因**：
1. 配置错误（缺少必需的环境变量）
2. 数据库连接失败
3. 依赖服务不可用
4. 镜像构建错误

**解决方案**：
```bash
# 1. 查看容器日志
docker logs <container-name> --tail=100

# 2. 检查环境变量
docker exec <container-name> env | grep -E "DATABASE|REDIS|SECRET"

# 3. 检查依赖服务
ping <database-host>
nc -zv <database-host> <port>
```

### 4.2 部署后性能下降

**现象**：部署后响应延迟升高、吞吐量下降。

**排查步骤**：
1. 比较部署前后的性能指标
2. 检查是否有新增的慢查询
3. 检查资源使用情况（CPU、内存、IO）
4. 检查是否有配置变更影响性能

### 4.3 配置未生效

**现象**：配置已更新但服务行为未变化。

**可能原因**：
1. 配置文件未正确挂载
2. 服务未重启
3. 环境变量优先级问题

**解决方案**：
```bash
# 1. 进入容器检查实际配置
docker exec <container-name> cat /app/.env

# 2. 检查环境变量
docker exec <container-name> env

# 3. 重启服务
docker restart <container-name>
```

---

## 5. 相关链接

- 部署脚本：`tools/deploy.sh`
- 回滚脚本：`tools/rollback.sh`
- 健康检查脚本：`tools/health-check.sh`
- Docker Compose 配置：`infra/docker-compose.prod.yml`
- Nginx 配置：`infra/nginx/conf.d/default.conf`
- 监控告警：`telemetry/alerts/alerts.yaml`

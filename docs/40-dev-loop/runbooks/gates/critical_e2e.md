# 关键路径 E2E 测试 (G-E2E-001)

## 门禁概述

| 项目 | 说明 |
|------|------|
| 门禁名称 | 关键路径 E2E 测试 |
| 门禁 ID | G-E2E-001 |
| 类型 | e2e |
| 触发条件 | 夜间定时任务，路径匹配 `game/**`、`services/vote/**`、`services/gateway/**` |
| 覆盖风险类型 | playability, regression, crash |

本门禁验证投票流程的端到端完整链路，包括投票周期管理、投票提交、结算、内容包发布与回滚，确保核心玩法路径可用。

---

## 常见失败原因

按出现频率从高到低排序：

### 1. 环境启动失败

测试环境的基础设施（数据库、Redis、消息队列等）无法正常启动，或服务依赖缺失，导致测试无法开始执行。

### 2. 服务不可用

后端服务启动后无法正常响应请求，包括端口未监听、接口 500 错误、权限验证失败、连接超时等问题。

### 3. 测试超时

测试用例执行时间超过预期阈值，可能是性能退化、死锁、无限循环、外部依赖响应慢等原因导致。

### 4. 数据不一致

测试执行后，数据库状态与预期不符，包括投票计数错误、状态机跳转异常、审计日志缺失、内容包状态不正确等。

---

## 解决方案

### 1. 环境启动失败

```bash
# 第一步：检查基础设施状态
cd infra && docker compose -f docker-compose.dev.yml ps

# 第二步：查看容器日志
docker compose -f docker-compose.dev.yml logs postgres
docker compose -f docker-compose.dev.yml logs redis

# 第三步：重启基础设施
docker compose -f docker-compose.dev.yml down
docker compose -f docker-compose.dev.yml up -d

# 第四步：等待服务就绪后重新运行测试
sleep 10
bash tools/playtest/run_vote_flow.sh
```

### 2. 服务不可用

```bash
# 第一步：检查服务进程是否在运行
ps aux | grep uvicorn

# 第二步：检查服务端口监听
ss -tlnp | grep 8000
ss -tlnp | grep 8001

# 第三步：查看服务日志
cd services/vote && tail -f logs/app.log
cd services/gateway && tail -f logs/app.log

# 第四步：重启服务
cd services/vote && uvicorn app.main:app --reload --port 8000 &
cd services/gateway && uvicorn app.main:app --reload --port 8001 &

# 第五步：健康检查验证
curl http://localhost:8000/api/v1/health
curl http://localhost:8001/api/v1/health

# 第六步：重新运行测试
bash tools/playtest/run_vote_flow.sh
```

### 3. 测试超时

```bash
# 第一步：查看详细日志，定位超时位置
bash tools/playtest/run_vote_flow.sh --verbose

# 第二步：检查是否有慢查询
# 开启慢查询日志
docker exec infra-postgres-1 psql -U postgres -c "SET log_min_duration_statement = 1000;"

# 第三步：检查数据库连接池
# 查看当前连接数
docker exec infra-postgres-1 psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# 第四步：增加超时时间重试
bash tools/playtest/run_vote_flow.sh --timeout 600

# 第五步：如果是性能退化，使用 profile 分析
bash tools/playtest/run_vote_flow.sh --profile
```

### 4. 数据不一致

```bash
# 第一步：查看测试失败的具体断言
bash tools/playtest/run_vote_flow.sh --verbose

# 第二步：检查数据库状态
docker exec infra-postgres-1 psql -U vote -d vote_db -c "SELECT * FROM vote_cycles ORDER BY created_at DESC LIMIT 5;"
docker exec infra-postgres-1 psql -U vote -d vote_db -c "SELECT * FROM votes ORDER BY created_at DESC LIMIT 10;"

# 第三步：检查状态机跳转是否正确
# 核对 vote_cycles.status 字段
# 核对 content_packages.status 字段

# 第四步：检查审计日志
docker exec infra-postgres-1 psql -U vote -d vote_db -c "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 20;"

# 第五步：清理测试数据后重跑
docker exec infra-postgres-1 psql -U vote -d vote_db -c "TRUNCATE votes, vote_cycles, audit_logs CASCADE;"
bash tools/playtest/run_vote_flow.sh
```

---

## 手动执行

```bash
# 基本执行方式
bash tools/playtest/run_vote_flow.sh

# 详细输出模式
bash tools/playtest/run_vote_flow.sh --verbose

# 指定超时时间（秒）
bash tools/playtest/run_vote_flow.sh --timeout 600

# 仅运行投票流程
bash tools/playtest/run_vote_flow.sh --scope vote

# 仅运行内容包流程
bash tools/playtest/run_vote_flow.sh --scope content

# 生成测试报告
bash tools/playtest/run_vote_flow.sh --report report.html

# 使用 pytest 直接运行（更灵活）
cd tools/playtest && pytest -v
cd tools/playtest && pytest -v -k "vote_flow"
cd tools/playtest && pytest -v -k "content_package"
```

---

## 升级路径

| 级别 | 处理方式 | 联系人 |
|------|----------|--------|
| 一级 | 按上述方案自行排查环境和服务问题 | QA Agent |
| 二级 | 服务代码 Bug，定位到具体模块 | 对应模块后端开发 |
| 三级 | 架构级问题（分布式事务、状态机） | 后端架构师 |
| 四级 | 生产环境 P0 级故障 | 项目负责人 + 运维 oncall |

**升级流程：**
1. 先尝试自行排查环境和配置问题，重跑测试
2. 连续 2 次失败且定位到代码 Bug，提交给对应模块后端开发
3. 涉及分布式事务、状态机等架构问题，升级到后端架构师
4. 生产环境出现 P0 级故障，立即上报项目负责人和运维 oncall

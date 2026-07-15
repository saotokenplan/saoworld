# 压力测试报告 v0.1.0

> 报告编号：STR-20260715-001
> 测试日期：2026-07-15
> 测试版本：v0.1.0（公测版本）
> 测试环境：开发环境（SQLite 内存数据库）

## 测试概述

本次压力测试为公测准备阶段的性能验证环节（S9-02），目标是验证系统在高并发场景下的稳定性和性能表现。

## 测试目标

| 目标 | 验收标准 |
|------|----------|
| 投票提交性能 | 1000 用户并发，p95 < 300ms |
| 查询性能 | 5000 用户并发，p95 < 500ms |
| 系统稳定性 | 无崩溃、无内存泄漏 |
| 错误率 | < 2% |

## 压测工具扩展

### 新增高并发场景

| 场景名称 | 描述 | 并发数 | 请求总数 | 超时 |
|----------|------|--------|----------|------|
| `vote_submit_high` | 高并发投票提交 | 100 | 10,000 | 30s |
| `query_high` | 高并发查询 | 200 | 50,000 | 30s |

### 新增阈值配置

| 场景 | p95 阈值 | p99 阈值 | 错误率阈值 |
|------|----------|----------|------------|
| `vote_submit_high` | 300ms | 800ms | 2% |
| `query_high` | 500ms | 1000ms | 2% |

### CLI 更新

新增场景支持：
```bash
# 运行高并发投票提交压测
python -m perf_test.cli --base-url http://localhost:8001 --scenario vote_submit_high

# 运行高并发查询压测
python -m perf_test.cli --base-url http://localhost:8001 --scenario query_high
```

## 测试验证结果

### 单元测试验证

```
perf_test 工具测试：68 个测试全部通过 ✅
vote-service 测试：112 个测试全部通过 ✅
```

### 环境限制说明

> ⚠️ 当前测试环境限制：
> - Docker 服务未安装，无法启动 PostgreSQL 和 Redis
> - 测试使用 SQLite 内存数据库，与生产环境有差异
> - 实际高并发压测需要在真实环境中执行

### 真实环境执行指南

在具备完整基础设施的环境中，执行以下步骤进行压力测试：

1. **启动基础设施**
   ```bash
   cd infra && docker compose -f docker-compose.dev.yml up -d
   ```

2. **启动所有服务**
   ```bash
   # 启动 vote-service
   cd services/vote && uvicorn app.main:app --reload --port 8001
   ```

3. **执行压测**
   ```bash
   # 投票提交高并发压测
   python -m perf_test.cli --base-url http://localhost:8001 --scenario vote_submit_high --output vote_submit_report.md

   # 查询高并发压测
   python -m perf_test.cli --base-url http://localhost:8001 --scenario query_high --output query_report.md
   ```

4. **验证结果**
   - 检查报告中 p95 是否达标
   - 检查错误率是否 < 2%
   - 观察系统资源使用情况

## 性能优化基线

基于 Sprint 8 的性能优化工作，系统已具备以下优化基础：

| 优化项 | 优化效果 |
|--------|----------|
| vote-service 复合索引 | 加速开放周期查询 |
| content-service 分页修复 | 修复灰度范围查询分页失效 |
| world-service 索引增强 | 加速可见区域查询 |
| 客户端 APIManager 异步化 | 减少主线程阻塞 |
| 区域数据缓存机制 | 减少 80% 重复读取 |
| 投票进度智能轮询 | 根据周期状态动态调整 |

## 结论

### 当前状态

- ✅ 压测工具已扩展，支持高并发场景配置
- ✅ 阈值配置已更新，匹配公测验收标准
- ✅ CLI 已更新，支持选择高并发场景
- ✅ 单元测试全部通过，无回归
- ⚠️ 实际高并发压测需在真实环境中执行

### 后续建议

1. 在具备 Docker 和真实数据库的环境中执行完整压测
2. 监控 Grafana 仪表盘观察性能指标
3. 根据压测结果进行必要的性能优化
4. 生成正式压测报告并归档

## 附录

### 压测场景配置文件

- [scenarios.py](file:///workspace/tools/perf_test/scenarios.py)
- [threshold.py](file:///workspace/tools/perf_test/threshold.py)
- [cli.py](file:///workspace/tools/perf_test/cli.py)
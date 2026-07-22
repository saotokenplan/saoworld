# 性能压测门禁（Performance Test Gate）

## 门禁概述

| 项目 | 说明 |
|------|------|
| 门禁 ID | G-NONFUNC-001 / G-NONFUNC-002 / G-NONFUNC-003 |
| 覆盖风险类型 | performance, regression |
| 触发方式 | 手动 / 灰度发布前 / 定期压测 |
| 工具位置 | `tools/perf_test/` |
| 规范来源 | `docs/20-specs/backend-data-spec.md`（响应时间要求）<br>`docs/10-requirements/packages/first-slice/acceptance/api-acceptance.md`<br>`docs/10-requirements/packages/first-slice/acceptance/vote-acceptance.md` |

本门禁用于验证项目核心接口的响应时间是否满足 `docs/20-specs/backend-data-spec.md` 等规范中的性能要求：

| 接口 | p95 阈值 | p99 阈值 | 错误率阈值 |
|------|---------|---------|-----------|
| `POST /api/v1/votes/submit`（投票提交） | < 300ms | < 500ms | < 1% |
| `GET /api/v1/votes/current`（投票查询） | < 100ms | < 200ms | < 1% |
| `GET /api/v1/content/updates`（内容查询） | < 100ms | < 200ms | < 1% |

## 工具能力

`tools/perf_test/` 是一款基于 `httpx` + `asyncio` 的异步压测工具，无需引入 locust / wrk / vegeta 等外部压测框架。

核心模块：

- `stats.py`：延迟统计（p50 / p95 / p99 / qps / error_rate）
- `load_runner.py`：异步负载执行器（httpx + asyncio.Semaphore）
- `threshold.py`：阈值校验（blocker / warn 级别）
- `report.py`：Markdown / JSON 报告生成
- `scenarios.py`：内置核心接口场景（vote_submit / vote_query / content_query）
- `cli.py`：命令行入口

## 常见失败原因

| 现象 | 可能原因 | 解决方案 |
|------|----------|----------|
| p95 超过 300ms（投票提交） | 数据库索引缺失 / 锁竞争 / 序列化逻辑重 | 检查 `votes` 表索引（`votes_candidate_id_idx`）；分析 SQL 执行计划；考虑加入缓存 |
| p95 超过 100ms（查询接口） | N+1 查询 / 未命中缓存 / 大量数据返回 | 检查 N+1；为常用查询路径加缓存；分页限制 |
| 错误率超过 1% | 上游限流 / 数据库连接耗尽 / 业务校验失败 | 检查 `audit_logs` 写入是否有瓶颈；调整连接池；分析 4xx/5xx 比例 |
| 工具运行报错 | base_url 不通 / JWT Token 缺失 | 确认服务已启动；通过 `--header` 注入 Authorization 头 |

## 解决方案

### 1. 本地开发环境验证

```bash
# 启动目标服务
cd services/vote && uvicorn app.main:app --reload --port 8001

# 安装 perf_test 工具
cd tools/perf_test && pip install -e ".[dev]"

# 运行全部默认场景
python -m perf_test.cli --base-url http://localhost:8001

# 仅运行投票查询场景
python -m perf_test.cli --base-url http://localhost:8001 --scenario vote_query

# 输出 JSON 报告
python -m perf_test.cli --base-url http://localhost:8001 --format json --output /tmp/perf.json
```

### 2. 灰度发布前验证

```bash
# 针对预发布环境运行
python -m perf_test.cli --base-url https://staging.example.com \\
  --header "Authorization: Bearer $STAGING_TOKEN" \\
  --format markdown \\
  --output perf-staging-$(date +%Y%m%d).md
```

### 3. 在 CI 中使用

可作为 GitHub Actions 的定时任务或 workflow_dispatch 任务：

```yaml
- name: Run performance test
  run: |
    cd tools/perf_test
    pip install -e ".[dev]"
    python -m perf_test.cli \\
      --base-url ${{ env.STAGING_URL }} \\
      --header "Authorization: Bearer ${{ secrets.PERF_TOKEN }}" \\
      --format json \\
      --output perf-report.json
- name: Upload performance report
  uses: actions/upload-artifact@v4
  with:
    name: perf-report
    path: tools/perf_test/perf-report.json
```

## 手动执行

### 准备测试环境

1. 确认目标服务已启动（如 `vote-service` 监听 `http://localhost:8001`）
2. 准备 JWT Token（如需鉴权）
3. 安装 `tools/perf_test` 工具

### 运行压测

```bash
cd tools/perf_test

# 默认场景（投票提交 50 并发 / 投票查询 100 并发 / 内容查询 100 并发）
python -m perf_test.cli --base-url http://localhost:8001

# 自定义请求头
python -m perf_test.cli --base-url http://localhost:8001 \\
  --header "Authorization: Bearer test-token" \\
  --header "X-Trace-Id: perf-trace-001"
```

### 解读报告

报告包含：
- 每个场景的 count / error_count / error_rate / qps / min / avg / p50 / p95 / p99 / max
- 阈值校验结果（PASS / FAIL）
- 总体通过情况

`blocker` 级别失败 → 退出码 2，CI 流水线应阻塞。
`warn` 级别失败 → 不阻塞，但需要关注。

## 升级路径

| 情况 | 处理方式 |
|------|----------|
| blocker 失败（p95 超阈值） | 必须修复性能问题后再发布；分析 SQL 慢查询、加索引、缓存 |
| warn 失败（p99 超阈值） | 记录到 issue 池，本迭代内处理 |
| 持续高错误率 | 立即停止发布，检查 5xx 错误日志 |
| 工具自身异常 | 检查 `tools/perf_test/tests/` 单元测试是否通过；提交 issue 修复 |
| 需要新增场景 | 在 `tools/perf_test/scenarios.py` 中添加工厂函数，并对应增加门禁注册表条目 |

## 相关链接

- 工具目录：`tools/perf_test/`
- 工具 README：`tools/README.md`（待补充）
- 规范来源：
  - `docs/20-specs/backend-data-spec.md`（响应时间要求）
  - `docs/10-requirements/packages/first-slice/acceptance/api-acceptance.md`
  - `docs/10-requirements/packages/first-slice/acceptance/vote-acceptance.md`
- 门禁注册表：`docs/40-dev-loop/gate_registry.yaml`

# 执行摘要：perf_test 接入 CI 流水线 + 扩展压测场景 + P4 可观测性基础设施

## 任务标识

- task_id：`auto-20260713-1200`
- 工作分支：`auto/auto-20260713-1200`

## 本轮完成的工作清单

1. **perf_test 接入 CI 流水线**
   - ci.yml 的 lint/type-check/test 矩阵添加 perf_test
   - 新建 `.github/workflows/perf.yml` 夜间性能测试 workflow（cron 每日3点UTC + workflow_dispatch + push tags v*）
   - G-NONFUNC-001/002/003 门禁触发方式从 manual 改为 nightly

2. **扩展 3 个核心接口压测场景**
   - world_region_query（GET /api/v1/world/regions，p95 < 100ms）
   - player_profile_query（GET /api/v1/player/profile，p95 < 200ms）
   - content_package_detail（GET /api/v1/content/packages/{id}，p95 < 100ms）
   - 更新 scenarios.py、threshold.py、cli.py
   - 补充 5 个新测试用例，perf_test 测试从 63 增加到 68
   - 新增 G-NONFUNC-004/005/006 门禁

3. **P4 可观测性基础设施**
   - 8 个后端服务新增 OpenTelemetry 分布式追踪中间件（TracingMiddleware + setup_tracing）
   - 创建 SLO 定义文件（telemetry/slo/slo-definitions.yaml，8 个核心 SLO）
   - 创建分布式追踪 Runbook（docs/runbook/gates/distributed-tracing.md）

## 修改的文件清单

### CI/CD 配置
- `.github/workflows/ci.yml` - 添加 perf_test 到矩阵
- `.github/workflows/perf.yml` - 新建夜间性能测试 workflow

### perf_test 工具
- `tools/perf_test/scenarios.py` - 新增 3 个场景
- `tools/perf_test/threshold.py` - 新增 3 组阈值
- `tools/perf_test/cli.py` - 注册新场景
- `tools/perf_test/tests/test_scenarios.py` - 新增测试用例
- `tools/perf_test/tests/test_cli.py` - 更新场景数量断言

### 门禁注册表
- `docs/40-dev-loop/gate_registry.yaml` - 更新门禁触发方式 + 新增 3 个门禁

### 分布式追踪（8 个服务各 2 个文件）
- `services/vote/app/core/tracing.py` - 新建
- `services/vote/app/main.py` - 集成追踪
- `services/world/app/core/tracing.py` - 新建
- `services/world/app/main.py` - 集成追踪
- `services/content/app/core/tracing.py` - 新建
- `services/content/app/main.py` - 集成追踪
- `services/generation/app/core/tracing.py` - 新建
- `services/generation/app/main.py` - 集成追踪
- `services/review/app/core/tracing.py` - 新建
- `services/review/app/main.py` - 集成追踪
- `services/player/app/core/tracing.py` - 新建
- `services/player/app/main.py` - 集成追踪
- `services/ops/app/core/tracing.py` - 新建
- `services/ops/app/main.py` - 集成追踪
- `services/gateway/app/core/tracing.py` - 新建
- `services/gateway/app/main.py` - 集成追踪

### SLO 定义
- `telemetry/slo/slo-definitions.yaml` - 新建

### 文档
- `docs/runbook/gates/distributed-tracing.md` - 新建
- `docs/00-governance/project-status.md` - 更新状态
- `docs/40-dev-loop/auto-plan-20260713-1200.md` - 更新状态为已完成

## 验证结果

- perf_test：68 个测试全部通过
- vote-service：80 个测试全部通过
- content-service：65 个测试全部通过
- world-service：85 个测试全部通过
- player-service：128 个测试全部通过
- ruff 检查：All checks passed

## 遗留问题与下一步建议

- OpenTelemetry 追踪中间件当前为 Phase 1（基础请求追踪），Phase 2 可集成完整 OTel SDK（自动 instrumentation + span 自动创建）
- SLO 定义文件当前为声明式定义，后续可接入 Sloth/Pyxie 等 SLO 计算工具生成 Prometheus recording rules 和 Grafana 仪表盘
- 夜间性能测试 workflow 需要实际部署环境才能运行，当前 CI 中 perf_test 以单元测试验证为主

# 分布式追踪 Runbook

> 门禁类型：nonfunctional（可观测性基础设施）
> 创建日期：2026-07-13

## 概述

本项目使用 OpenTelemetry 实现分布式追踪，为所有 8 个后端服务提供请求级别的追踪能力。

## 追踪架构

- **追踪协议**：W3C Trace Context（traceparent 头）+ X-Trace-Id 自定义头
- **中间件**：TracingMiddleware（每个 FastAPI 服务）
- **导出**：OTLP → Jaeger/Tempo（通过环境变量控制启用）
- **启用条件**：`{SERVICE_NAME}_TRACING_ENABLED=true`

## 常见问题

### 追踪 ID 丢失
- **症状**：响应头中没有 X-Trace-Id
- **原因**：请求头未携带 X-Trace-Id，或追踪中间件未启用
- **解决**：确保客户端传递 X-Trace-Id 头，检查环境变量配置

### 追踪数据未导出
- **症状**：Jaeger/Tempo 中无追踪数据
- **原因**：OTLP 导出器未配置或目标不可达
- **解决**：检查 OTEL_EXPORTER_OTLP_ENDPOINT 环境变量

## 手动执行

```bash
# 启用追踪（以 vote-service 为例）
export VOTE_TRACING_ENABLED=true
uvicorn app.main:app --reload
```

## SLO 监控

SLO 定义文件：`telemetry/slo/slo-definitions.yaml`

关键 SLO：
- SLO-VOTE-001：投票提交 p95 < 300ms
- SLO-VOTE-002：投票查询 p95 < 100ms
- SLO-CONTENT-001：内容查询 p95 < 100ms
- SLO-GATEWAY-001：网关可用性 > 99.99%

## 升级路径

- Phase 1：基础追踪中间件（当前）
- Phase 2：完整 OpenTelemetry SDK 集成（自动 instrumentation）
- Phase 3：追踪数据与分析平台集成

# Runbook: Gateway Service Unit Tests (G-UNIT-009)

> gate_id: G-UNIT-009
> gate_name: Service Unit Tests (gateway)
> gate_type: unit
> owner: Backend Agent

## 门禁概述

Gateway Service Unit Tests 是 gateway-service 的单元测试门禁，验证 API 网关核心功能：JWT 认证中间件、令牌桶限流、请求追踪、反向代理路由等。

**触发条件**：
- 路径：`services/gateway/**`
- 触发：`on_pr`

**执行命令**：
```bash
cd services/gateway && pytest
```

**预期耗时**：45 秒

## 常见失败原因

### 1. JWT 认证中间件失败

**现象**：
- 认证测试失败
- 有效令牌被拒绝或无效令牌被允许

**解决方案**：
```bash
cd services/gateway && pytest -k "auth" -v
# 检查文件：services/gateway/app/core/auth.py
# 确认 JWT 验证逻辑和密钥配置是否正确
```

### 2. 限流中间件失败

**现象**：
- 限流测试失败
- 请求未被正确限流或过度限流

**解决方案**：
```bash
cd services/gateway && pytest -k "limit" -v
# 检查文件：services/gateway/app/core/limiter.py
# 确认令牌桶限流配置是否正确
```

### 3. 反向代理路由失败

**现象**：
- 代理测试失败
- 请求未被正确路由到目标服务

**解决方案**：
```bash
cd services/gateway && pytest -k "proxy" -v
# 检查文件：services/gateway/app/core/proxy.py
# 确认路由映射配置是否正确
```

### 4. 请求追踪中间件失败

**现象**：
- 追踪测试失败
- X-Request-Id 或 X-Trace-Id 未正确传递

**解决方案**：
```bash
cd services/gateway && pytest -k "trace" -v
# 检查文件：services/gateway/app/core/deps.py
# 确认追踪头传递逻辑是否正确
```

## 手动执行

```bash
cd services/gateway && pytest
cd services/gateway && pytest tests/test_auth.py -v
cd services/gateway && pytest tests/test_proxy.py::test_route_mapping -v
cd services/gateway && pytest --cov=app --cov-report=html
```

## 升级路径

| 级别 | 处理方式 |
|------|----------|
| 认证问题 | 检查 auth.py 中的 JWT 验证逻辑和密钥配置 |
| 限流问题 | 检查 limiter.py 中的限流配置 |
| 路由问题 | 检查 proxy.py 中的路由映射配置 |
| 无法解决 | 联系 Backend Agent |

## 相关链接

- 规范文档：`docs/30-api/api-overview.md`
- 测试文件：`services/gateway/tests/`
- 门禁注册表：`docs/40-dev-loop/gate_registry.yaml`
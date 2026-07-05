# Runbook: Critical Path E2E (G-E2E-001)

> gate_id: G-E2E-001
> gate_name: Critical Path E2E (Vote Flow)
> gate_type: e2e
> owner: QA Agent

## 门禁概述

Critical Path E2E (Vote Flow) 是投票流程的端到端测试门禁，验证投票周期管理、投票提交、结算的完整链路，以及内容包发布/回滚流程和事件总线集成。

**触发条件**：
- 路径：`game/**`, `services/vote/**`, `services/content/**`, `services/gateway/**`, `workers/**`, `tools/playtest/**`
- 触发：`nightly`

**执行命令**：
```bash
bash tools/playtest/run_vote_flow.sh
```

**执行命令（完整集成测试）**：
```bash
cd tools/playtest && pytest -v
```

**预期耗时**：300 秒

## 常见失败原因

### 1. 服务未启动

**现象**：
- 测试无法连接到后端服务
- 提示连接超时

**解决方案**：
```bash
# 启动 vote-service
cd services/vote && uvicorn app.main:app --reload &

# 启动 gateway-service
cd services/gateway && uvicorn app.main:app --reload &

# 等待服务就绪
sleep 10

# 重新运行测试
bash tools/playtest/run_vote_flow.sh
```

### 2. 数据库未初始化

**现象**：
- 测试无法创建投票周期
- 数据库表不存在

**解决方案**：
```bash
# 启动数据库
cd infra && docker compose -f docker-compose.dev.yml up -d

# 执行迁移
cd services/vote && alembic upgrade head

# 重新运行测试
bash tools/playtest/run_vote_flow.sh
```

### 3. 投票结算失败

**现象**：
- 关闭投票时结算失败
- 无法确定获胜候选项

**解决方案**：
```bash
# 查看详细错误日志
bash tools/playtest/run_vote_flow.sh --verbose

# 检查投票结算逻辑
# 文件：services/vote/app/repositories/vote_repo.py

# 运行单元测试验证
cd services/vote && pytest -k "close" -v
```

### 4. 权限验证失败

**现象**：
- 测试无法通过认证
- 提示权限不足

**解决方案**：
```bash
# 查看详细错误日志
bash tools/playtest/run_vote_flow.sh --verbose

# 检查测试用的 JWT Token 是否有效
# 检查 auth middleware 配置

# 运行认证测试
cd services/vote && pytest -k "auth" -v
```

### 5. 内容包发布失败

**现象**：
- 创建内容包失败
- 灰度发布或回滚操作失败

**解决方案**：
```bash
# 查看详细错误日志
cd tools/playtest && pytest -v -k "content"

# 检查内容包服务
# 文件：services/content/app/repositories/content_repo.py

# 运行内容服务测试
cd services/content && pytest -v
```

### 6. 事件总线集成失败

**现象**：
- 事件发布/订阅测试失败
- 投票结算后事件未触发

**解决方案**：
```bash
# 查看详细错误日志
cd tools/playtest && pytest -v -k "event"

# 检查事件总线配置
# 文件：workers/events/event_bus.py

# 运行 workers 测试
cd workers && pytest -v -k "event"
```

## 手动执行

```bash
# 运行完整投票流程测试
bash tools/playtest/run_vote_flow.sh

# 运行详细模式
bash tools/playtest/run_vote_flow.sh --verbose

# 运行单个步骤
bash tools/playtest/run_vote_flow.sh --step create_cycle
bash tools/playtest/run_vote_flow.sh --step submit_vote
bash tools/playtest/run_vote_flow.sh --step close_and_count

# 运行完整端到端集成测试
cd tools/playtest && pytest -v

# 运行投票链路测试
cd tools/playtest && pytest -v -k "vote"

# 运行内容包流程测试
cd tools/playtest && pytest -v -k "content"

# 运行事件总线测试
cd tools/playtest && pytest -v -k "event"
```

## 升级路径

| 级别 | 处理方式 |
|------|----------|
| 服务未启动 | 启动后端服务 |
| 数据库未初始化 | 启动数据库并执行迁移 |
| 结算失败 | 检查投票结算逻辑 |
| 权限失败 | 检查 JWT Token 和权限配置 |
| 无法解决 | 联系 QA Agent 或 Backend Agent |

## 相关链接

- 规范文档：`docs/packages/first-slice/`
- 测试脚本：`tools/playtest/run_vote_flow.sh`
- 门禁注册表：`docs/40-dev-loop/gate_registry.yaml`
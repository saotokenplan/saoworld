# ops-service

运营管理服务 - 后台运营入口、仪表盘、运营操作记录、系统状态汇总监控。

## 文档定位

- 本文档是 `ops-service` 的本地入口，用于概览服务职责、启动方式和当前实现范围。
- 本文档不替代 `docs/20-specs/` 中的正式执行规范，也不替代 `docs/30-api/` 中的接口参考。
- 涉及权限、错误码、运营动作边界和发布流程时，应回到上游规范确认。

## 技术栈

- Python 3.11+
- FastAPI + Uvicorn
- SQLAlchemy 2.0 (异步)
- PostgreSQL 16+
- Alembic (数据迁移)
- Pydantic 2.x
- python-jose (JWT)
- structlog (结构化日志)
- Prometheus metrics (业务指标)
- pytest + pytest-asyncio

## 目录结构

```
ops-service/
├── app/
│   ├── api/              # 路由处理器
│   ├── core/             # 配置、数据库、认证、错误、指标、健康检查客户端
│   ├── domain/           # SQLAlchemy ORM 模型
│   ├── repositories/     # 数据访问层
│   ├── schemas/          # Pydantic 请求/响应模型
│   ├── tasks/            # Celery 异步任务
│   └── main.py           # FastAPI 应用入口
├── alembic/              # 数据库迁移
│   └── versions/         # 迁移脚本
├── tests/                # pytest 测试
├── pyproject.toml        # 项目依赖与工具配置
├── alembic.ini           # Alembic 配置
└── .env.example          # 环境变量模板
```

## 快速启动

```bash
# 安装依赖
pip install -e ".[dev]"

# 复制环境变量
cp .env.example .env

# 运行数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --port 8006
```

## API 文档

开发模式下访问:
- Swagger: http://localhost:8006/docs
- Redoc: http://localhost:8006/redoc

## API Endpoints

### 运营 API

| Method | Path | Description | Scope |
|--------|------|-------------|-------|
| GET | `/api/v1/health` | 健康检查 | Public |
| GET | `/api/v1/ops/dashboard` | 获取仪表盘数据 | `ops:*` |
| GET | `/api/v1/ops/dashboard/history` | 仪表盘历史记录（分页） | `ops:*` |
| GET | `/api/v1/ops/actions` | 运营操作记录列表（分页、过滤） | `ops:*` |
| GET | `/api/v1/ops/actions/{action_id}` | 运营操作记录详情 | `ops:*` |
| GET | `/api/v1/ops/system/status` | 系统状态汇总（所有服务健康检查） | `ops:*` |

## 核心功能

- [x] 仪表盘数据查询与历史记录
- [x] 运营操作记录查询（支持按类型、状态、操作人过滤）
- [x] 系统状态汇总监控（HTTP 调用各服务健康检查接口）
- [x] JWT 认证与权限校验（ops:* scope）
- [x] 统一响应 envelope 格式
- [x] 审计日志持久化（audit_logs 表）
- [x] Prometheus 业务指标
- [x] Alembic 数据库迁移
- [x] 结构化日志（request_id, trace_id）
- [x] 健康检查客户端（HTTP 调用各服务 /health 接口）

## 数据库表

- `ops_dashboards` - 运营仪表盘表
- `ops_actions` - 运营操作记录表
- `audit_logs` - 审计日志表

## 环境变量

见 `.env.example`

## 测试与代码检查

```bash
# 运行测试
pytest

# 代码检查
ruff check .
mypy app
```

## Next Steps

- [ ] 添加运营操作执行接口（如：发布内容包、创建投票周期等）
- [ ] 添加系统告警配置与通知
- [ ] 添加运营数据统计报表
- [ ] 添加玩家管理运营接口
- [ ] 添加内容审核运营后台

## 相关文档

- `docs/20-specs/backend-data-spec.md` - 运营侧数据模型、审计要求和服务边界
- `docs/20-specs/product-spec.md` - 运营动作涉及的产品边界与发布背景
- `docs/30-api/api-overview.md` - 运营相关 API 总览
- `docs/30-api/api-permissions.md` - 运营接口权限矩阵
- `docs/30-api/api-error-codes.md` - 标准错误码与冲突语义
- `docs/40-dev-loop/runbooks/operations/` - 发布、回滚、部署和迁移 runbook

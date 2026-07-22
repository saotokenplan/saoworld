# review-service

内容审核服务 - 负责结构化校验、风险判断、质量评分和人工复核流转。

## 文档定位

- 本文档是 `review-service` 的本地入口，用于概览服务职责、启动方式和当前实现范围。
- 本文档不替代 `docs/20-specs/` 中的正式执行规范，也不替代 `docs/30-api/` 中的接口参考。
- 涉及审核状态机、风险等级、权限和发布前校验时，应回到上游规范确认。

## 技术栈

- Python 3.11+
- FastAPI + Uvicorn
- SQLAlchemy 2.0 (异步)
- PostgreSQL 16+
- Alembic (数据迁移)
- Pydantic 2.0+
- structlog (结构化日志)
- Prometheus metrics (业务指标)
- pytest + pytest-asyncio

## 目录结构

```
review-service/
├── app/
│   ├── api/              # 路由处理器
│   ├── core/             # 配置、数据库、认证、错误、指标、事件发布
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
uvicorn app.main:app --reload --port 8004

# 运行测试
pytest

# 代码检查
ruff check .
mypy app
```

## API 文档

- Swagger: http://localhost:8004/docs （debug 模式）
- Redoc: http://localhost:8004/redoc （debug 模式）

## API Endpoints

### Ops API

| Method | Path | Description | Scope/Role |
|--------|------|-------------|------------|
| GET | `/api/v1/health` | 健康检查 | Public |
| POST | `/api/v1/ops/reviews` | 创建审核记录 | `review:approve` |
| GET | `/api/v1/ops/reviews` | 审核记录列表（分页） | `review:approve` |
| GET | `/api/v1/ops/reviews/{id}` | 审核记录详情 | `review:approve` |
| PUT | `/api/v1/ops/reviews/{id}` | 更新审核记录 | `review:approve` |
| POST | `/api/v1/ops/reviews/{id}/approve` | 审核批准 | `review:approve` |
| POST | `/api/v1/ops/reviews/{id}/reject` | 审核拒绝 | `review:approve` |

## 核心功能

- [x] 审核记录管理（创建、查询、列表、更新）
- [x] 审核批准/拒绝接口
- [x] 审核状态机：pending → approved / rejected / manual_review
- [x] 风险等级：low / medium / high / critical
- [x] JWT 认证与权限校验（review:approve scope）
- [x] 统一响应 envelope 格式
- [x] 审计日志持久化（audit_logs 表）
- [x] Prometheus 业务指标
- [x] 事件发布（review.batch.completed）
- [x] Alembic 数据库迁移
- [x] 结构化日志（request_id, trace_id）

## 数据库表

- `review_records` - 审核记录表
- `audit_logs` - 审计日志表

## Next Steps

- [ ] 集成内容检查四项工具（世界一致性、数值边界、内容安全、重复度）
- [ ] 添加人工复核工作流
- [ ] 添加审核规则模板管理
- [ ] 添加审核质量评分与统计

## 相关文档

- `docs/20-specs/backend-data-spec.md` - 审核记录、状态机与审计基线
- `docs/20-specs/content-generation-spec.md` - 内容生成、审核与发布前检查约束
- `docs/30-api/api-overview.md` - 审核相关 API 总览
- `docs/30-api/api-permissions.md` - 审核与运营接口权限矩阵
- `docs/30-api/api-error-codes.md` - 标准错误码与冲突语义
- `docs/40-dev-loop/runbooks/gates/` - 内容检查与质量门禁相关 runbook

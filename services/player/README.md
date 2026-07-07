# player-service

玩家服务 - 负责账号、角色、成长、声望、章节进度、玩家任务和区域解锁管理。

## 技术栈

- Python 3.11+
- FastAPI + Uvicorn
- SQLAlchemy 2.0（异步模式）
- PostgreSQL + asyncpg
- Alembic (数据迁移)
- Pydantic + pydantic-settings
- python-jose（JWT）
- structlog（结构化日志）
- Prometheus metrics (业务指标)
- pytest + pytest-asyncio

## 目录结构

```
player-service/
├── app/
│   ├── api/              # 路由处理器
│   ├── core/             # 配置、数据库、认证、错误、指标
│   ├── domain/           # SQLAlchemy ORM 模型
│   ├── repositories/     # 数据访问层
│   ├── schemas/          # Pydantic 请求/响应模型
│   ├── tasks/            # Celery 异步任务
│   └── main.py           # FastAPI 应用入口
├── alembic/              # 数据库迁移
│   └── versions/         # 迁移脚本
├── scripts/              # 工具脚本
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

# 运行服务（开发模式）
uvicorn app.main:app --reload --port 8005

# API 文档（debug模式）
# http://localhost:8005/docs
# http://localhost:8005/redoc
```

## 测试

```bash
# 运行测试
pytest

# 代码检查
ruff check .
mypy app
```

## API Endpoints

### 玩家 API

| Method | Path | Description | Scope |
|--------|------|-------------|-------|
| GET | `/api/v1/health` | 健康检查 | Public |
| GET | `/api/v1/player/info` | 获取玩家信息 | player |
| GET | `/api/v1/player/quests` | 获取玩家任务列表（分页） | `quests:read` |
| GET | `/api/v1/player/regions` | 获取玩家已解锁区域（分页） | player |

### 运营 API

| Method | Path | Description | Role |
|--------|------|-------------|------|
| POST | `/api/v1/ops/players` | 创建玩家 | ops |
| GET | `/api/v1/ops/players` | 玩家列表（分页） | ops |
| GET | `/api/v1/ops/players/{player_id}` | 玩家详情 | ops |
| PUT | `/api/v1/ops/players/{player_id}` | 更新玩家信息 | ops |
| POST | `/api/v1/ops/players/{player_id}/regions/{region_id}/unlock` | 解锁玩家区域 | ops |

## 核心功能

- [x] 玩家信息管理（创建、查询、更新）
- [x] 玩家任务管理（任务列表、状态过滤、分页）
- [x] 玩家区域解锁管理
- [x] 任务状态机：available → active → completed / failed
- [x] JWT 认证与权限校验
- [x] 统一响应 envelope 格式
- [x] 审计日志持久化（audit_logs 表）
- [x] Prometheus 业务指标
- [x] Alembic 数据库迁移
- [x] 结构化日志（request_id, trace_id）
- [x] 自定义 UUID 类型（兼容 SQLite 测试环境）

## 数据库表

- `players` - 玩家表
- `player_quests` - 玩家任务表
- `player_regions` - 玩家区域表
- `audit_logs` - 审计日志表

## 环境变量

参考 `.env.example` 文件。

## Next Steps

- [ ] 添加玩家声望系统
- [ ] 添加玩家成长/经验系统
- [ ] 添加玩家成就系统
- [ ] 添加玩家好友/社交系统

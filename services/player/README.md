# Player Service

玩家服务，负责账号、角色、成长、声望、章节进度管理。

## 技术栈

- FastAPI + Uvicorn
- SQLAlchemy 2.0（异步模式）
- PostgreSQL + asyncpg
- Pydantic + pydantic-settings
- python-jose（JWT）
- structlog（结构化日志）

## 快速启动

```bash
# 安装依赖
pip install -e ".[dev]"

# 运行服务（开发模式）
uvicorn app.main:app --reload

# API 文档（debug模式）
# http://localhost:8000/docs
# http://localhost:8000/redoc
```

## 测试

```bash
# 运行测试
pytest

# 代码检查
ruff check .
mypy app
```

## 环境变量

参考 `.env.example` 文件。
# review-service

内容审核服务 - 负责结构化校验、风险判断和人工复核流转

## 技术栈

- Python 3.11+
- FastAPI + Uvicorn
- SQLAlchemy 2.0 (异步)
- PostgreSQL 16+
- Pydantic 2.0+
- pytest + pytest-asyncio

## 启动命令

```bash
# 安装依赖
pip install -e ".[dev]"

# 启动开发服务器
uvicorn app.main:app --reload

# 运行测试
pytest

# 代码检查
ruff check .
mypy app
```

## API 文档

- Swagger: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc

## 核心功能

- 审核记录管理（创建、查询、更新）
- 审核批准/拒绝接口
- JWT 认证与权限校验
- 统一响应 envelope 格式
- 审计日志持久化

## 数据库表

- `review_records` - 审核记录
- `audit_logs` - 审计日志
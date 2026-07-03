# ops-service

运营管理服务 - 后台运营入口、指标汇总、Issue 触发

## 功能

- 仪表盘数据查询与历史
- 运营操作记录查询
- 系统状态汇总监控

## 技术栈

- FastAPI + Uvicorn
- SQLAlchemy 2.0 (异步)
- Pydantic 2.x
- PostgreSQL 16+
- JWT 认证

## 快速启动

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## API 文档

开发模式下访问:
- http://localhost:8000/docs
- http://localhost:8000/redoc

## 环境变量

见 `.env.example`

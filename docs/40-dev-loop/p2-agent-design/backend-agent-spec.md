# Backend Agent 技术规范

> 文档状态：draft
> 适用阶段：P2（多代理协同期）
> 维护要求：持续维护

## 职责定义

Backend Agent 负责编写投票服务、生成服务、审核服务和运营后台接口。

## 输入

| 输入来源 | 格式 | 说明 |
|---------|------|------|
| design-note.md | markdown | 技术设计文档 |
| 现有代码 | Python | 当前服务实现 |
| API 规范 | yaml | OpenAPI 定义 |

## 输出

| 输出产物 | 格式 | 说明 |
|---------|------|------|
| 路由文件 | Python | routes.py |
| 模型文件 | Python | models.py |
| 仓库文件 | Python | repositories/*.py |
| Schema 文件 | Python | schemas/*.py |
| 测试文件 | Python | tests/*.py |

## 核心流程

1. 读取 design-note.md 和现有代码
2. 实现 API 路由
3. 实现数据模型
4. 实现数据访问层
5. 编写测试用例
6. 运行测试验证

## 关键能力

- FastAPI 开发
- SQLAlchemy 异步开发
- Pydantic 数据验证
- 测试驱动开发

## 约束条件

- 必须遵循 10-python-backend.md 规范
- 必须遵循 11-database.md 规范
- 必须遵循 12-api-design.md 规范
- 必须编写测试用例

## 验收标准

- ruff 检查通过
- mypy 类型检查通过
- pytest 测试通过
- 接口响应符合 envelope 格式
# 接口参考入口

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本目录作为 `docs/30-api/` 的统一入口，用于收拢 API 总览、权限矩阵、错误码、OpenAPI 草案、接口样例和客户端 UI 参考，降低接口检索成本。

## 适用范围

- 适用于后端、客户端、测试和运营在实施或联调阶段查询接口信息。
- 适用于查找 API 路径、权限、错误码、样例和 OpenAPI 草案。
- 不替代 `docs/20-specs/backend-data-spec.md` 中的正式执行约束。

## 当前定位

- 本目录承担接口参考层角色，负责回答“接口在哪、怎么查、有哪些样例”。
- 服务边界、数据模型、状态机、异步任务和审计要求仍以 `docs/20-specs/` 为准。
- 若本目录与 `docs/20-specs/backend-data-spec.md` 冲突，以后者为准。

## 文档列表

- `api-overview.md`
  - API 域、服务边界和完整接口导航入口
- `api-permissions.md`
  - 角色、Scope 和权限矩阵
- `api-error-codes.md`
  - 统一错误码和状态冲突说明
- `openapi-draft.md`
  - OpenAPI 草案说明和组织方式
- `openapi-v1-draft.yaml`
  - OpenAPI 草案文件
- `api-examples-*.md`
  - 各服务的接口样例集合
- `client-ui/`
  - 客户端 UI 与接口消费相关的页面流转和交互参考

## 建议阅读顺序

1. 先读 `api-overview.md`，获得全局接口视图
2. 再读 `api-permissions.md` 和 `api-error-codes.md`
3. 需要契约细节时查看 `openapi-draft.md` 与 `openapi-v1-draft.yaml`
4. 需要按服务联调时查看 `api-examples-*.md`
5. 需要结合客户端页面理解交互时查看 `client-ui/README.md`

## 维护边界

- 新增接口参考、样例、错误码和 OpenAPI 内容时优先落在本目录
- 不在本目录重复定义产品范围、数据库设计和工程协作规范
- 如需新增正式约束，应优先更新 `docs/20-specs/`，本目录再同步索引

## 与其他文档的关系

- `docs/20-specs/backend-data-spec.md`
  - 提供后端与数据执行规范，本目录负责索引和参考展示
- `docs/10-requirements/`
  - 提供需求背景，不承担接口权威定义
- `docs/30-api/client-ui/`
  - 提供客户端界面和接口消费关系的局部入口

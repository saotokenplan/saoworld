# API 视图

> 说明：本目录用于快速理解“最小投票链路”涉及的接口切片、认证要求和错误场景；正式 API 契约以 `docs/30-api/` 与 `docs/20-specs/backend-data-spec.md` 为准。

## 本目录看什么

- `vote-endpoints.md`：最小投票链路涉及的玩家接口与运营接口速览
- `auth-requirements.md`：认证、角色、Scope、链路追踪与审计关注点
- `error-codes.md`：按业务场景整理的错误分组，而不是第二套错误码字典

## 建议阅读顺序

1. 先看 `vote-endpoints.md`，理解最小链路包含哪些接口
2. 再看 `auth-requirements.md`，确认谁可以调用、写接口需要哪些保护
3. 最后看 `error-codes.md`，理解联调和验收时最常见的失败场景

## 不在这里维护什么

- 不重复维护请求头、响应 envelope、分页规则和字段明细
- 不重复维护完整错误码枚举和状态机
- 不把本目录扩展成第二套正式接口文档

## 源文档入口

- API 总览：`docs/30-api/api-overview.md`
- 权限矩阵：`docs/30-api/api-permissions.md`
- 错误码：`docs/30-api/api-error-codes.md`
- 后端与数据规范：`docs/20-specs/backend-data-spec.md`

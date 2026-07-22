# 投票接口清单

> 版本：v1.0.0
> 创建时间：2026-07-04

> 说明：本文档用于快速理解“最小投票链路”涉及的接口切片；正式 API 契约、请求头要求、错误码与响应结构以 `docs/30-api/` 和 `docs/20-specs/backend-data-spec.md` 为准。

## 阅读方式

- 本文档只保留最小投票链路涉及的接口视图、调用意图和联调关注点。
- 请求头、响应 envelope、错误结构、分页规则与鉴权要求请直接查 `docs/30-api/`。
- 如接口路径、 Scope 或字段与源规范冲突，以源规范为准。

## 玩家接口

| 接口 | 方法 | Scope | 在最小链路中的作用 | 联调关注点 |
|------|------|-------|------------------|------------|
| `/api/v1/votes/current` | GET | `votes:read` | 给玩家展示当前开放周期和候选项 | 当前周期是否开放、候选项信息是否足够支持展示 |
| `/api/v1/votes/submit` | POST | `votes:submit` | 接收玩家投票并返回提交结果 | 幂等键、玩家身份、候选项归属、风控拦截 |
| `/api/v1/votes/history` | GET | `votes:history:read` | 展示历史结果与实际落地情况 | 分页、章节过滤、结果和内容包关联 |

## 运营接口

| 接口 | 方法 | Scope | 在最小链路中的作用 | 联调关注点 |
|------|------|-------|------------------|------------|
| `/api/v1/ops/vote-cycles` | POST | `ops:vote-cycles:write` | 创建新周期并配置候选项 | 幂等、创建原因、候选项数量与时间窗 |
| `/api/v1/ops/vote-cycles/{id}/schedule` | POST | `ops:vote-cycles:write` | 将草稿周期推进到待开放状态 | 状态合法性、时间配置、审计记录 |
| `/api/v1/ops/vote-cycles/{id}/open` | POST | `ops:vote-cycles:write` | 打开已配置好的投票周期 | 周期冲突、时间合法性、审计记录 |
| `/api/v1/ops/vote-cycles/{id}/close` | POST | `ops:vote-cycles:write` | 关闭进行中的投票周期 | 状态切换是否合法、关闭后是否停止提交 |
| `/api/v1/ops/vote-cycles/{id}/finalize` | POST | `ops:vote-cycles:write` | 触发结算并把结果送入后续链路 | 无候选项、状态冲突、结果是否可追溯 |

## 本切片特别关注

- 玩家侧最重要的是“看见当前投票”“提交成功且不重复计票”“能回看历史结果”。
- 运营侧最重要的是“可配置周期”“可追踪状态推进”“可把结果交给后续生成链路”。
- 错误码只需理解错误场景，不建议在本切片继续维护第二套 code 枚举。

## 源文档入口

- API 总览：`docs/30-api/api-overview.md`
- 权限矩阵：`docs/30-api/api-permissions.md`
- 错误码：`docs/30-api/api-error-codes.md`
- 后端与数据规范：`docs/20-specs/backend-data-spec.md`

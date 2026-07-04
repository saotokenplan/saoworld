# 认证与权限要求

> 版本：v1.0.0
> 创建时间：2026-07-04

## 认证方式

### JWT Bearer Token

- 认证方案：OIDC 签发的 JWT Bearer Token
- 请求头：`Authorization: Bearer <token>`
- Token 格式：标准 JWT（Header.Payload.Signature）

### Token 内容要求

JWT Token 必须包含以下声明：

| 声明 | 说明 |
|------|------|
| sub | 操作者唯一标识（OIDC sub） |
| roles | 角色列表（player/ops/reviewer/system） |
| scopes | 权限范围列表 |
| exp | 过期时间 |
| iat | 签发时间 |

## 权限角色

### player

- 面向普通玩家
- 可访问世界、任务、投票和内容更新查询接口
- 不允许访问运营、审核、生成和发布类接口

### ops

- 面向运营和配置角色
- 可创建投票周期、发布内容包、触发回滚
- 所有写操作都必须记录操作者和原因

### reviewer

- 面向审核和批准角色
- 可处理内容审核流、批准内容对象
- 不应直接承担内容发布职责，除非额外具备 ops 权限

### system

- 面向 Agent、任务队列和自动化流程
- 主要处理内部长任务、事件消费、状态流转
- 不对外暴露为普通客户端权限

## Scope 矩阵

### 投票接口 Scope

| 方法 | 路径 | 所需 Scope | 适用角色 |
|------|------|-----------|----------|
| GET | /api/v1/votes/current | votes:read | player, system |
| POST | /api/v1/votes/submit | votes:submit | player |
| GET | /api/v1/votes/history | votes:history:read | player, ops, system |

### 运营接口 Scope

| 方法 | 路径 | 所需 Scope | 适用角色 |
|------|------|-----------|----------|
| POST | /api/v1/ops/vote-cycles | ops:vote-cycles:write | ops |
| POST | /api/v1/ops/vote-cycles/{id}/schedule | ops:vote-cycles:write | ops |
| POST | /api/v1/ops/vote-cycles/{id}/open | ops:vote-cycles:write | ops |
| POST | /api/v1/ops/vote-cycles/{id}/close | ops:vote-cycles:write | ops |
| POST | /api/v1/ops/vote-cycles/{id}/finalize | ops:vote-cycles:write | ops |

## 必选请求头

### 所有接口

| 请求头 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 除公开接口外必选 | Bearer Token |

### 写接口

| 请求头 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| X-Trace-Id | string | 是 | 全链路追踪ID |
| X-Player-Id | string | 玩家接口必选 | 玩家ID |

### 运营写接口

| 请求头 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Idempotency-Key | string | 是 | 幂等键，防止重复操作 |

## 必选响应头

所有响应必须返回：
- X-Request-Id：请求追踪ID
- X-Trace-Id：全链路追踪ID（如果请求携带了）

## 认证错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|------------|------|
| INVALID_TOKEN | 401 | Token 格式或签名非法 |
| INSUFFICIENT_SCOPE | 403 | 访问令牌缺少所需作用域 |
| TOKEN_EXPIRED | 401 | Access Token 已过期 |

## 权限校验流程

1. 解析 Authorization 头中的 Bearer Token
2. 验证 Token 签名和过期时间
3. 提取角色和 Scope 声明
4. 校验接口所需的 Scope
5. 将用户信息注入请求上下文
6. 处理认证失败响应

## 安全要求

### Token 安全

- 使用 HTTPS 传输 Token
- Token 过期时间不宜过长（建议 15-30 分钟）
- 支持 Refresh Token 机制
- Token 泄露时可主动失效

### 权限最小化

- 遵循最小权限原则
- 每个角色只授予必要的权限
- Scope 细粒度控制

### 敏感操作保护

- 运营写接口必须携带 Idempotency-Key
- 所有敏感操作必须记录审计日志
- 关键操作可配置二次确认或审批链

### 风控要求

- 投票接口必须做设备与行为风控
- 频率限制和冷却期
- 异常行为聚类分析

## 审计要求

以下接口调用必须进入审计链：

| 接口 | action | 说明 |
|------|--------|------|
| POST /api/v1/ops/vote-cycles | vote_cycle_create | 创建投票周期 |
| POST /api/v1/ops/vote-cycles/{id}/schedule | vote_cycle_scheduled | 计划投票周期 |
| POST /api/v1/ops/vote-cycles/{id}/open | vote_cycle_opened | 开放投票 |
| POST /api/v1/ops/vote-cycles/{id}/close | vote_cycle_closed | 关闭投票 |
| POST /api/v1/ops/vote-cycles/{id}/finalize | vote_cycle_finalized | 结算投票 |
| POST /api/v1/votes/submit | vote_submit | 提交投票 |

每条审计记录至少包含：
- request_id
- trace_id
- operator_role
- operator_id
- action
- target_id
- reason
- result
- occurred_at
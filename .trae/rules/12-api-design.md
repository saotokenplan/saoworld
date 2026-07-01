# 12 - API 设计规范

> 适用角色：后端开发、前端/客户端开发
> 本文件定义 API 通用约定、响应格式、错误码、权限Scope。

## 通用约定

### 协议与格式

- 协议：HTTPS
- 数据格式：JSON（`Content-Type: application/json`）
- API 版本前缀：所有接口统一使用 `/api/v1`
- 时间格式：ISO 8601 / RFC 3339（UTC，如 `2026-07-01T10:30:00Z`）

### 认证方式

- 认证方案：OIDC 签发的 JWT Bearer Token
- 请求头：`Authorization: Bearer <token>`
- 细粒度权限通过 OAuth 2.0 Scope 控制（见后文权限表）

### 必选请求头

| 请求头 | 类型 | 必选 | 说明 |
|--------|------|------|------|
| `Authorization` | string | 除公开接口外必选 | Bearer Token |
| `X-Trace-Id` | string | 写接口必选 | 全链路追踪ID |
| `Idempotency-Key` | string | 运营写接口必选 | 幂等键，防止重复操作 |
| `X-Player-Id` | UUID | 玩家接口必选 | 玩家ID（投票、世界查询等） |
| `X-Request-Id` | string | 可选 | 客户端自定义请求ID，不传则服务端生成 |

### 必选响应头

所有响应必须返回：
- `X-Request-Id`：请求追踪ID
- `X-Trace-Id`：全链路追踪ID（如果请求携带了）

---

## 成功响应格式

所有成功响应使用统一 envelope 包装：

```json
{
  "request_id": "req_abc123def456",
  "data": {
    "vote_cycle_id": "vc_xxx",
    "candidates": []
  },
  "meta": {
    "total": 100,
    "limit": 20,
    "offset": 0
  },
  "trace_id": "trace_xxx"
}
```

字段说明：
- `request_id`：服务端生成的请求追踪ID（必填）
- `data`：业务数据（必填）
- `meta`：分页信息（列表接口必填，其他接口可选）
- `trace_id`：全链路追踪ID（写接口必填返回）

---

## 错误响应格式

所有错误响应使用统一结构：

```json
{
  "code": "ERROR_CODE",
  "message": "人类可读错误描述",
  "request_id": "req_abc123def456",
  "details": [
    {
      "location": "body",
      "field": "candidate_id",
      "issue": "not_found",
      "rejected_value": "xxx"
    }
  ],
  "trace_id": "trace_xxx"
}
```

字段说明：
- `code`：**机器可读错误码**，客户端分支判断必须基于此字段
- `message`：人类可读错误描述，仅供展示，**不可**作为客户端分支判断依据
- `request_id`：请求追踪ID
- `details`：字段级错误详情数组（参数校验错误等场景提供）
  - `location`：错误位置（`body`/`header`/`path`/`query`）
  - `field`：字段名
  - `issue`：错误类型标识
  - `rejected_value`：被拒绝的值
- `trace_id`：全链路追踪ID

---

## 标准错误码

服务端必须使用以下已定义错误码：

| 错误码 | HTTP 状态码 | 说明 |
|--------|------------|------|
| `NO_OPEN_VOTE_CYCLE` | 404 | 当前没有开放的投票周期 |
| `INVALID_VOTE_STATE` | 409 | 投票周期状态不允许投票 |
| `CANDIDATE_NOT_FOUND` | 404 | 候选项不存在或不属于当前周期 |
| `CANDIDATE_NOT_ACTIVE` | 409 | 候选项当前不可投票（已撤回/已当选） |
| `ALREADY_VOTED` | 409 | 玩家在本周期已投票 |
| `INVALID_PLAYER_ID` | 400 | 无效的玩家 ID 格式（非UUID） |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |
| `HTTP_<status_code>` | 对应状态码 | 通用 HTTP 错误包装 |

错误码命名约定：
- 使用大写下划线命名（UPPER_SNAKE_CASE）
- 名词在前，错误描述在后
- 4xx 错误码描述客户端问题，5xx 错误码描述服务端问题

---

## 接口权限 Scope

所有接口必须配置对应的权限 Scope：

| Scope | 适用角色 | 说明 |
|-------|---------|------|
| `world:read` | player, system | 查询世界区域信息 |
| `quests:read` | player, system | 查询玩家任务列表 |
| `votes:read` | player, system | 查询当前投票周期与候选项 |
| `votes:history:read` | player, ops, system | 查询历史投票结果与落地情况 |
| `votes:submit` | player | 提交投票 |
| `content:read` | player, system, ops | 查询内容包和更新列表 |
| `content:release` | ops | 发布内容包 |
| `content:rollback` | ops | 回滚内容包 |
| `review:approve` | reviewer, ops | 审核批准内容对象 |
| `ops:vote-cycles:write` | ops | 创建投票周期 |

### 角色定义

| 角色 | 说明 |
|------|------|
| `player` | 普通玩家（世界查询、任务查询、投票、内容更新查询） |
| `ops` | 运营人员（创建投票周期、发布内容包、回滚内容包） |
| `reviewer` | 审核人员（审核批准内容对象；默认不具备发布权限） |
| `system` | Agent/自动化任务（内部长任务、事件消费、状态流转；不对外暴露） |

---

## 已定义 API 端点

### 玩家与世界接口

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| GET | `/api/v1/world/regions` | `world:read` | 获取当前可见区域列表 |
| GET | `/api/v1/world/regions/{region_id}` | `world:read` | 获取区域详情和状态 |
| GET | `/api/v1/quests` | `quests:read` | 获取玩家任务列表 |

### 投票接口

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| GET | `/api/v1/votes/current` | `votes:read` | 获取当前投票周期与候选项 |
| POST | `/api/v1/votes/submit` | `votes:submit` | 提交投票 |
| GET | `/api/v1/votes/history` | `votes:history:read` | 获取历史投票结果与落地情况 |

### 内容投放接口

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| GET | `/api/v1/content/updates` | `content:read` | 获取当前玩家可见的新内容包 |
| GET | `/api/v1/content/packages/{content_package_id}` | `content:read` | 获取内容包摘要 |

### 运营接口

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| POST | `/api/v1/ops/vote-cycles` | `ops:vote-cycles:write` | 创建投票周期 |
| POST | `/api/v1/ops/review/{object_id}/approve` | `review:approve` | 批准内容对象 |
| POST | `/api/v1/ops/content-packages/{id}/release` | `content:release` | 发布内容包 |
| POST | `/api/v1/ops/content-packages/{id}/rollback` | `content:rollback` | 回滚内容包 |

### 健康检查接口

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| GET | `/api/v1/health` | 公开 | 服务健康检查 |

---

## 幂等性要求

- 所有运营写接口必须支持 `Idempotency-Key` 请求头
- 服务端根据幂等键识别重复请求，直接返回首次处理结果
- 幂等键存储在对应业务表中（如 `votes.idempotency_key`）

---

## 分页约定

列表接口使用 offset-based 分页：

**请求参数（Query）：**
- `limit`：每页数量，默认 20，范围 1-100
- `offset`：偏移量，默认 0，>= 0

**响应 meta：**
```json
{
  "meta": {
    "total": 100,
    "limit": 20,
    "offset": 0
  }
}
```

---

## 相关规则

- Python 后端开发规范 → [10-python-backend.md](./10-python-backend.md)
- 数据库设计规范 → [11-database.md](./11-database.md)
- 安全规范 → [50-security.md](./50-security.md)

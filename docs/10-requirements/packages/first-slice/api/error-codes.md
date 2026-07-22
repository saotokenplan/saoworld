# 错误码清单

> 版本：v1.0.0
> 创建时间：2026-07-04

> 说明：本文档用于快速理解最小投票链路会遇到的错误场景；正式错误码枚举与命名以 `docs/30-api/api-error-codes.md` 和 `docs/20-specs/backend-data-spec.md` 为准。如出现同义 code，优先以源规范收敛。

## 通用错误返回结构

```json
{
  "code": "INVALID_VOTE_STATE",
  "message": "当前投票周期不可投票",
  "request_id": "req_vote_current_409",
  "details": [
    {
      "location": "body",
      "field": "vote_cycle_id",
      "issue": "state_conflict",
      "rejected_value": "vc_001"
    }
  ],
  "trace_id": "trace_xxx"
}
```

## 通用 HTTP 层错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|------------|------|
| INVALID_ARGUMENT | 400 | 请求参数非法 |
| INVALID_TOKEN | 401 | Token 格式或签名非法 |
| INSUFFICIENT_SCOPE | 403 | 访问令牌缺少所需作用域 |
| RESOURCE_NOT_FOUND | 404 | 目标资源不存在 |
| CONFLICT | 409 | 资源状态冲突（通用） |
| RATE_LIMITED | 429 | 触发限流或频率限制 |
| SERVICE_UNAVAILABLE | 503 | 服务暂不可用 |

## 投票接口错误码

### 投票周期相关

| 错误码 | HTTP 状态码 | 说明 | 适用接口 |
|--------|------------|------|----------|
| VOTE_CYCLE_NOT_FOUND | 404 | 当前不存在有效投票周期 | GET /votes/current, POST /votes/submit |
| INVALID_VOTE_STATE | 409 | 当前投票周期不可投票 | GET /votes/current, POST /votes/submit |
| VOTE_CYCLE_CLOSED | 409 | 投票周期已关闭 | POST /votes/submit |
| VOTE_CYCLE_CONFLICT | 409 | 投票周期创建冲突 | POST /ops/vote-cycles, POST /ops/vote-cycles/{id}/open |
| NO_CANDIDATES_FOUND | 409 | 投票周期下无有效候选项 | POST /ops/vote-cycles/{id}/finalize |

### 候选项相关

| 错误码 | HTTP 状态码 | 说明 | 适用接口 |
|--------|------------|------|----------|
| CANDIDATE_NOT_FOUND | 404 | 候选项不存在 | POST /votes/submit |
| CANDIDATE_OUT_OF_SCOPE | 409 | 候选项不属于当前投票周期 | POST /votes/submit |

### 玩家相关

| 错误码 | HTTP 状态码 | 说明 | 适用接口 |
|--------|------------|------|----------|
| PLAYER_NOT_ELIGIBLE | 403 | 玩家不满足投票资格 | POST /votes/submit |
| DUPLICATE_VOTE | 409 | 同一玩家在同一周期重复投票 | POST /votes/submit |

### 风控相关

| 错误码 | HTTP 状态码 | 说明 | 适用接口 |
|--------|------------|------|----------|
| VOTE_RISK_BLOCKED | 403 | 命中设备或行为风控 | POST /votes/submit |

## 运营接口错误码

### 通用运营错误

| 错误码 | HTTP 状态码 | 说明 | 适用接口 |
|--------|------------|------|----------|
| REASON_REQUIRED | 400 | 敏感操作缺少原因字段 | 所有运营写接口 |

## 预留错误码

| 错误码 | HTTP 状态码 | 说明 | 预计使用阶段 |
|--------|------------|------|--------------|
| TOKEN_EXPIRED | 401 | Access Token 已过期 | 接入 Refresh Token 后 |
| INTERNAL_ERROR | 500 | 服务内部未知异常 | 服务端实现时 |
| AUDIT_WRITE_FAILED | 500 | 审计记录写入失败 | 服务端实现时 |
| TRACE_ID_MISSING | 500 | 系统未正确生成链路追踪字段 | 服务端实现时 |

## 错误码使用建议

### 客户端

- 对 401 和 403 做明确鉴权提示，不要混用
- 对 400 带 details 的错误，可按 field 和 issue 做表单级错误映射
- 对 409 做状态冲突处理，不要直接重试所有请求
- 对 429 做指数退避和频率提示

### 服务端

- 同一错误语义只使用一个稳定 code，不要为同类错误新造近义词
- 不要把数据库底层异常直接透传给客户端
- 对运营和审核写接口，错误响应中仍应保留 request_id 方便审计
- 参数校验错误应尽可能提供 details 数组

## details.issue 分类

| 类别 | issue 值 | 说明 |
|------|----------|------|
| 参数校验 | required | 缺少必填字段 |
| 参数校验 | pattern_mismatch | 字段格式不匹配正则 |
| 参数校验 | unsupported_enum | 枚举值不在允许范围内 |
| 参数校验 | must_be_between_1_and_100 | 数值超出范围 |
| 鉴权授权 | missing_required_scope | Token 缺少所需 scope |

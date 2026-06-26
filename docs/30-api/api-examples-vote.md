# 投票接口样例

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本文档用于补充投票链路的请求响应样例，帮助后续实现服务端接口、客户端接入和 OpenAPI 草案编写。

## 适用范围

- 适用于投票链路相关接口的请求响应样例编写和联调参考。
- 适用于服务端实现、客户端接入和 OpenAPI 草案下沉前的样例对齐。
- 不替代接口总览、权限矩阵和错误码文档，而是作为具体接口层面的补充示例。

## 当前定位

- 本文档是接口样例，不替代详细规范。
- 接口边界以 `docs/30-api/api-overview.md` 为准。
- 权限与审计要求以 `docs/30-api/api-permissions.md` 为准。
- 错误码以 `docs/30-api/api-error-codes.md` 为准。

## 适用接口

- `GET /api/v1/votes/current`
- `POST /api/v1/votes/submit`
- `GET /api/v1/votes/history`

## 通用约定

- 协议：`HTTPS + JSON`
- 认证：`Bearer Token`
- 时间格式：ISO 8601
- 所有成功响应统一带 `request_id`
- 写接口成功响应统一补 `trace_id`
- 列表接口统一使用 `data + meta`
- 详情接口统一使用 `data + meta`
- 写接口统一使用 `data + meta`，其中 `meta.idempotent_replay` 表示是否命中幂等重放

## `GET /api/v1/votes/current`

### 作用

- 获取当前投票周期
- 获取候选项列表
- 获取玩家是否有资格投票
- 获取投票截止时间和当前状态

### 请求示例

```http
GET /api/v1/votes/current HTTP/1.1
Authorization: Bearer <player_token>
Accept: application/json
```

### 成功响应示例

```json
{
  "request_id": "req_vote_current_001",
  "data": {
    "vote_cycle": {
      "vote_cycle_id": "cycle_202606",
      "chapter_id": "chapter_02",
      "status": "open",
      "starts_at": "2026-06-26T08:00:00Z",
      "ends_at": "2026-06-28T08:00:00Z"
    },
    "player_context": {
      "player_id": "player_001",
      "eligible": true,
      "reason": null,
      "has_voted": false,
      "vote_weight": 1.05
    },
    "candidates": [
      {
        "candidate_id": "candidate_01",
        "title": "荒原废墟扩张",
        "summary": "机械教团开始向废墟腹地推进。",
        "region_scope": ["region_wasteland_01"],
        "risk_tags": ["高冲突", "资源紧张"]
      },
      {
        "candidate_id": "candidate_02",
        "title": "流亡者据点重建",
        "summary": "流亡者试图重建旧聚落并争夺补给线。",
        "region_scope": ["region_wasteland_01"],
        "risk_tags": ["阵营对抗", "局部事件增加"]
      },
      {
        "candidate_id": "candidate_03",
        "title": "遗迹异变调查",
        "summary": "遗迹深处出现异常能量波动，引发新的探索任务。",
        "region_scope": ["region_ruins_02"],
        "risk_tags": ["高危险", "限时事件"]
      }
    ]
  },
  "meta": {
    "resource_type": "vote_cycle"
  }
}
```

### 常见错误

```json
{
  "code": "VOTE_CYCLE_NOT_FOUND",
  "message": "当前不存在有效投票周期",
  "request_id": "req_vote_current_404"
}
```

```json
{
  "code": "INVALID_VOTE_STATE",
  "message": "当前投票周期不可投票",
  "request_id": "req_vote_current_409"
}
```

## `POST /api/v1/votes/submit`

### 作用

- 提交玩家在当前投票周期中的投票结果
- 返回投票记录、票权和受理结果

### 请求示例

```http
POST /api/v1/votes/submit HTTP/1.1
Authorization: Bearer <player_token>
Content-Type: application/json
Accept: application/json
Idempotency-Key: 8dbdfe06-6c75-49f2-a177-bf6d3d7a85d1
```

```json
{
  "vote_cycle_id": "cycle_202606",
  "candidate_id": "candidate_03"
}
```

### 成功响应示例

```json
{
  "request_id": "req_vote_submit_001",
  "trace_id": "trace_vote_submit_001",
  "data": {
    "vote_id": "vote_001",
    "vote_cycle_id": "cycle_202606",
    "candidate_id": "candidate_03",
    "accepted": true,
    "weight": 1.05,
    "submitted_at": "2026-06-26T09:12:33Z"
  },
  "meta": {
    "resource_type": "vote",
    "idempotent_replay": false,
    "accepted_at": "2026-06-26T09:12:33Z"
  }
}
```

### 幂等重复提交响应示例

```json
{
  "request_id": "req_vote_submit_002",
  "trace_id": "trace_vote_submit_001",
  "data": {
    "vote_id": "vote_001",
    "vote_cycle_id": "cycle_202606",
    "candidate_id": "candidate_03",
    "accepted": true,
    "weight": 1.05,
    "submitted_at": "2026-06-26T09:12:33Z"
  },
  "meta": {
    "resource_type": "vote",
    "idempotent_replay": true,
    "accepted_at": "2026-06-26T09:12:33Z"
  }
}
```

### 常见错误

请求体缺少候选项：

```json
{
  "code": "INVALID_ARGUMENT",
  "message": "投票请求参数不合法",
  "request_id": "req_vote_submit_400",
  "details": [
    {
      "location": "body",
      "field": "candidate_id",
      "issue": "required"
    }
  ]
}
```

玩家无资格：

```json
{
  "code": "PLAYER_NOT_ELIGIBLE",
  "message": "当前角色未满足投票资格",
  "request_id": "req_vote_submit_403"
}
```

重复投票：

```json
{
  "code": "DUPLICATE_VOTE",
  "message": "当前投票周期已提交过投票",
  "request_id": "req_vote_submit_409"
}
```

风控拦截：

```json
{
  "code": "VOTE_RISK_BLOCKED",
  "message": "当前请求命中投票风控规则",
  "request_id": "req_vote_submit_risk"
}
```

候选项不存在：

```json
{
  "code": "CANDIDATE_NOT_FOUND",
  "message": "候选项不存在",
  "request_id": "req_vote_candidate_404"
}
```

投票周期已关闭：

```json
{
  "code": "VOTE_CYCLE_CLOSED",
  "message": "当前投票周期已关闭",
  "request_id": "req_vote_submit_closed_409"
}
```

候选项超出当前投票周期范围：

```json
{
  "code": "CANDIDATE_OUT_OF_SCOPE",
  "message": "候选项不属于当前投票周期",
  "request_id": "req_vote_submit_scope_409"
}
```

请求频率超限：

```json
{
  "code": "RATE_LIMITED",
  "message": "请求过于频繁，请稍后再试",
  "request_id": "req_vote_submit_429"
}
```

## `GET /api/v1/votes/history`

### 作用

- 获取历史投票周期结果
- 获取各候选项得票情况
- 获取结果最终落地情况

### 请求示例

```http
GET /api/v1/votes/history?chapter_id=chapter_02&page=1&page_size=20 HTTP/1.1
Authorization: Bearer <player_token>
Accept: application/json
```

### 成功响应示例

```json
{
  "request_id": "req_vote_history_001",
  "data": [
    {
      "vote_cycle_id": "cycle_202606",
      "chapter_id": "chapter_02",
      "closed_at": "2026-06-28T08:00:00Z",
      "winner_candidate_id": "candidate_03",
      "winner_title": "遗迹异变调查",
      "total_votes": 128430,
      "candidates": [
        {
          "candidate_id": "candidate_01",
          "title": "荒原废墟扩张",
          "vote_percent": 29.4
        },
        {
          "candidate_id": "candidate_02",
          "title": "流亡者据点重建",
          "vote_percent": 31.1
        },
        {
          "candidate_id": "candidate_03",
          "title": "遗迹异变调查",
          "vote_percent": 39.5
        }
      ],
      "delivery": {
        "status": "gray",
        "content_package_id": "pkg_chapter_02_ruins_20260629_01",
        "affected_regions": ["region_ruins_02"]
      }
    }
  ],
  "meta": {
    "resource_type": "vote_history",
    "page": 1,
    "page_size": 20,
    "total": 1,
    "returned": 1,
    "has_more": false
  }
}
```

### 空结果示例

```json
{
  "request_id": "req_vote_history_002",
  "data": [],
  "meta": {
    "resource_type": "vote_history",
    "page": 1,
    "page_size": 20,
    "total": 0,
    "returned": 0,
    "has_more": false
  }
}
```

### 分页越界示例

```json
{
  "request_id": "req_vote_history_003",
  "data": [],
  "meta": {
    "resource_type": "vote_history",
    "page": 5,
    "page_size": 20,
    "total": 1,
    "returned": 0,
    "has_more": false
  }
}
```

### 常见错误

```json
{
  "code": "INVALID_ARGUMENT",
  "message": "分页参数不合法",
  "request_id": "req_vote_history_400",
  "details": [
    {
      "location": "query",
      "field": "page_size",
      "issue": "must_be_between_1_and_100",
      "rejected_value": "0"
    }
  ]
}
```

```json
{
  "code": "INSUFFICIENT_SCOPE",
  "message": "当前访问令牌缺少所需作用域",
  "request_id": "req_scope_403",
  "details": [
    {
      "location": "header",
      "field": "Authorization",
      "issue": "missing_required_scope",
      "rejected_value": "<required-scope>"
    }
  ]
}
```

## 审计与实现建议

### `GET /api/v1/votes/current`

- 可做缓存
- 响应中应明确玩家是否已投票
- 响应包装应保持 `request_id + data + meta`
- 若投票周期关闭，状态应与错误码语义一致

### `POST /api/v1/votes/submit`

- 应支持 `Idempotency-Key`
- 应保证 `vote_cycle_id + player_id` 唯一约束
- 应在风控通过后再落库
- 响应包装应保持 `request_id + trace_id + data + meta`

### `GET /api/v1/votes/history`

- 应支持分页
- 应支持按章节、区域或周期筛选
- 列表响应应统一返回 `meta.page/page_size/total/returned/has_more`
- 应返回“投票结果是否已落地”的最小状态信息

## 建议下一步

1. 继续补内容生成链路的接口样例文档
2. 再补运营发布链路的请求响应样例
3. 最后汇总到 `docs/30-api/openapi-draft.md`

## 与其他文档的关系

- `docs/30-api/api-overview.md`
  - 作为投票接口的上游总览，定义接口入口、职责和服务归属。
- `docs/30-api/api-permissions.md`
  - 定义投票接口的角色访问边界、审计要求和敏感操作约束。
- `docs/30-api/api-error-codes.md`
  - 定义本文件中成功与失败样例所对应的错误码语义。
- `docs/20-specs/backend-data-spec.md`
  - 作为更高权威的执行规范，约束投票链路与数据模型的最终实现边界。
- `docs/30-api/openapi-draft.md`
  - 作为本文件后续下沉到 OpenAPI 草案的汇总入口。

# 投票提交流程

> 版本：v1.0.0
> 创建时间：2026-07-04

## 概述

投票提交流程描述了玩家从查看投票到提交投票的完整操作序列，包含客户端和服务端的交互步骤。

## 客户端流程

### 步骤 1：进入投票界面

**操作**：玩家从游戏主界面进入投票界面

**客户端行为**：
- 检查本地缓存的投票周期信息
- 若无有效缓存，发起 API 请求

### 步骤 2：查询当前投票周期

**请求**：`GET /api/v1/votes/current`

**请求头**：
- Authorization: Bearer <token>

**服务端处理**：
1. 校验 Token 有效性
2. 查询当前 open 状态的投票周期
3. 查询关联的候选项列表
4. 组装响应数据

**响应**：
```json
{
  "request_id": "req_vote_current_xxx",
  "data": {
    "vote_cycle_id": "uuid-string",
    "chapter_id": "chapter_01",
    "status": "open",
    "starts_at": "2026-07-04T00:00:00Z",
    "ends_at": "2026-07-11T00:00:00Z",
    "candidates": [...]
  }
}
```

### 步骤 3：展示投票信息

**客户端行为**：
- 展示投票周期标题和时间
- 展示候选项列表（标题、摘要、影响区域）
- 展示投票截止倒计时

### 步骤 4：选择候选项

**操作**：玩家点击某个候选项

**客户端行为**：
- 高亮选中的候选项
- 展示候选项详细描述
- 展示风险标签和影响区域

### 步骤 5：提交投票

**请求**：`POST /api/v1/votes/submit`

**请求头**：
- Authorization: Bearer <token>
- X-Trace-Id: <trace_id>
- Idempotency-Key: <idempotency_key>
- X-Player-Id: <player_id>

**请求体**：
```json
{
  "vote_cycle_id": "uuid-string",
  "candidate_id": "uuid-string",
  "player_id": "uuid-string",
  "weight": 1.0,
  "device_fingerprint_hash": "string-hash",
  "reason": "可选，投票原因"
}
```

## 服务端流程

### 步骤 1：认证校验

**校验项**：
- Token 是否存在且有效
- Token 是否过期
- Token 是否包含 required_scope（votes:submit）

**错误响应**：
- 401 INVALID_TOKEN：Token 格式或签名非法
- 403 INSUFFICIENT_SCOPE：缺少所需 scope

### 步骤 2：参数校验

**校验项**：
- vote_cycle_id 是否为有效 UUID
- candidate_id 是否为有效 UUID
- player_id 是否为有效 UUID
- weight 是否在有效范围（0 < weight <= 10.0）
- device_fingerprint_hash 是否存在
- Idempotency-Key 是否存在

**错误响应**：
- 400 INVALID_ARGUMENT：参数校验失败

### 步骤 3：投票周期状态校验

**校验项**：
- 投票周期是否存在
- 投票周期状态是否为 open

**错误响应**：
- 404 VOTE_CYCLE_NOT_FOUND：投票周期不存在
- 409 INVALID_VOTE_STATE：投票周期状态不允许投票
- 409 VOTE_CYCLE_CLOSED：投票周期已关闭

### 步骤 4：候选项校验

**校验项**：
- 候选项是否存在
- 候选项是否属于当前投票周期
- 候选项状态是否为 active

**错误响应**：
- 404 CANDIDATE_NOT_FOUND：候选项不存在
- 409 CANDIDATE_OUT_OF_SCOPE：候选项不属于当前投票周期

### 步骤 5：重复投票校验

**校验项**：
- 玩家在本周期是否已投票（通过 UNIQUE 约束）

**错误响应**：
- 409 DUPLICATE_VOTE：同一玩家在同一周期重复投票

### 步骤 6：投票资格校验

**校验项**：
- 玩家是否存在
- 玩家是否满足投票资格门槛

**错误响应**：
- 403 PLAYER_NOT_ELIGIBLE：玩家不满足投票资格

### 步骤 7：风控校验

**校验项**：
- 设备指纹是否异常
- 投票频率是否正常

**错误响应**：
- 403 VOTE_RISK_BLOCKED：命中设备或行为风控

### 步骤 8：幂等性校验

**校验项**：
- Idempotency-Key 是否已存在（通过 UNIQUE 约束）

**处理逻辑**：
- 若幂等键已存在，直接返回首次处理结果
- 若幂等键不存在，继续执行

### 步骤 9：创建投票记录

**操作**：
- 生成 vote_id
- 创建投票记录到 votes 表
- 设置投票时间为当前时间

### 步骤 10：记录审计日志

**操作**：
- 写入 audit_logs 表
- action: vote_submit
- operator_role: player
- resource_type: vote
- resource_id: vote_id

### 步骤 11：返回响应

**成功响应**（200）：
```json
{
  "request_id": "req_vote_submit_xxx",
  "data": {
    "vote_id": "uuid-string",
    "vote_cycle_id": "uuid-string",
    "candidate_id": "uuid-string",
    "player_id": "uuid-string",
    "weight": 1.0,
    "created_at": "2026-07-04T10:30:00Z"
  },
  "trace_id": "trace_xxx"
}
```

## 客户端后续处理

### 步骤 1：展示投票成功

**客户端行为**：
- 展示投票成功提示
- 更新投票按钮状态为"已投票"
- 刷新候选项票数统计

### 步骤 2：缓存投票结果

**客户端行为**：
- 缓存投票记录
- 缓存投票时间
- 在本周期内不再允许投票

## 幂等性保障

### 客户端

- 生成唯一的 Idempotency-Key（建议使用 UUID）
- 保存 Idempotency-Key 直到投票周期结束
- 网络异常重试时使用相同的 Idempotency-Key

### 服务端

- 通过 UNIQUE (idempotency_key) 约束保证幂等
- 捕获唯一约束冲突异常
- 冲突时查询已有投票记录并返回

## 性能要求

- 投票提交接口 p95 响应时间 < 300ms
- 支持高并发投票（建议 > 1000 QPS）
- 数据库写入应使用批量操作或异步写入

## 错误处理

### 网络错误

**客户端行为**：
- 显示网络错误提示
- 提供重试按钮
- 重试时使用相同的 Idempotency-Key

### 服务端错误

**客户端行为**：
- 根据错误码展示对应的错误提示
- 409 DUPLICATE_VOTE：提示"您已在本周期投票"
- 404 CANDIDATE_NOT_FOUND：提示"候选项不存在"
- 403 PLAYER_NOT_ELIGIBLE：提示"您不满足投票资格"

### 超时处理

**客户端行为**：
- 设置请求超时时间（建议 5 秒）
- 超时后显示超时提示
- 提供重试按钮
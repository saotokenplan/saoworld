# 50 - 安全规范

> 适用角色：后端开发、安全、运营
> 本文件定义接口安全、风控、审计、密钥管理要求。

---

## 认证与授权

### JWT 认证

- 认证方式：OIDC 签发的 JWT Bearer Token
- Token 通过 `Authorization: Bearer <token>` 请求头传递
- JWT 中必须包含：
  - `sub`：操作者唯一标识（玩家ID或运营人员ID）
  - `scope`：权限列表（空格分隔）
  - `exp`：过期时间
- JWT 密钥生产环境必须替换默认值 `change-me-in-production`
- Access Token 有效期：30 分钟（可配置）
- 禁止在 JWT 中存放敏感信息（密钥、密码等）

### OAuth 2.0 Scope 权限控制

所有接口必须配置 Scope 权限校验，详见 [12-api-design.md](./12-api-design.md) 中的权限表。

角色与权限矩阵：

| 角色 | 说明 |
|------|------|
| `player` | 普通玩家：世界查询、任务查询、投票、内容查询 |
| `ops` | 运营人员：创建投票周期、发布、回滚、查看历史 |
| `reviewer` | 审核人员：审核批准内容（默认无发布权限） |
| `system` | 系统/Agent：内部任务、事件消费、状态流转（不对外暴露） |

---

## 运营接口安全

所有运营接口必须满足：

1. **操作者记录**：从 JWT `sub` 获取操作者ID，记录到审计日志
2. **操作原因**：请求体中必须包含 `reason` 字段，说明操作原因
3. **二次确认/审批链**：敏感操作（发布、回滚、批准内容）必须支持二次确认或审批流程
4. **幂等性**：所有写接口必须支持 `Idempotency-Key` 幂等键，防止重复操作
5. **请求体审计**：请求体和响应结果必须通过 `trace_id` 串联记录到审计日志

---

## 投票风控

投票接口必须实施以下风控措施：

1. **设备指纹**：`device_fingerprint_hash` 必填，用于识别刷票行为
2. **投票资格校验**：校验玩家章节进度、活跃度、贡献度门槛
3. **票权限制**：
   - 基础票权一致（weight 默认 1.0）
   - 贡献度修正倍率 **不超过 1.2**
   - weight 范围：`0 < weight <= 10.0`
4. **频率限制**：单设备/单玩家投票频率限制
5. **冷却期**：投票后存在冷却期，防止高频操作
6. **一人一票**：通过 `UNIQUE (vote_cycle_id, player_id)` 数据库约束保证一个周期每玩家只能投一票
7. **幂等键**：`idempotency_key` 全局唯一，防止客户端重试重复计票
8. **异常检测**：行为聚类分析识别异常投票模式
9. **人工复核**：高风险或接近阈值的投票结果进入人工复核

---

## 审计日志要求

以下操作必须记录审计日志（`audit_logs` 表）：

- 投票提交（`vote_submit`）
- 投票周期创建与状态变更（`vote_cycle_create`、`vote_cycle_status_change`）
- 内容审核批准/拒绝（`review_approve`、`review_reject`）
- 内容发布（`content_release`）
- 内容回滚（`content_rollback`）
- 其他敏感运营操作

审计日志每条记录必须包含：
- `trace_id`：全链路追踪ID（必填）
- `request_id`：API请求ID（可选）
- `operator_id`：操作者标识
- `operator_role`：操作者角色（player/ops/reviewer/system）
- `action`：操作类型
- `resource_type`：资源类型
- `resource_id`：资源ID
- `reason`：操作原因（运营写接口必填）
- `request_payload_jsonb`：请求体快照（可选）
- `result_status`：响应码或任务结果状态
- `created_at`：操作时间

审计日志表特殊要求：
- 按月做范围分区
- 应用数据库账号只有 INSERT/SELECT 权限，无 UPDATE/DELETE 权限
- 通过 `trace_id` 可串联同一操作的全链路日志

---

## 密钥与配置安全

- **绝对禁止将密钥、凭证提交到代码仓库**
- `.env` 文件已加入 `.gitignore`，使用 `.env.example` 提供模板（不含真实值）
- 敏感配置（数据库密码、JWT密钥、API密钥等）必须通过环境变量注入
- 生产环境密钥必须使用密钥管理服务（如 Vault、云厂商KMS）存储，不放在配置文件中
- 禁止在代码中硬编码密钥、密码、Token
- 禁止在日志中输出密钥、密码、Token 等敏感信息

---

## CORS 配置

- 开发环境允许所有来源（`allow_origins=["*"]`），但生产环境必须配置具体的允许来源
- 允许凭证（`allow_credentials=True`）
- 允许所有方法（开发阶段），生产环境按需开放
- 必须暴露 `X-Request-Id` 和 `X-Trace-Id` 响应头

---

## 错误处理安全

- 错误响应不暴露内部实现细节（堆栈跟踪、SQL语句、文件路径等）
- 生产环境 debug 模式必须关闭（`docs_url` 和 `redoc_url` 仅在 debug 模式下开放）
- 未捕获异常统一返回 `INTERNAL_ERROR` 错误码，不泄露具体错误信息
- 所有异常必须记录到日志（包含 stack trace），但不返回给客户端

---

## 相关规则

- API 设计规范 → [12-api-design.md](./12-api-design.md)
- Python 后端配置管理 → [10-python-backend.md](./10-python-backend.md)
- 数据库审计表设计 → [11-database.md](./11-database.md)
- 发布与回滚 → [42-release-rollback.md](./42-release-rollback.md)

# 执行摘要：auto-20260713-1800 - Sprint 4 S4-02「投票讨论区」

## 任务标识

- task_id：`auto-20260713-1800`
- 任务名称：Sprint 4 S4-02「投票讨论区」
- 工作分支：`auto/auto-20260713-1800`
- 任务状态：已完成（后端部分）

## 本轮完成的工作清单

### 1. 数据模型设计（完成）
- 新增三张核心表：
- `vote_discussions`（讨论主帖表）：discussion_id, vote_cycle_id, player_id, content, like_count, reply_count, status, created_at, updated_at
- `vote_discussion_replies`（讨论回复表）：reply_id, discussion_id, player_id, content, like_count, status, created_at, updated_at
- `vote_discussion_likes`（点赞记录表）：like_id, discussion_id, reply_id, player_id, created_at

包含完整约束：
- CHECK 约束：content 长度 1-500 字，status 合法值（active/hidden/deleted）
- 外键约束：vote_cycle_id → vote_cycles.vote_cycle_id（RESTRICT），discussion_id → vote_discussions.discussion_id（CASCADE）
- 索引：按周期+时间排序、按周期+热度排序、回复按讨论+时间排序、点赞唯一索引

### 2. Repository 层实现（完成）
在 `services/vote/app/repositories/discussion_repo.py` 中实现 DiscussionRepository：
- `list_discussions()` - 讨论列表（支持按时间/热度排序、分页）
- `get_discussion()` - 讨论详情
- `create_discussion()` - 发布讨论
- `delete_discussion()` - 删除讨论（软删除，status=deleted）
- `like_discussion()` - 点赞讨论（幂等）
- `unlike_discussion()` - 取消点赞
- `has_liked_discussion()` - 检查是否已点赞讨论
- `list_replies()` - 回复列表（分页）
- `get_reply()` - 回复详情
- `create_reply()` - 发布回复
- `delete_reply()` - 删除回复（软删除）
- `like_reply()` - 点赞回复（幂等）
- `has_liked_reply()` - 检查是否已点赞回复

### 3. Schemas 层（完成）
在 `services/vote/app/schemas/vote.py` 中新增：
- `VoteDiscussionResponse` - 讨论响应（含是否已点赞标记）
- `VoteDiscussionReplyResponse` - 回复响应（含是否已点赞标记）
- `CreateDiscussionRequest` - 发布讨论请求（content 1-500字校验）
- `CreateReplyRequest` - 发布回复请求（content 1-500字校验）
- `LikeResponse` - 点赞响应（liked 状态）

### 4. API 路由层（完成）
在 `services/vote/app/api/routes.py` 中新增 10 个端点：

玩家接口：
- `GET /api/v1/votes/discussions/{vote_cycle_id}` - 获取讨论列表（votes:discussions:read）
- `POST /api/v1/votes/discussions/{vote_cycle_id}` - 发布讨论（votes:discussions:write）
- `POST /api/v1/votes/discussions/{discussion_id}/like` - 点赞讨论（votes:discussions:write）
- `DELETE /api/v1/votes/discussions/{discussion_id}/like` - 取消点赞（votes:discussions:write）
- `DELETE /api/v1/votes/discussions/{discussion_id}` - 删除自己的讨论（votes:discussions:write）
- `GET /api/v1/votes/discussions/{discussion_id}/replies` - 获取回复列表（votes:discussions:read）
- `POST /api/v1/votes/discussions/{discussion_id}/replies` - 发布回复（votes:discussions:write）
- `POST /api/v1/votes/replies/{reply_id}/like` - 点赞回复（votes:discussions:write）
- `DELETE /api/v1/votes/replies/{reply_id}` - 删除自己的回复（votes:discussions:write）

运营接口：
- `DELETE /api/v1/ops/discussions/{discussion_id}/hide` - 隐藏讨论（ops:discussions:moderate）
- `DELETE /api/v1/ops/replies/{reply_id}/hide` - 隐藏回复（ops:discussions:moderate）

### 5. 认证与授权（完成）
- 新增 3 个 Scope：`votes:discussions:read`、`votes:discussions:write`、`ops:discussions:moderate`
- 角色权限配置：player 有 votes:discussions:read/write，ops 有全部 scope，reviewer 有 ops:discussions:moderate，system 有全部
- 新增依赖注入快捷方式：RequireDiscussionsReadScope、RequireDiscussionsWriteScope、RequireDiscussionsModerateScope

### 6. 错误码（完成）
在 `services/vote/app/core/errors.py` 新增 6 个错误码：
- `DISCUSSION_NOT_FOUND` - 讨论不存在
- `REPLY_NOT_FOUND` - 回复不存在
- `DISCUSSION_NOT_ACTIVE` - 讨论不可用（已删除/隐藏）
- `REPLY_NOT_ACTIVE` - 回复不可用
- `CANNOT_DELETE_OTHER_DISCUSSION` - 不能删除他人的讨论
- `CANNOT_DELETE_OTHER_REPLY` - 不能删除他人的回复

### 7. 审计日志（完成）
新增 4 个审计动作常量：
- `ACTION_DISCUSSION_CREATE` - 创建讨论
- `ACTION_DISCUSSION_DELETE` - 删除讨论
- `ACTION_REPLY_CREATE` - 创建回复
- `ACTION_REPLY_DELETE` - 删除回复

### 8. 业务指标（完成）
新增 4 类 Prometheus 指标：
- `vote_discussion_created_total` - 讨论发布数
- `vote_discussion_liked_total` - 讨论点赞数
- `vote_reply_created_total` - 回复发布数
- `vote_reply_liked_total` - 回复点赞数

### 9. 测试用例（完成）
新增 24 个测试用例（`services/vote/tests/test_discussions.py）：
- 讨论列表查询（成功、按时间排序、按热度排序、分页、周期不存在、无token）
- 发布讨论（成功、内容过长、周期不存在、无token）
- 点赞讨论（成功、重复点赞、讨论不存在）
- 取消点赞（成功、未点赞时取消）
- 删除讨论（删除自己的、删除他人的-禁止、讨论不存在）
- 回复功能（创建回复、回复列表、讨论不存在、点赞回复、删除自己的回复、删除他人的-禁止）

## 修改的文件清单

### 后端服务（vote-service）
- `services/vote/app/domain/models.py` - 新增 3 个数据模型（VoteDiscussion、VoteDiscussionReply、VoteDiscussionLike）
- `services/vote/app/repositories/discussion_repo.py` - 新增讨论区仓储层（新文件）
- `services/vote/app/schemas/vote.py` - 新增讨论区相关 schema
- `services/vote/app/schemas/auth.py` - 新增讨论区相关 Scope 和角色权限
- `services/vote/app/api/routes.py` - 新增讨论区 API 路由
- `services/vote/app/core/errors.py` - 新增错误码
- `services/vote/app/core/metrics.py` - 新增业务指标
- `services/vote/app/core/deps.py` - 新增依赖注入快捷方式
- `services/vote/tests/test_discussions.py` - 新增测试用例（新文件）

### 文档
- `docs/00-governance/project-status.md` - 更新当前阶段记录
- `docs/40-dev-loop/auto-plan-20260713-1800.md` - 本计划文档
- `docs/40-dev-loop/auto-execution-summary-20260713-1800.md` - 本执行摘要

## 测试结果

- vote-service 测试：80 个通过（原 56 + 新增 24）
- ruff 检查：通过
- mypy 检查：通过
- 无回归问题

## 遗留问题与下一步建议

### 本轮未完成项（留待后续轮次）
1. **Alembic 迁移脚本生成
2. **Godot 客户端 VoteManager 扩展
3. **讨论区 UI 面板实现
4. **投票界面集成讨论区入口
5. **客户端 GUT 测试补全

### 下一步建议
1. 下一轮可以继续推进 S4-02 的客户端部分，完成 VoteManager 扩展和讨论区 UI 面板实现
2. 生成 Alembic 迁移脚本，确保数据库 schema 可部署
3. 完善运营端隐藏讨论区管理功能（查看、审核、置顶等）
4. 考虑添加讨论区的热门排序算法优化（热度 = 点赞数 + 回复数 * 2 - 时间衰减）

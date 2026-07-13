# 执行摘要：S5-03 公会系统基础

> 任务标识：auto-20260714-1100
> 执行时间：2026-07-14 11:00 ~ 11:30
> 工作分支：auto/auto-20260714-1100

## 完成的工作清单

### 1. 数据模型层
- ✅ 新增 `Guild` 模型（guilds 表）
  - guild_id（UUID 主键）
  - name（VARCHAR(64)，唯一索引）
  - leader_id（UUID，会长玩家ID）
  - description/announcement（TEXT，可选）
  - level/member_count/max_members（INTEGER）
  - created_at/updated_at（审计字段）
  - CHECK 约束（名称长度、等级、成员数）

- ✅ 新增 `GuildMember` 模型（guild_members 表）
  - guild_member_id（UUID 主键）
  - guild_id/player_id（UUID）
  - role（VARCHAR(16)，枚举：leader/officer/member）
  - joined_at（加入时间）
  - player_id 唯一约束（一个玩家只能加入一个公会）

### 2. 仓储层
- ✅ 新增 `GuildRepository` 仓储层，实现 12 个方法：
  - create_guild（创建公会，同时创建会长成员记录）
  - get_guild_by_id/get_guild_by_name/get_guild_by_player（查询）
  - update_guild/delete_guild（更新/解散）
  - add_member/remove_member（成员管理）
  - transfer_leader（转让会长）
  - set_member_role（设置成员角色）
  - get_members/get_member_count（成员列表与计数）
  - is_guild_leader/is_guild_officer/is_guild_member（权限检查）

### 3. API 层
- ✅ 新增 10 个 API 端点：
  - POST /player/guilds（创建公会）
  - GET /player/guilds/my（获取我的公会）
  - GET /player/guilds/{id}（公会详情）
  - PUT /player/guilds/{id}（更新公会）
  - DELETE /player/guilds/{id}（解散公会）
  - POST /player/guilds/{id}/members（邀请成员）
  - DELETE /player/guilds/{id}/members/{pid}（移除成员）
  - POST /player/guilds/{id}/leave（退出公会）
  - POST /player/guilds/{id}/transfer（转让会长）
  - GET /player/guilds/{id}/members（成员列表）

- ✅ 新增 9 个错误码：
  - GUILD_NAME_EXISTS、GUILD_NOT_FOUND
  - ALREADY_IN_GUILD、NOT_IN_GUILD
  - NOT_GUILD_LEADER、NOT_GUILD_OFFICER
  - CANNOT_REMOVE_LEADER、GUILD_FULL
  - CANNOT_LEAVE_AS_LEADER

- ✅ 新增 2 个 Scope：guild:read、guild:write
- ✅ 新增 3 类业务指标：guilds_created_total、guild_members_added_total、guild_members_removed_total
- ✅ 新增 6 个审计动作常量

### 4. 数据库迁移
- ✅ 新增 Alembic 迁移脚本 `2026_07_14_1100_add_guild_tables.py`

### 5. 测试覆盖
- ✅ 新增 19 个测试用例（test_guild_api.py）
  - 创建公会（成功、名称重复、已加入公会）
  - 获取公会（我的公会、详情、不存在）
  - 更新公会（成功、非会长）
  - 邀请成员（成功、已在公会）
  - 移除成员（成功、不能移除会长）
  - 退出公会（成功、会长不能退出）
  - 转让会长（成功、非会长）
  - 解散公会
  - 获取成员列表

## 修改的文件清单

| 文件 | 变更类型 |
|------|----------|
| services/player/app/domain/models.py | 修改（新增 Guild、GuildMember 模型）|
| services/player/app/repositories/guild_repo.py | 新建 |
| services/player/app/api/routes.py | 修改（新增公会 API）|
| services/player/app/schemas/player.py | 修改（新增公会 Schema）|
| services/player/app/schemas/auth.py | 修改（新增 Scope）|
| services/player/app/core/errors.py | 修改（新增错误码）|
| services/player/app/core/metrics.py | 修改（新增指标）|
| services/player/app/core/deps.py | 修改（新增 Scope 依赖）|
| services/player/app/repositories/audit_repo.py | 修改（新增审计常量）|
| services/player/alembic/versions/2026_07_14_1100_add_guild_tables.py | 新建 |
| services/player/tests/test_guild_api.py | 新建 |
| docs/40-dev-loop/auto-plan-20260714-1100.md | 新建 |
| docs/00-governance/project-status.md | 修改 |

## 测试结果

- player-service 测试：162 个通过（+19）
- ruff 检查：通过
- mypy 检查：通过

## 遗留问题与下一步建议

### 遗留问题
- 无

### 下一步建议
- S5-04 公会聊天（P1）：基于公会系统实现公会内聊天功能
- 客户端 GuildManager 和 GuildPanel（P2）：实现公会管理的客户端 UI
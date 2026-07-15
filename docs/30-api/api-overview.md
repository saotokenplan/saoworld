# API 总览

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本文档用于把 `docs/20-specs/backend-data-spec.md` 中分散的接口方向整理成一份实施索引，作为 `docs/30-api/` 目录的导航入口。

## 适用范围

- 适用于 `docs/30-api/` 目录下的接口参考导航和总览说明。
- 适用于梳理当前 API 域、服务边界、接口清单和后续补充方向时的统一入口。
- 不替代 `docs/20-specs/` 中的执行规范，也不替代具体接口样例、权限矩阵和错误码细表。

## 当前定位

- 本文档是接口总览，不替代详细规范。
- 服务边界、数据模型、异步任务、事件流和安全要求以 `docs/20-specs/backend-data-spec.md` 为准。
- 如果本文件与 `docs/20-specs/backend-data-spec.md` 冲突，以后者为准。

## 通用约定

- 协议：`HTTPS + JSON`
- 认证：OIDC 签发的 JWT Bearer Token（`Authorization: Bearer <token>`）
- 版本前缀：`/api/v1`
- 时间格式：ISO 8601
- 错误返回统一结构（详见 [api-error-codes.md](file:///workspace/docs/30-api/api-error-codes.md) 和 OpenAPI Schema）：

```json
{
  "code": "INVALID_VOTE_STATE",
  "message": "当前投票周期不可投票",
  "request_id": "req_vote_current_409",
  "details": [
    {
      "location": "body",
      "field": "candidate_id",
      "issue": "required"
    }
  ]
}
```

## 角色与权限

### `player`

- 面向普通玩家
- 可访问世界、任务、投票和内容更新查询接口

### `ops`

- 面向运营和配置角色
- 可创建投票周期、发布内容包、触发回滚

### `reviewer`

- 面向审核角色
- 可批准或处理审核流中的内容对象

### `system`

- 面向 Agent、任务队列和自动化流程
- 主要处理内部任务、事件和审计链路

## 服务边界速览

| 服务 | 主要职责 | 是否直接对客户端开放 |
|---|---|---|
| `gateway-service` | 统一入口、鉴权、限流、会话上下文 | 是 |
| `player-service` | 账号、角色、成长、声望、章节进度 | 是 |
| `world-service` | 区域状态、阵营状态、地图与任务可见性 | 是 |
| `vote-service` | 候选池、投票资格、投票记录、结算 | 是 |
| `generation-service` | 生成请求组织、模板加载、生成结果落库 | 否 |
| `review-service` | 结构化校验、风险判断、人工复核流转 | 否 |
| `content-service` | 内容包、灰度投放、版本归档、回滚 | 部分 |
| `ops-service` | 运营后台入口、指标汇总、Issue 触发 | 否 |

## 完整接口清单（176 个端点）

> 以下清单基于代码实际实现审计，按服务分组。所有端点均需 `Authorization: Bearer <token>` 认证（除健康检查外）。

### vote-service（27 个端点）

#### 玩家接口

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| GET | `/api/v1/votes/current` | `votes:read` | 获取当前投票周期与候选项 |
| GET | `/api/v1/votes/current/progress` | `votes:read` | 获取当前投票进度 |
| POST | `/api/v1/votes/submit` | `votes:submit` | 提交投票 |
| GET | `/api/v1/votes/history` | `votes:history:read` | 获取历史投票记录 |
| GET | `/api/v1/votes/history/{vote_cycle_id}/chart-data` | `votes:history:read` | 获取投票结果图表数据 |
| GET | `/api/v1/votes/history/{vote_cycle_id}/review` | `votes:history:read` | 获取投票复盘报告 |
| GET | `/api/v1/votes/discussions/{vote_cycle_id}` | `votes:discussions:read` | 列出投票讨论 |
| POST | `/api/v1/votes/discussions/{vote_cycle_id}` | `votes:discussions:write` | 创建讨论 |
| POST | `/api/v1/votes/discussions/{discussion_id}/like` | `votes:discussions:write` | 点赞讨论 |
| POST | `/api/v1/votes/discussions/{discussion_id}/unlike` | `votes:discussions:write` | 取消点赞讨论 |
| DELETE | `/api/v1/votes/discussions/{discussion_id}` | `votes:discussions:write` | 删除讨论 |
| GET | `/api/v1/votes/discussions/{discussion_id}/replies` | `votes:discussions:read` | 列出讨论回复 |
| POST | `/api/v1/votes/discussions/{discussion_id}/replies` | `votes:discussions:write` | 创建回复 |
| POST | `/api/v1/votes/replies/{reply_id}/like` | `votes:discussions:write` | 点赞回复 |
| POST | `/api/v1/votes/replies/{reply_id}/unlike` | `votes:discussions:write` | 取消点赞回复 |
| DELETE | `/api/v1/votes/replies/{reply_id}` | `votes:discussions:write` | 删除回复 |

#### 运营接口

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| POST | `/api/v1/ops/vote-cycles` | `ops:vote-cycles:write` | 创建投票周期 |
| POST | `/api/v1/ops/vote-cycles/{id}/schedule` | `ops:vote-cycles:write` | 调度投票周期（draft→scheduled） |
| POST | `/api/v1/ops/vote-cycles/{id}/open` | `ops:vote-cycles:write` | 开启投票周期（scheduled→open） |
| POST | `/api/v1/ops/vote-cycles/{id}/close` | `ops:vote-cycles:write` | 关闭投票周期（open→closed） |
| POST | `/api/v1/ops/vote-cycles/{id}/finalize` | `ops:vote-cycles:write` | 确认投票周期（closed→finalized） |
| GET | `/api/v1/ops/anomalies` | `ops` | 列出异常记录 |
| GET | `/api/v1/ops/anomalies/stats` | `ops` | 获取异常统计 |
| GET | `/api/v1/ops/anomalies/{anomaly_id}` | `ops` | 获取异常详情 |
| PATCH | `/api/v1/ops/anomalies/{anomaly_id}/resolve` | `ops` | 标记异常已解决 |
| PATCH | `/api/v1/ops/anomalies/{anomaly_id}/false-positive` | `ops` | 标记异常误报 |

### world-service（26 个端点）

#### 玩家接口

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| GET | `/api/v1/world/regions` | `world:read` | 获取可见区域列表 |
| GET | `/api/v1/world/regions/{region_id}` | `world:read` | 获取区域详情 |
| GET | `/api/v1/world/skeleton` | `world:read` | 获取当前世界骨架快照 |
| GET | `/api/v1/world/npcs` | `world:read` | 获取 NPC 列表 |
| GET | `/api/v1/world/npcs/{npc_id}` | `world:read` | 获取 NPC 详情（by UUID） |
| GET | `/api/v1/world/npcs/by-key/{npc_key}` | `world:read` | 获取 NPC 详情（by key） |
| GET | `/api/v1/world/quests` | `world:read` | 获取任务列表 |
| GET | `/api/v1/world/quests/{quest_id}` | `world:read` | 获取任务详情（by UUID） |
| GET | `/api/v1/world/quests/by-key/{quest_key}` | `world:read` | 获取任务详情（by key） |
| GET | `/api/v1/world/items` | `items:read` | 获取物品列表 |
| GET | `/api/v1/world/items/{item_key}` | `items:read` | 获取物品详情 |
| GET | `/api/v1/world/monsters` | `world:read` | 获取怪物定义列表 |
| GET | `/api/v1/world/monsters/{monster_id}` | `world:read` | 获取怪物详情 |
| GET | `/api/v1/world/bosses` | `world:read` | 获取区域 Boss 列表 |
| GET | `/api/v1/world/bosses/{monster_key}` | `world:read` | 获取 Boss 详情 |

#### 运营接口

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| POST | `/api/v1/ops/world/regions` | `ops` | 创建区域 |
| POST | `/api/v1/ops/world/regions/{region_id}/status` | `ops` | 更新区域状态 |
| POST | `/api/v1/ops/world/skeleton` | `ops` | 创建世界骨架快照 |
| POST | `/api/v1/ops/world/npcs` | `ops` | 创建 NPC |
| POST | `/api/v1/ops/world/quests` | `ops` | 创建任务 |
| POST | `/api/v1/ops/world/items` | `ops` | 创建物品 |
| PUT | `/api/v1/ops/world/items/{item_id}` | `ops` | 更新物品 |
| DELETE | `/api/v1/ops/world/items/{item_id}` | `ops` | 删除物品 |
| POST | `/api/v1/ops/world/monsters` | `ops` | 创建怪物定义 |
| POST | `/api/v1/ops/world/monsters/bosses` | `ops` | 创建 Boss 定义 |

### content-service（7 个端点）

#### 玩家接口

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| GET | `/api/v1/content/updates` | `content:read` | 获取玩家可见内容更新列表 |
| GET | `/api/v1/content/packages/{package_id}` | `content:read` | 获取内容包详情 |
| GET | `/api/v1/content/packages/by-vote-cycle/{vote_cycle_id}` | `content:read` | 按投票周期获取内容包 |

#### 运营接口

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| POST | `/api/v1/ops/content-packages` | `content:release` | 创建内容包 |
| POST | `/api/v1/ops/content-packages/{package_id}/release` | `content:release` | 发布内容包（灰度/全量） |
| POST | `/api/v1/ops/content-packages/{package_id}/rollback` | `content:rollback` | 回滚内容包 |
| GET | `/api/v1/health` | 公开 | 健康检查 |

### generation-service（10 个端点）

#### 运营接口

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| GET | `/api/v1/ops/generation/requests` | `ops` | 列出生成请求 |
| GET | `/api/v1/ops/generation/requests/{request_id}` | `ops` | 获取生成请求详情 |
| POST | `/api/v1/ops/generation/requests` | `ops` | 创建生成请求 |
| POST | `/api/v1/ops/generation/requests/{request_id}/status` | `ops` | 更新生成请求状态 |
| GET | `/api/v1/ops/generation/objects` | `ops` | 列出生成对象 |
| GET | `/api/v1/ops/generation/objects/{object_id}` | `ops` | 获取生成对象详情 |
| POST | `/api/v1/ops/generation/objects/{object_id}/status` | `review:approve` | 更新生成对象状态（审核） |
| POST | `/api/v1/ops/generation/requests/{request_id}/objects` | `ops` | 创建生成对象 |
| GET | `/api/v1/ops/generation/cost` | `ops` | 获取生成成本统计 |
| GET | `/api/v1/health` | 公开 | 健康检查 |

### review-service（7 个端点）

#### 运营接口

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| GET | `/api/v1/ops/review/records` | `ops` | 列出审核记录 |
| GET | `/api/v1/ops/review/records/{review_id}` | `ops` | 获取审核记录详情 |
| POST | `/api/v1/ops/review/records` | `ops` | 创建审核记录 |
| POST | `/api/v1/ops/review/records/{review_id}/result` | `review:approve` | 更新审核结果 |
| POST | `/api/v1/ops/review/{object_id}/approve` | `review:approve` | 批准内容对象 |
| POST | `/api/v1/ops/review/{object_id}/reject` | `review:approve` | 拒绝内容对象 |
| GET | `/api/v1/health` | 公开 | 健康检查 |

### player-service（53 个端点）

#### 玩家接口 — 基础

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| GET | `/api/v1/player/info` | player | 获取玩家基本信息 |
| GET | `/api/v1/player/profile` | player | 获取玩家档案（聚合） |
| GET | `/api/v1/player/level` | player | 获取玩家等级 |
| GET | `/api/v1/player/contribution` | `contribution:read` | 获取贡献度 |

#### 玩家接口 — 任务

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| GET | `/api/v1/player/quests` | `quests:read` | 获取玩家任务列表 |
| GET | `/api/v1/player/quests/{quest_id}` | `quests:read` | 获取玩家任务详情 |
| POST | `/api/v1/player/quests/{quest_id}/accept` | `quests:write` | 接受任务 |
| POST | `/api/v1/player/quests/{quest_id}/progress` | `quests:write` | 更新任务进度 |
| POST | `/api/v1/player/quests/{quest_id}/complete` | `quests:write` | 完成任务 |
| POST | `/api/v1/player/quests/{quest_id}/fail` | `quests:write` | 失败任务 |

#### 玩家接口 — 区域与声望

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| GET | `/api/v1/player/regions` | player | 获取玩家区域列表 |
| GET | `/api/v1/player/reputation/{region_id}` | player | 获取指定区域声望 |
| GET | `/api/v1/player/reputation` | player | 获取全部声望 |

#### 玩家接口 — 背包

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| GET | `/api/v1/player/inventory` | player | 获取玩家背包 |
| POST | `/api/v1/player/inventory/use` | player | 使用物品 |

#### 玩家接口 — 装备

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| GET | `/api/v1/player/equipment` | player | 获取装备信息 |
| GET | `/api/v1/player/equipment/stats` | player | 获取装备属性统计 |
| POST | `/api/v1/player/equipment/equip` | player | 装备物品 |
| POST | `/api/v1/player/equipment/unequip` | player | 卸下装备 |

#### 玩家接口 — 成就

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| GET | `/api/v1/player/achievements` | `achievements:read` | 列出成就定义 |
| GET | `/api/v1/player/achievements/{achievement_key}` | `achievements:read` | 获取成就定义详情 |
| GET | `/api/v1/player/me/achievements` | `achievements:read` | 列出我的成就 |
| POST | `/api/v1/player/me/achievements/{achievement_key}/claim` | `achievements:unlock` | 领取成就奖励 |

#### 玩家接口 — 好友

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| POST | `/api/v1/player/friends/request` | `friends:write` | 发送好友请求 |
| POST | `/api/v1/player/friends/accept` | `friends:write` | 接受好友请求 |
| POST | `/api/v1/player/friends/reject` | `friends:write` | 拒绝好友请求 |
| DELETE | `/api/v1/player/friends/{friend_id}` | `friends:write` | 删除好友 |
| GET | `/api/v1/player/friends` | `friends:read` | 获取好友列表 |
| GET | `/api/v1/player/friends/requests` | `friends:read` | 获取好友请求列表 |
| GET | `/api/v1/player/friends/{friend_id}/status` | `friends:read` | 获取好友状态 |

#### 玩家接口 — 私信

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| POST | `/api/v1/player/messages` | `messages:write` | 发送私信 |
| GET | `/api/v1/player/messages/conversations` | `messages:read` | 获取会话列表 |
| GET | `/api/v1/player/messages/conversations/{friend_id}` | `messages:read` | 获取会话消息 |
| POST | `/api/v1/player/messages/{message_id}/read` | `messages:write` | 标记消息已读 |
| GET | `/api/v1/player/messages/unread` | `messages:read` | 获取未读消息 |
| GET | `/api/v1/player/messages/unread/count` | `messages:read` | 获取未读消息数 |

#### 玩家接口 — 公会

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| POST | `/api/v1/player/guilds` | `guild:write` | 创建公会 |
| GET | `/api/v1/player/guilds/my` | `guild:read` | 获取我的公会 |
| GET | `/api/v1/player/guilds/{guild_id}` | `guild:read` | 获取公会详情 |
| PUT | `/api/v1/player/guilds/{guild_id}` | `guild:write` | 更新公会信息 |
| DELETE | `/api/v1/player/guilds/{guild_id}` | `guild:write` | 解散公会 |
| POST | `/api/v1/player/guilds/{guild_id}/members` | `guild:write` | 邀请公会成员 |
| DELETE | `/api/v1/player/guilds/{guild_id}/members/{player_id}` | `guild:write` | 移除公会成员 |
| POST | `/api/v1/player/guilds/{guild_id}/leave` | `guild:write` | 离开公会 |
| POST | `/api/v1/player/guilds/{guild_id}/transfer` | `guild:write` | 转让会长 |
| GET | `/api/v1/player/guilds/{guild_id}/members` | `guild:read` | 获取公会成员列表 |

#### 玩家接口 — 公会聊天

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| POST | `/api/v1/player/guilds/{guild_id}/messages` | `guild:write` | 发送公会消息 |
| GET | `/api/v1/player/guilds/{guild_id}/messages` | `guild:read` | 获取公会消息 |
| POST | `/api/v1/player/guilds/{guild_id}/messages/read` | `guild:write` | 标记公会消息已读 |
| GET | `/api/v1/player/guilds/{guild_id}/messages/unread-count` | `guild:read` | 获取未读公会消息数 |
| DELETE | `/api/v1/player/guilds/{guild_id}/messages/{message_id}` | `guild:write` | 删除公会消息 |

#### 玩家接口 — 社交概览

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| GET | `/api/v1/player/social/overview` | `social:read` | 获取社交概览 |

#### 运营接口

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| POST | `/api/v1/ops/players` | `ops` | 创建玩家 |
| GET | `/api/v1/ops/players` | `ops` | 列出玩家 |
| GET | `/api/v1/ops/players/{player_id}` | `ops` | 获取玩家详情 |
| PUT | `/api/v1/ops/players/{player_id}` | `ops` | 更新玩家 |
| POST | `/api/v1/ops/players/{player_id}/regions/{region_id}/unlock` | `ops` | 解锁区域 |
| GET | `/api/v1/ops/players/{player_id}/quests` | `ops` | 获取玩家任务 |
| POST | `/api/v1/ops/players/{player_id}/quests` | `ops` | 创建玩家任务 |
| PATCH | `/api/v1/ops/players/{player_id}/quests/{quest_id}/status` | `ops` | 更新任务状态 |
| POST | `/api/v1/ops/players/{player_id}/inventory` | `ops` | 添加背包物品 |
| DELETE | `/api/v1/ops/players/{player_id}/inventory/{item_key}` | `ops` | 移除背包物品 |
| POST | `/api/v1/ops/players/{player_id}/reputation/{region_id}/adjust` | `ops` | 调整声望 |
| POST | `/api/v1/ops/players/{player_id}/experience` | `ops` | 增加经验 |
| POST | `/api/v1/ops/players/{player_id}/contribution` | `ops` | 增加贡献度 |
| POST | `/api/v1/ops/achievements` | `ops` | 创建成就定义 |
| POST | `/api/v1/ops/players/{player_id}/achievements/{achievement_key}/unlock` | `ops` | 解锁成就 |

### ops-service（42 个端点）

#### 运营接口 — 仪表盘与分析

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| GET | `/api/v1/ops/dashboard` | `ops` | 获取运营仪表盘 |
| GET | `/api/v1/ops/dashboard/history` | `ops` | 获取仪表盘历史 |
| GET | `/api/v1/ops/actions` | `ops` | 获取运营操作记录列表 |
| GET | `/api/v1/ops/actions/{action_id}` | `ops` | 获取运营操作详情 |
| GET | `/api/v1/ops/system/status` | `ops` | 获取系统状态 |

#### 运营接口 — 数据分析

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| GET | `/api/v1/ops/analytics/player-metrics` | `ops` | 获取玩家指标 |
| GET | `/api/v1/ops/analytics/region-metrics` | `ops` | 获取区域指标 |
| GET | `/api/v1/ops/analytics/trends` | `ops` | 获取趋势数据 |
| GET | `/api/v1/ops/analytics/reports` | `ops` | 获取分析报告列表 |
| GET | `/api/v1/ops/analytics/dashboard/overview` | `ops` | 获取分析总览 |
| GET | `/api/v1/ops/analytics/dashboard/regions` | `ops` | 获取区域分析 |
| GET | `/api/v1/ops/analytics/dashboard/quests` | `ops` | 获取任务分析 |
| GET | `/api/v1/ops/analytics/dashboard/votes` | `ops` | 获取投票分析 |

#### 运营接口 — 洞察与需求

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| GET | `/api/v1/insights` | `ops` | 获取洞察列表 |
| GET | `/api/v1/insights/{insight_id}` | `ops` | 获取洞察详情 |
| POST | `/api/v1/ops/insights/{insight_id}/generate-requirement` | `ops` | 从洞察生成需求 |
| GET | `/api/v1/ops/requirements` | `ops` | 获取需求列表 |
| GET | `/api/v1/ops/requirements/{requirement_id}` | `ops` | 获取需求详情 |
| POST | `/api/v1/ops/requirements/{requirement_id}/approve` | `ops` | 批准需求 |

#### 运营接口 — 投票管理代理

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| POST | `/api/v1/ops/vote-cycles` | `ops` | 创建投票周期（代理） |
| POST | `/api/v1/ops/vote-cycles/{id}/schedule` | `ops` | 调度投票周期（代理） |
| POST | `/api/v1/ops/vote-cycles/{id}/open` | `ops` | 开启投票周期（代理） |
| POST | `/api/v1/ops/vote-cycles/{id}/close` | `ops` | 关闭投票周期（代理） |
| POST | `/api/v1/ops/vote-cycles/{id}/finalize` | `ops` | 确认投票周期（代理） |
| GET | `/api/v1/ops/vote-cycles` | `ops` | 列出投票周期（代理） |
| GET | `/api/v1/ops/vote-cycles/{vote_cycle_id}` | `ops` | 获取投票周期详情（代理） |

#### 运营接口 — 内容管理代理

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| POST | `/api/v1/ops/content-packages/{id}/release` | `ops` | 发布内容包（代理） |
| POST | `/api/v1/ops/content-packages/{id}/rollback` | `ops` | 回滚内容包（代理） |
| GET | `/api/v1/ops/content-packages` | `ops` | 列出内容包（代理） |
| GET | `/api/v1/ops/content-packages/{content_package_id}` | `ops` | 获取内容包详情（代理） |

#### 运营接口 — 审核工作流代理

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| POST | `/api/v1/ops/review/{object_id}/approve` | `ops` | 批准审核对象（代理） |
| POST | `/api/v1/ops/review/{object_id}/reject` | `ops` | 拒绝审核对象（代理） |
| GET | `/api/v1/ops/review/objects` | `ops` | 列出审核对象（代理） |
| GET | `/api/v1/ops/review/stats` | `ops` | 获取审核统计（代理） |

#### 运营接口 — 运营事件

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| POST | `/api/v1/ops/events` | `ops` | 创建运营事件 |
| GET | `/api/v1/ops/events` | `ops` | 列出运营事件 |
| GET | `/api/v1/ops/events/active` | `ops` | 获取活跃运营事件 |
| GET | `/api/v1/ops/events/{event_id}` | `ops` | 获取运营事件详情 |
| PUT | `/api/v1/ops/events/{event_id}` | `ops` | 更新运营事件 |
| POST | `/api/v1/ops/events/{event_id}/activate` | `ops` | 激活运营事件 |
| POST | `/api/v1/ops/events/{event_id}/pause` | `ops` | 暂停运营事件 |
| POST | `/api/v1/ops/events/{event_id}/end` | `ops` | 结束运营事件 |
| DELETE | `/api/v1/ops/events/{event_id}` | `ops` | 删除运营事件 |

#### 玩家接口

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| GET | `/api/v1/player/events/active` | `events:read` | 获取玩家可见活跃事件 |

### gateway-service（4 个端点）

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| GET | `/api/v1/health` | 公开 | 网关健康检查 |
| GET | `/api/v1/health/services` | 公开 | 全服务健康检查 |
| POST | `/api/v1/events/batch` | — | 批量提交玩家事件 |
| * | `/{full_path:path}` | — | 全路径反向代理 |

## 请求与响应样例

详细的请求响应样例已在以下文档中定义，并已同步到 OpenAPI 草案的 `components/examples`：

- 投票链路：`docs/30-api/api-examples-vote.md`
- 内容查询/发布/回滚：`docs/30-api/api-examples-content.md`
- 世界/任务/运营审核：`docs/30-api/api-examples-world-ops.md`
- 玩家接口：`docs/30-api/api-examples-player.md`
- 审核接口：`docs/30-api/api-examples-review.md`
- 生成接口：`docs/30-api/api-examples-generation.md`
- 运营接口：`docs/30-api/api-examples-ops.md`
- 网关接口：`docs/30-api/api-examples-gateway.md`

## 关键状态关系

### 投票链路

`vote_cycle -> candidate -> vote -> finalized_result`

### 内容链路

`generation_request -> generated_object -> review_record -> content_package -> release_or_rollback`

### 生命周期对齐

- 内容对象状态参考 `docs/20-specs/content-generation-spec.md`：
  - `draft -> validated -> reviewed -> packaged -> gray -> live -> archived`
- 发布接口只能操作已满足发布前置条件的对象或内容包。

## 异步任务索引

以下能力不应通过同步接口直接执行：

- `generate_content_batch`
- `run_world_consistency_review`
- `run_balance_review`
- `package_content_batch`
- `release_content_package`
- `rollback_content_package`
- `daily_gate_scan`

建议：

- 同步接口只负责接收请求、校验权限、生成 `request_id` 或 `task_id`
- 实际长任务交给队列系统处理
- 所有状态变更写入审计链

## 事件主题索引

建议内部事件总线至少包含：

- `vote.cycle.closed`
- `vote.result.finalized`
- `generation.request.created`
- `generation.batch.completed`
- `review.batch.completed`
- `content.package.released`
- `content.package.rolled_back`

每条事件至少包含：

- `event_id`
- `event_type`
- `occurred_at`
- `trace_id`
- `producer`
- `payload`

## 文档资产清单

`docs/30-api/` 目录当前包含以下接口参考文档：

| 文档 | 说明 |
|---|---|
| `api-overview.md`（本文档） | 接口总览、服务边界、接口清单 |
| `api-permissions.md` | 角色矩阵、scope 映射、审计要求 |
| `api-error-codes.md` | 错误码索引（已落地 vs 预留）、错误结构说明 |
| `api-examples-vote.md` | 投票链路请求响应样例 |
| `api-examples-content.md` | 内容查询、发布与回滚链路样例 |
| `api-examples-world-ops.md` | 世界、任务查询及运营写接口样例 |
| `api-examples-player.md` | 玩家信息、任务列表、区域状态及运营玩家管理接口样例 |
| `api-examples-review.md` | 审核记录查询、审核批准与拒绝接口样例 |
| `api-examples-generation.md` | 生成请求创建、查询及生成对象查询接口样例 |
| `api-examples-ops.md` | 运营仪表盘、运营操作记录、系统状态监控接口样例 |
| `api-examples-gateway.md` | 网关健康检查、服务状态监控接口样例 |
| `openapi-draft.md` | OpenAPI 草案入口、分批次阅读片段 |
| `openapi-v1-draft.yaml` | **权威**单文件 OpenAPI 3.1 草案（覆盖全部 8 个服务） |

## 需要后续补齐的内容

- 新增端点的字段级校验错误 details 样例
- 成功响应包装的复用层抽象
- 更完整的幂等策略说明（`Idempotency-Key` 冲突响应行为待细化）
- 按服务拆分 OpenAPI 子草案，降低单文件复杂度

## 与其他文档的关系

- `docs/20-specs/backend-data-spec.md`
  - 定义服务边界、数据模型和接口约束，是本文件的上游执行规范。
- `docs/30-api/api-permissions.md`
  - 补充接口角色边界、敏感操作约束和审计要求。
- `docs/30-api/api-error-codes.md`
  - 补充接口错误码、HTTP 状态码和异常语义。
- `docs/30-api/api-examples-vote.md`
  - 提供投票链路的请求响应样例，作为本总览中具体接口的下游细化文档。
- `docs/30-api/api-examples-content.md`
  - 提供内容查询、发布与回滚链路的请求响应样例，作为第二批接口的下游细化文档。
- `docs/30-api/api-examples-world-ops.md`
  - 提供世界查询、任务查询和第三批运营写接口的请求响应样例，作为第三批接口的下游细化文档。
- `docs/30-api/openapi-draft.md`
  - 作为本文件、权限矩阵、错误码和接口样例的后续汇总入口，并维护单文件草案的组织说明。
- `docs/30-api/openapi-v1-draft.yaml`
  - 当前首版单文件 OpenAPI 草案输出，供接口评审、实现对齐和后续工具链接入使用。

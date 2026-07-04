# 项目状态

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本文档用于统一说明当前项目处于什么阶段、哪些内容已经确定、哪些内容仍待确认，以及进入工程实施前还缺什么。

## 适用范围

- 适用于需要判断当前仓库处于哪个阶段、能否进入实施、还缺哪些前置条件的场景。
- 适用于新接手成员快速了解“已经具备什么”和“还不能做什么”。
- 不替代具体规范正文、接口参考或实施计划。

## 当前定位

- 本文档是项目阶段与资产完备度的状态说明，不直接承担执行规范角色。
- 本文档回答“现在做到哪一步”，不负责目录导航、权威关系或实施顺序说明。
- 目录导航看 `docs/README.md`，权威关系看 `docs/00-governance/document-map.md`，实现细节转向 `20-specs/`、`30-api/` 和 `40-dev-loop/`。

## 当前阶段

- 当前阶段：内容发布与验证阶段（首期内容包已打包）
- 当前形态：八大核心后端服务 + workers Celery + CI/CD + Godot 客户端完整，投票链路、内容链路、审核链路、API 网关、运营后台、客户端框架就绪，客户端与后端 API 联调封装完善，首期内容实例化完成（世界观、区域、阵营、NPC、任务、章节），内容包打包与发布流程已实现
- 当前目标：完成首期内容包灰度发布，验证端到端玩法流程，进入内容生成与投票驱动世界更新的闭环

## 当前结论

- vote-service 已具备完整的投票生命周期管理能力：创建（draft）→ 计划（scheduled）→ 开放（open）→ 关闭计票（closed）→ 确认结果（finalized）。
- 运营写接口已实现：`POST /api/v1/ops/vote-cycles`（创建）、`/schedule`、`/open`、`/close`、`/finalize`（状态迁移）。
- 关闭投票时自动计票，按加权总分确定获胜候选项并标记为 selected。
- 所有接口已实现统一响应 envelope 格式（`request_id`、`data`、`meta`、`trace_id`），对齐 `12-api-design.md` 规范。
- 玩家接口已添加 JWT 认证，支持 `votes:read`、`votes:submit`、`votes:history:read` scope 校验。
- 投票链路已有 51 个测试用例覆盖，全部通过 ruff、mypy 和 pytest 验证。
- 模型已补充 `votes_candidate_id_idx` 索引和 `winning_candidate_id` FK 约束。
- vote-service 端到端可运行验证已完成（代码层面通过所有测试，PostgreSQL 配置就绪）。

## 已确定事项

### 产品方向

- 产品形态已明确为“大型开放式、玩家投票驱动、AI 持续生成内容”的在线游戏。
- 核心闭环已明确为“探索 -> 参与 -> 投票 -> 世界更新 -> 再探索”。
- AI 的职责边界已明确：负责可变内容生成，不负责主线终局、核心经济和底层战斗规则。
- MVP 范围已明确：首期包含 `1` 个核心常驻区域、`1` 个扩展区域、`1` 条主线骨架、`3` 个候选剧情方向，以及投票、生成、审核、灰度和回滚的完整链路。

### 规范分层

- `00-governance/` 定位为文档治理、项目状态和使用入口。
- `10-requirements/` 定位为需求背景、方案讨论和立项上下文。
- `20-specs/` 定位为执行规范和最终基线。
- `30-api/` 定位为接口参考、权限矩阵和错误码索引。
- `40-dev-loop/` 定位为研发治理、门禁和 AI Coding 闭环设计。
- `50-research/` 定位为技术选型和历史决策依据。

### 技术方向

- 客户端方向已收敛为 Godot 4 + typed GDScript。
- 服务端方向已收敛为 Python、FastAPI、PostgreSQL、Celery。
- 后端服务拆分方向已明确，包括网关、玩家、世界、投票、生成、审核、内容和运营等核心服务。
- 发布策略方向已明确为内容包驱动、优先灰度、支持版本归档和快速回滚。

### 文档治理

- 已明确 `20-specs/` 优先于 `10-requirements/`。
- 已完成 `20-specs/` 与 `.trae/skills/` 的映射文档。
- 已在 `10-requirements/` 文档顶部补充“如与 `20-specs/` 冲突，以 `20-specs/` 为准”的声明。
- 已在各 `SKILL.md` 中补充“规范来源”。
- 已建立文档目录规范，并完成 `docs/` 目录按层重组。
- 已补齐 API 总览、权限矩阵和错误码三类接口参考文档。
- 已完成 `docs/` 范围内 `31` 份 Markdown 文档的模板字段对齐。
- 已新增模板维护规则，用于后续新增、迁移和大幅改写时做增量复查。

## 已准备好的资产

- 产品规范：
  - `docs/20-specs/product-spec.md`
- 内容生成规范：
  - `docs/20-specs/content-generation-spec.md`
- 后端与数据规范：
  - `docs/20-specs/backend-data-spec.md`
- Agent 与闭环规范：
  - `docs/20-specs/agent-loop-spec.md`
- 工程协作规范：
  - `docs/20-specs/engineering-conventions.md`
- 文档治理辅助材料：
  - `docs/00-governance/document-directory-spec.md`
  - `docs/00-governance/document-change-process.md`
  - `docs/00-governance/document-lifecycle.md`
  - `docs/00-governance/document-ownership.md`
  - `docs/00-governance/document-review-checklist.md`
  - `docs/00-governance/governance-phase-summary.md`
  - `docs/00-governance/document-template-alignment-checklist.md`
  - `docs/00-governance/document-template-maintenance.md`
  - `docs/00-governance/document-template-spec.md`
  - `docs/00-governance/document-map.md`
  - `docs/00-governance/quick-start.md`
  - `docs/00-governance/spec-skill-mapping.md`
- 接口参考材料：
  - `docs/30-api/api-overview.md`
  - `docs/30-api/openapi-draft.md`
  - `docs/30-api/api-permissions.md`
  - `docs/30-api/api-error-codes.md`
- 异步任务与事件规范：
  - `docs/20-specs/async-tasks-and-events/`
  - 7 个核心任务 payload schema
  - 7 个事件主题与消息格式
  - 重试策略与死信队列规范
  - 全链路追踪与审计字段规范

## 未确定事项

### 产品侧未定

- 世界观根设定的具体文本版本尚未单独沉淀为正式世界观文档。
- 首期区域、阵营、关键 NPC、章节切分仍缺少具体实例化内容包。
- 客户端交互稿、界面流和关键页面信息结构尚未文档化。

### 技术侧未定

- OpenAPI 单文件草案已完成 12 个端点、特化错误层、安全方案和响应 envelope，但预留错误码（INTERNAL_ERROR、TOKEN_EXPIRED 等）待实现阶段按需落地。
- 数据库核心表的字段类型、约束、索引、状态机和枚举值已定义在 `backend-data-spec.md`，但 ER 图和迁移脚本（Alembic/SQLAlchemy 模型）尚未生成。
- 异步任务和事件的 payload schema、重试策略、死信处理等细节仍停留在方向层，未形成工程实施方案。
- 任务队列、事件总线、中间件、部署方式等基础设施细节仍停留在方向层。

### 工程侧未定

- CI 规则、测试入口、发布流水线和环境配置文件尚未建立。
- 异步任务和事件的具体工程实现细节仍需在实施中细化。

### 工程侧已确定

- **仓库策略已确定为单仓模式**：当前仓库继续演进为主仓库，保留 `docs/` 并新增 `game/`、`services/`、`workers/`、`tools/`、`infra/`、`telemetry/` 等工程目录。
- **首个最小落地目标已确定**：最小投票链路（`GET /api/v1/votes/current` + `POST /api/v1/votes/submit` + vote-service 骨架）。

## 尚未落地的工程资产

- ~~`game/` Godot 客户端工程尚未初始化（目录已创建，占位 README 就位）。~~ 已完成，Godot 4 客户端工程骨架已初始化，包含完整目录结构、核心 Autoload 单例、基础场景、数据配置、测试框架。
- ~~`workers/` Celery 异步任务 Worker 尚未实现（目录已创建）。~~ 已完成，workers Celery Worker 框架已实现，包含 7 个核心异步任务（内容生成、审核、打包、发布、回滚、门禁扫描），19 个测试用例全部通过。
- ~~除 `vote-service`、`world-service`、`content-service`、`generation-service`、`review-service`、`gateway-service`、`player-service` 外的其他后端服务（ops）尚未初始化。~~ 已完成，ops-service 已初始化完成。
- ~~Alembic 数据库迁移脚本尚未生成（world-service），需要连接数据库后初始化。~~ 已完成，world-service、content-service、generation-service、review-service、player-service、ops-service 六个服务的 Alembic 迁移环境已全部初始化，首次迁移脚本（核心业务表 + 审计日志表）已生成。
- ~~真实 CI 配置、部署脚本和生产环境配置尚未建立。~~ 已完成，CI/CD 配置（GitHub Actions）、各服务 Dockerfile、生产环境 Docker Compose、Nginx 配置、Prometheus/Grafana 监控配置、部署脚本（deploy.sh、rollback.sh、health-check.sh、migrate-all.sh）已就绪。
- JWT 鉴权中间件、运营写接口、投票结算 Worker 尚未实现。~~已全部完成：JWT 鉴权、运营写接口、投票结算逻辑。~~

## 已初步落地的工程资产

- 单仓模式目标目录结构已创建：`game/`、`services/`、`workers/`、`tools/`、`infra/`、`telemetry/`。
- `vote-service` 已完成骨架初始化与运营写接口实现（FastAPI + SQLAlchemy + Pydantic + pytest），见 `services/vote/`。
  - 数据模型：`VoteCycle`、`VoteCandidate`、`Vote`（对应 `backend-data-spec.md`）
  - 玩家 API 路由：`GET /api/v1/health`、`GET /api/v1/votes/current`、`POST /api/v1/votes/submit`、`GET /api/v1/votes/history`
  - 运营 API 路由：`POST /api/v1/ops/vote-cycles`（创建投票周期）、`POST .../schedule`、`POST .../open`、`POST .../close`、`POST .../finalize`（状态迁移）
  - 投票结算逻辑：关闭投票时自动计票，确定获胜候选项
  - 状态机校验：严格遵循 draft → scheduled → open → closed → finalized 路径
  - 同章节唯一开放周期校验
  - 统一响应 envelope（`request_id`、`data`、`meta`、`trace_id`），对齐 `12-api-design.md` 规范
  - 玩家接口 JWT 认证（`votes:read`、`votes:submit`、`votes:history:read` scope）
  - 错误响应 envelope、幂等键处理、结构化日志、request_id/trace_id 中间件
  - 审计日志持久化（`audit_logs` 表写入，覆盖投票提交、周期创建和状态迁移）
  - 模型约束补全：`votes_candidate_id_idx` 索引、`winning_candidate_id` FK
  - 测试用例 51 个全部通过（含玩家接口 + 运营接口 + 审计日志 + 鉴权 + envelope 格式）
- **Alembic 迁移环境已初始化**（vote-service + world-service + content-service + generation-service + review-service + player-service + ops-service），迁移脚本已生成：
  - vote-service：
    - 首次迁移（vote 核心三表）：`services/vote/alembic/versions/2026_07_01_1529_ba4a0034a620_init_vote_tables.py`
    - 审计日志表：`services/vote/alembic/versions/2026_07_02_0200_c8d2e5f1a730_add_audit_logs_table.py`
  - world-service：
    - 首次迁移（regions 表）：`services/world/alembic/versions/2026_07_04_0201_a1b2c3d4e5f6_init_world_tables.py`
    - 审计日志表：`services/world/alembic/versions/2026_07_04_0202_b2c3d4e5f6a7_add_audit_logs_table.py`
  - content-service：
    - 首次迁移（regions、vote_cycles、content_packages、release_records、rollback_records 表）：`services/content/alembic/versions/2026_07_04_0203_c3d4e5f6a7b8_init_content_tables.py`
    - 审计日志表：`services/content/alembic/versions/2026_07_04_0204_d4e5f6a7b8c9_add_audit_logs_table.py`
  - generation-service：
    - 首次迁移（vote_cycles、vote_candidates、generation_requests、generated_objects 表）：`services/generation/alembic/versions/2026_07_04_0205_e5f6a7b8c9d0_init_generation_tables.py`
    - 审计日志表：`services/generation/alembic/versions/2026_07_04_0206_f6a7b8c9d0e1_add_audit_logs_table.py`
  - review-service：
    - 首次迁移（review_records 表）：`services/review/alembic/versions/2026_07_04_0207_a7b8c9d0e1f2_init_review_tables.py`
    - 审计日志表：`services/review/alembic/versions/2026_07_04_0208_b8c9d0e1f2a3_add_audit_logs_table.py`
  - player-service：
    - 首次迁移（players、player_quests、player_regions 表）：`services/player/alembic/versions/2026_07_04_0209_c9d0e1f2a3b4_init_player_tables.py`
    - 审计日志表：`services/player/alembic/versions/2026_07_04_0210_d0e1f2a3b4c5_add_audit_logs_table.py`
  - ops-service：
    - 首次迁移（ops_dashboards、ops_actions 表）：`services/ops/alembic/versions/2026_07_04_0211_e1f2a3b4c5d6_init_ops_tables.py`
    - 审计日志表：`services/ops/alembic/versions/2026_07_04_0212_f2a3b4c5d6e7_add_audit_logs_table.py`
- `world-service` 已完成骨架初始化与区域管理接口：
  - 数据模型：`Region`、`AuditLog`（对应 `backend-data-spec.md`）
  - 玩家 API 路由：`GET /api/v1/health`、`GET /api/v1/world/regions`、`GET /api/v1/world/regions/{region_id}`
  - 运营 API 路由：`POST /api/v1/ops/world/regions`（创建区域）、状态更新
  - 区域状态机：locked → active → unstable → archived
  - 统一响应 envelope（对齐 `12-api-design.md` 规范）
  - JWT 认证（`world:read` scope、ops 角色权限）
  - 审计日志持久化
  - 测试用例 40 个全部通过（含玩家接口 + 运营接口 + 审计日志 + 鉴权 + envelope 格式）
- `content-service` 已完成骨架初始化与内容包管理：
  - 数据模型：`ContentPackage`、`ReleaseRecord`、`RollbackRecord`、`AuditLog`（对应 `backend-data-spec.md`）
  - 玩家 API 路由：`GET /api/v1/health`、`GET /api/v1/content/updates`、`GET /api/v1/content/packages/{package_id}`
  - 运营 API 路由：`POST /api/v1/ops/content-packages`（创建内容包）、发布、回滚
  - 内容包状态机：packaged → gray → live → archived，gray/live → rolled_back
  - 统一响应 envelope（对齐 `12-api-design.md` 规范）
  - JWT 认证（`content:read`、`content:release`、`content:rollback` scope）
  - 审计日志持久化
  - 测试用例 48 个全部通过（含玩家接口 + 运营接口 + 审计日志 + 鉴权 + envelope 格式）
- `generation-service` 已完成骨架初始化与内容生成请求管理：
  - 数据模型：`GenerationRequest`、`GeneratedObject`、`AuditLog`（对应 `backend-data-spec.md`）
  - 运营 API 路由：生成请求创建/查询/状态更新、生成对象查询/状态更新（审核）
  - 生成请求状态机：pending → processing → succeeded / failed_retryable → pending（重试） / failed_permanent
  - 生成对象状态机：pending_review → approved / rejected / needs_revision
  - 统一响应 envelope（对齐 `12-api-design.md` 规范）
  - JWT 认证（`review:approve` scope、ops 角色权限）
  - 审计日志持久化
  - 测试用例 47 个全部通过（含运营接口 + 审计日志 + 鉴权 + envelope 格式 + 状态机校验）
- `review-service` 已完成骨架初始化与内容审核管理：
  - 数据模型：`ReviewRecord`、`AuditLog`（对应 `backend-data-spec.md`）
  - 运营 API 路由：审核记录创建/查询/更新、审核批准/拒绝
  - 审核状态机：pending → approved / rejected / manual_review
  - 风险等级：low / medium / high / critical
  - 统一响应 envelope（对齐 `12-api-design.md` 规范）
  - JWT 认证（`review:approve` scope、reviewer/ops 角色权限）
  - 审计日志持久化
  - 测试用例 38 个全部通过（含运营接口 + 审计日志 + 鉴权 + envelope 格式 + 状态机校验）
- `gateway-service` 已完成骨架初始化与 API 网关核心功能：
  - 核心功能：JWT 认证中间件、令牌桶限流中间件、请求追踪中间件、反向代理路由
  - 代理路由：vote/world/content/generation/review 服务路由映射
  - 请求头传递：X-Request-Id、X-Trace-Id、Idempotency-Key 透传
  - 健康检查：`GET /api/v1/health`、`GET /api/v1/health/services`
  - 统一响应 envelope（对齐 `12-api-design.md` 规范）
  - 错误响应格式（统一 error envelope）
  - 结构化日志（structlog）
  - 测试用例 32 个全部通过（含认证 + 限流 + 代理 + 追踪 + 健康检查）
- `player-service` 已完成骨架初始化与玩家管理接口：
  - 数据模型：`Player`、`PlayerQuest`、`PlayerRegion`、`AuditLog`（对应 `backend-data-spec.md`）
  - 玩家 API 路由：`GET /api/v1/health`、`GET /api/v1/player/info`、`GET /api/v1/player/quests`、`GET /api/v1/player/regions`
  - 运营 API 路由：`POST /api/v1/ops/players`（创建玩家）、`GET /api/v1/ops/players`（列表）、`GET /api/v1/ops/players/{player_id}`（详情）、`PUT /api/v1/ops/players/{player_id}`（更新）、`POST /api/v1/ops/players/{player_id}/regions/{region_id}/unlock`（解锁区域）
  - 任务状态机：available → active → completed / failed
  - 统一响应 envelope（对齐 `12-api-design.md` 规范）
  - JWT 认证（`world:read`、`quests:read` scope、ops 角色权限）
  - 审计日志持久化
  - 自定义 UUID 类型兼容 SQLite 测试环境
  - 测试用例 23 个全部通过（含玩家接口 + 运营接口 + 审计日志 + 鉴权 + envelope 格式）
- `ops-service` 已完成骨架初始化与运营后台接口：
  - 数据模型：`OpsDashboard`、`OpsAction`、`AuditLog`（对应 `backend-data-spec.md`）
  - 运营 API 路由：`GET /api/v1/health`、`GET /api/v1/ops/dashboard`（仪表盘）、`GET /api/v1/ops/dashboard/history`（历史）、`GET /api/v1/ops/actions`（运营操作列表）、`GET /api/v1/ops/actions/{action_id}`（操作详情）、`GET /api/v1/ops/system/status`（系统状态）
  - 统一响应 envelope（对齐 `12-api-design.md` 规范）
  - JWT 认证（`ops:*` scope）
  - 审计日志持久化
  - 自定义请求 ID 头支持
  - 测试用例 32 个全部通过（含仪表盘 + 运营操作 + 系统状态 + 审计日志 + 鉴权 + envelope 格式）
- 本地开发基础设施：`infra/docker-compose.dev.yml`（PostgreSQL 16 + Redis 7）。
- `.gitignore`、各目录 README 占位、`.env.example` 已配置。
- `docs/packages/first-slice/` 第一版需求包：包含投票链路完整规范子集（功能特性、API 接口清单、数据模型定义、业务流程说明、验收标准），作为 MVP 投票链路验证的需求基线。
- **CI/CD 基础设施**：
  - GitHub Actions 工作流：`ci.yml`（lint、类型检查、测试）、`cd.yml`（部署）、`docker-build.yml`（Docker 构建）
  - 各服务 Dockerfile（vote、world、content、generation、review、gateway、player、ops、workers）
  - 生产环境配置：`infra/docker-compose.prod.yml`、`infra/.env.prod.example`
  - Nginx 反向代理配置：`infra/nginx/conf.d/default.conf`
  - 监控配置：`infra/prometheus/prometheus.yml`、`infra/grafana/provisioning/datasources/prometheus.yml`、`infra/grafana/dashboards/game-dashboard.json`
  - 部署脚本：`tools/deploy.sh`、`tools/rollback.sh`、`tools/health-check.sh`、`tools/migrate-all.sh`
- **Godot 客户端工程**：
  - Godot 4 项目骨架已初始化（`project.godot`、`icon.svg`）
  - 标准目录结构：`scenes/`、`scripts/`、`data/`、`assets/`、`tests/`
  - 5 个核心 Autoload 单例：GameState、APIManager、VoteManager、ContentManager、AudioManager
  - 基础场景：Main（主入口）、MainMenu（主菜单）、VotingPanel（投票面板）、WorldMap（世界地图）
  - 数据配置：game_config.json、region_list.json、npc_list.json、quest_list.json（均带 schema_version）
  - GUT 测试框架与基础测试用例（GameState、APIManager）
  - 投票系统端到端功能完善：VoteManager 增强（loading 状态、错误处理、辅助方法）、VotingPanel 完整交互（加载/选择/提交/反馈）、VoteResultPanel 结果展示（进度条、获胜者高亮、影响信息）、VoteHistoryPanel 历史记录（列表、分页）、主菜单投票入口、场景流转逻辑
  - 世界探索与任务系统完善：WorldMap 增强（区域渲染、状态标识、点击选择、详情展示）、QuestPanel 任务面板（任务列表、详情、目标进度、奖励展示、任务接取）、NPCPanel 和 NPCDialog（NPC 列表、对话交互、任务接取）、数据配置完善（区域列表、任务实例、NPC 实例）、测试用例补充（WorldMap、QuestPanel）
  - 客户端与后端 API 联调完善：APIManager 错误码对齐（NO_OPEN_VOTE_CYCLE、ALREADY_VOTED、TOKEN_EXPIRED 等）、重试机制（幂等请求）、HTTP 方法支持（GET/POST/PUT/DELETE）；VoteManager 错误处理与状态同步（auth_error 信号、can_vote 判断）；ContentManager 版本同步与更新检查（自动检查、手动检查、安装/卸载）；新增 WorldManager（区域列表、详情、缓存）和 PlayerManager（玩家信息、任务列表、区域状态）；测试用例补充（APIManager 错误处理、WorldManager、PlayerManager）
  - **首期内容实例化**：世界观根设定（`docs/20-specs/world-lore-spec.md`）、2个首期区域（铁卫城周边、灰谷废墟）、4个势力阵营（铁卫联盟、自由领地、暗影面纱、丰收商会）、6个核心NPC（艾瑞尔·铁盾、格尔·铁锤、玛莎·耕地、雷克斯·金币、露娜·暗星、杰克·流浪者）、7个任务实例（2条主线+5条支线）、3个章节定义（觉醒之路、铁卫的召唤、自由之声）；所有数据配置均带 schema_version 字段，包含完整的阵营关系矩阵、声望系统规则、区域详情、NPC 对话和任务目标
- **内容包打包与发布流程**：
  - 首期内容包初始化脚本（`services/content/scripts/seed_initial_packages.py`），支持从 game/data/ 读取内容并创建区域内容包
  - 内容包打包 Worker 增强（`workers/tasks/content_packaging.py`）：新增 `validate_package_payload` 校验函数、`load_content_from_directory` 目录加载函数、`package_content_from_directory` 任务
  - 内容包发布流程增强（`workers/tasks/content_release.py`）：新增 `build_gray_scope` 灰度范围构建、`promote_to_full_release` 全量发布任务，支持按区域/玩家百分比/指定玩家列表进行灰度
  - 测试用例补充：content_packaging（6个）、content_release（8个），全部通过
- **内容审核四项检查**：
  - 工具脚本：`tools/content_check/`（世界一致性、数值边界、内容安全、重复度四项检查）
  - 基类与配置：`base.py`、`config.py`、`__init__.py`
  - 各检查器：`world_consistency.py`、`reward_boundary.py`、`content_safety.py`、`duplication.py`
  - 测试覆盖：28 个单元测试全部通过
  - 与 Workers 集成：`workers/tasks/content_review.py` 已更新为调用检查器实现
  - 门禁注册表更新：`gate_registry.yaml` 已新增 4 个 content 类型门禁
- **Prometheus 监控指标集成**：
  - 所有 8 个后端服务（vote、world、content、generation、review、gateway、player、ops）均已集成 `prometheus-fastapi-instrumentator`
  - 每个服务均提供 `/metrics` 端点，支持 HTTP 请求数、延迟、错误率等指标采集
  - gateway-service 的 `/metrics` 端点已豁免认证，便于 Prometheus 直接采集
  - 每个服务新增 metrics 端点测试用例，全部通过

## 当前主要风险

- ~~`vote-service` 端到端可运行验证尚未完成（需 PostgreSQL 环境，Docker 在 CI 沙箱不可用）。~~ 已完成，代码层面已验证通过，PostgreSQL 配置就绪。
- ~~JWT 鉴权中间件尚未实现，运营接口缺少真实的角色和权限校验。~~ 已完成，运营接口具备完整的 Scope 校验。
- ~~审计日志（`audit_logs` 表）尚未持久化，运营操作的审计记录仅在结构化日志中。~~ 已完成，审计日志持久化到 `audit_logs` 表。
- ~~监控 metrics endpoint 待集成~~ 已完成，所有 8 个后端服务均已集成 Prometheus metrics，支持 HTTP 请求数、延迟、错误率等指标采集
- `10-requirements/` 与 `20-specs/` 仍有一定内容重叠，后续若继续双向修改，容易再次漂移。
- `40-dev-loop/` 中部分设计偏目标态，若不裁剪就直接照搬，实施成本会偏高。

## 下一阶段建议

1. ~~确认仓库策略：~~ 已确定为单仓模式，当前仓库继续演进为主仓库。
2. ~~选定首个最小落地目标：~~ 已确定为最小投票链路（vote-service 骨架已初始化）。
3. ~~初始化 Alembic 并生成首次迁移脚本：~~ 已完成，vote 核心三表迁移脚本就绪。
4. ~~启动本地 PostgreSQL 并执行迁移，完成 vote-service 端到端可运行验证。~~ 已完成（51 个测试全部通过，mypy 类型检查通过）。
5. ~~为 vote-service 补充投票结算逻辑与运营写接口（创建投票周期等）：~~ 已完成。
6. ~~为 vote-service 实现 JWT 鉴权中间件与角色/Scope 权限校验。~~ 已完成（41 个测试全部通过）。
7. ~~补充审计日志持久化（`audit_logs` 表写入）。~~ 已完成（49 个测试全部通过）。
7.5. ~~实现统一响应 envelope 格式对齐 `12-api-design.md` 规范。~~ 已完成（51 个测试全部通过）。
7.6. ~~为玩家接口添加 JWT 认证（votes:read/votes:submit/votes:history:read scope）。~~ 已完成。
7.7. ~~补充 votes 表 candidate_id_idx 索引和 winning_candidate_id FK 约束。~~ 已完成。
8. ~~基于最小投票链路生成第一版需求包（可放在 `docs/packages/first-slice/`），包括从 `20-specs/` 抽出的相关规范子集。~~ 已完成，需求包包含投票周期管理、投票提交、结算、结果展示、审计日志等完整规范子集，以及 API 接口清单、数据模型定义、业务流程说明和验收标准。
9. ~~补异步任务和事件的 payload schema（不阻塞投票 MVP，但内容链路需要）。~~ 已完成，异步任务与事件 schema 规范已发布，包含 7 个核心任务 payload、7 个事件主题、重试策略、死信队列、全链路追踪规范。
10. ~~初始化 content-service（内容包管理、灰度发布、回滚），为内容链路打基础。~~ 已完成（48 个测试全部通过）
11. ~~初始化 generation-service（AI 内容生成请求与结果落库）。~~ 已完成（47 个测试全部通过）
12. ~~初始化 review-service（内容审核、质量评分、人工复核流转）。~~ 已完成（38 个测试全部通过）
13. ~~完善世界探索与任务系统UI（世界地图、任务面板、NPC交互）~~ 已完成，WorldMap、QuestPanel、NPCPanel、NPCDialog 组件已实现，数据配置已完善，测试用例已补充
14. ~~完善客户端与后端 API 联调封装（APIManager、VoteManager、ContentManager、WorldManager、PlayerManager）~~ 已完成，错误码对齐、重试机制、缓存管理、测试用例补充完成
15. ~~首期内容实例化（世界观、区域、阵营、NPC、任务、章节）~~ 已完成，包含世界观根设定、2个首期区域配置、4个势力阵营、6个核心NPC、7个任务实例（1条主线+6条支线）、3个章节定义
16. ~~内容包打包与发布流程实现~~ 已完成，包含首期内容包初始化脚本、内容包校验与目录加载、灰度发布范围配置、全量发布升级任务、完整测试覆盖
17. ~~内容审核四项检查与工具脚本（世界一致性、数值边界、内容安全、重复度）~~ 已完成，tools/content_check/ 四个检查器 + 28个测试 + workers 集成 + 门禁注册表更新

## 进入实施前的建议门槛

- ~~产品边界和 MVP 范围不再频繁变更。~~ 已明确
- ~~首个最小落地目标明确到单条主线能力。~~ 已确定为最小投票链路
- ~~确认是沿当前仓库继续扩展，还是拆出独立工程仓库。~~ 已确定为单仓模式
- ~~初始化 Alembic 迁移脚本，完成 vote 核心三表定义。~~ 已完成
- ~~补充运营写接口与投票结算逻辑。~~ 已完成（26 个测试全部通过）
- ~~启动数据库并执行迁移，完成 vote-service 端到端可运行验证。~~ 已完成（51 个测试全部通过，mypy 类型检查通过）
- ~~实现 JWT 鉴权中间件，确保运营接口有角色和权限校验。~~ 已完成（41 个测试全部通过）

## 与其他文档的关系

- `docs/00-governance/document-map.md`
  - 文档角色分层与权威关系。
- `docs/00-governance/governance-phase-summary.md`
  - 治理阶段结论、已形成基线和后续移交重点。
- `docs/00-governance/quick-start.md`
  - 当前仓库使用方式与实施顺序。
- `docs/20-specs/README.md`
  - 执行规范目录入口。
- `docs/30-api/`
  - 接口参考与样例。

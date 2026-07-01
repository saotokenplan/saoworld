# 01 - 仓库结构与命名规范

> 适用角色：全员
> 本文件定义仓库目录结构、文件命名、ID前缀等约定。

## 根目录结构

```
.
├── docs/           # 文档与规范（00-governance ~ 50-research 六层结构）
├── game/           # Godot 4 客户端工程
├── services/       # 后端微服务（gateway/player/world/vote/generation/review/content/ops）
├── workers/        # Celery 异步任务 Worker
├── tools/          # 离线脚本、校验器、打包工具
├── infra/          # Docker、Compose、部署配置
├── telemetry/      # 指标、日志、告警定义
└── .trae/          # IDE 配置、技能、项目规则（本目录）
```

### 各目录职责

| 目录 | 职责 |
|------|------|
| `docs/` | 产品需求、技术规范、API文档、研发流程、技术调研 |
| `game/` | Godot 客户端工程（场景、脚本、资源、数据） |
| `services/` | Web API 与后台微服务 |
| `workers/` | Celery 或其他异步任务入口 |
| `tools/` | 离线脚本、校验器、打包工具、Git hooks |
| `infra/` | Docker Compose、部署配置、基础设施定义 |
| `telemetry/` | 指标、日志、告警定义 |

---

## 后端服务目录结构

每个微服务必须遵循以下目录结构：

```
services/<service-name>/
├── app/
│   ├── api/          # API 路由层（routes.py）
│   ├── core/         # 核心配置、数据库连接（config.py, db.py）
│   ├── domain/       # SQLAlchemy 领域模型（models.py）
│   ├── repositories/ # 数据访问层
│   ├── schemas/      # Pydantic 请求/响应模型
│   ├── tasks/        # Celery 异步任务定义
│   └── main.py       # FastAPI 应用入口
├── tests/            # 测试文件（conftest.py, test_*.py）
├── scripts/          # 运维脚本（可选，如 seed_dev_data.py）
├── pyproject.toml    # 项目配置与依赖
├── .env.example      # 环境变量模板
└── README.md         # 服务说明
```

服务命名使用小写英文单词，如 `vote`、`player`、`world`、`content`。

---

## 文件与目录命名

### 通用规则

| 类型 | 命名风格 | 示例 |
|------|----------|------|
| 目录名 | kebab-case（小写短横线）或小写单词 | `api/`、`repositories/`、`vote-service` |
| Python 模块文件 | snake_case（下划线） | `vote_repo.py`、`config.py` |
| 其他文件 | kebab-case（小写短横线） | `docker-compose.dev.yml` |
| 类名 | PascalCase（大驼峰） | `VoteCycle`、`VoteRepository` |
| 函数/方法名 | snake_case（下划线） | `get_current_open_cycle()` |
| 变量名 | snake_case（下划线） | `vote_cycle_id` |
| 常量 | UPPER_SNAKE_CASE | `MAX_VOTE_WEIGHT` |

### Godot 客户端目录约定

```
game/
├── project.godot
├── scenes/
│   ├── player/
│   ├── npc/
│   ├── world/
│   └── ui/
├── scripts/        # typed GDScript
├── data/           # 静态数据、配置
├── assets/         # 美术、音频资源
└── tests/
```

- 场景文件与主脚本文件同名
- 场景目录按领域划分（player/npc/world/ui）

---

## ID 前缀约定

所有业务 ID 使用稳定前缀，便于日志追踪和问题排查：

| 前缀 | 适用对象 | 示例 |
|------|----------|------|
| `region_` | 区域ID | `region_wasteland_01` |
| `chapter_` | 章节ID | `chapter_02` |
| `npc_` | NPC ID | `npc_blacksmith_01` |
| `quest_` | 任务ID | `quest_rescue_01` |
| `event_` | 事件ID | `event_raid_01` |
| `pkg_` | 内容包版本 | `pkg_ch02_waste_20260701_01` |
| `tpl_` | 模板版本 | `tpl_wasteland_quest_v2` |
| `rule_` | 审核规则版本 | `rule_content_v1` |
| `gate_` | 门禁规则 | `gate_quality_check` |
| `gen_` | 生成请求ID | `gen_20260701_001` |
| `req_` | 请求追踪ID | `req_vote_submit_xxx` |
| `trace_` | 全链路追踪ID | `trace_xxx` |

---

## 版本命名

| 类型 | 格式 | 示例 |
|------|------|------|
| 服务端版本 | 语义化版本 SemVer | `0.1.0`、`1.2.3` |
| 内容包版本 | `pkg_<chapter>_<region>_<yyyymmdd>_<seq>` | `pkg_ch02_waste_20260701_01` |
| 模板版本 | `tpl_<domain>_v<major>.<minor>` | `tpl_npc_v2.1` |
| 规则版本 | `rule_<domain>_v<major>.<minor>` | `rule_review_v1.0` |

---

## 相关规则

- Python 后端代码规范 → [10-python-backend.md](./10-python-backend.md)
- Godot 客户端规范 → [30-godot-client.md](./30-godot-client.md)

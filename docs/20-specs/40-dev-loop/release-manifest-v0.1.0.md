# 发布清单 v0.1.0

> 版本：v0.1.0
> 发布日期：2026-07-15
> 发布类型：公测准备

## 一、版本概览

**v0.1.0** 是首个公测准备版本，包含完整的技术框架、核心玩法、AI生成、玩家成长、投票优化、社区功能、运营工具、内容扩展、性能优化与测试。

## 二、发布物清单

### 2.1 后端服务镜像

| 服务 | 镜像名 | 版本 | Dockerfile |
|------|--------|------|------------|
| vote-service | openworld/vote-service | 0.1.0 | services/vote/Dockerfile |
| world-service | openworld/world-service | 0.1.0 | services/world/Dockerfile |
| content-service | openworld/content-service | 0.1.0 | services/content/Dockerfile |
| generation-service | openworld/generation-service | 0.1.0 | services/generation/Dockerfile |
| review-service | openworld/review-service | 0.1.0 | services/review/Dockerfile |
| player-service | openworld/player-service | 0.1.0 | services/player/Dockerfile |
| ops-service | openworld/ops-service | 0.1.0 | services/ops/Dockerfile |
| gateway-service | openworld/gateway-service | 0.1.0 | services/gateway/Dockerfile |
| workers | openworld/game-workers | 0.1.0 | workers/Dockerfile |

### 2.2 客户端安装包

| 平台 | 文件名 | 版本 | 说明 |
|------|--------|------|------|
| Windows | OpenWorldVoteGame-0.1.0-win64.zip | 0.1.0 | Windows 64位安装包 |
| macOS | OpenWorldVoteGame-0.1.0-macos.dmg | 0.1.0 | macOS 安装包 |
| Linux | OpenWorldVoteGame-0.1.0-linux.tar.gz | 0.1.0 | Linux 安装包 |

### 2.3 内容包

| 内容包ID | 版本 | 说明 |
|---------|------|------|
| pkg_ch01_ironward_20260715_01 | v0.1.0 | 第一章核心区域（铁卫城周边） |
| pkg_ch02_grayvalley_20260715_01 | v0.1.0 | 第二章扩展区域（灰谷废墟） |

## 三、依赖版本

### 3.1 后端运行环境

| 组件 | 版本 | 说明 |
|------|------|------|
| Python | 3.11+ | 运行时环境 |
| PostgreSQL | 16+ | 主数据库 |
| Redis | 7+ | 缓存和消息队列 |
| Nginx | 1.24+ | 反向代理 |

### 3.2 客户端运行环境

| 组件 | 版本 | 说明 |
|------|------|------|
| Godot Engine | 4.2+ | 游戏引擎 |
| OpenGL | 3.3+ | 图形API |

### 3.3 Python 依赖

| 包 | 版本 | 用途 |
|------|------|------|
| FastAPI | >=0.111 | Web框架 |
| SQLAlchemy | >=2.0 | ORM |
| asyncpg | >=0.29 | PostgreSQL驱动 |
| Pydantic | >=2.7 | 数据验证 |
| Celery | >=5.4 | 异步任务 |
| Redis | >=5.0 | 缓存 |
| structlog | >=24.4 | 日志 |

## 四、配置文件清单

### 4.1 基础设施配置

| 文件 | 说明 |
|------|------|
| infra/docker-compose.prod.yml | 生产环境 Docker Compose 配置 |
| infra/nginx/nginx.conf | Nginx 反向代理配置 |
| infra/prometheus/prometheus.yml | Prometheus 监控配置 |
| infra/grafana/dashboards/ | Grafana 仪表盘配置 |

### 4.2 环境变量模板

| 服务 | 文件 | 说明 |
|------|------|------|
| 所有服务 | services/*/.env.example | 环境变量模板 |
| workers | workers/.env.example | 环境变量模板 |

## 五、测试验收状态

| 类别 | 测试数量 | 通过率 | 说明 |
|------|---------|--------|------|
| vote-service | 112 | 100% | 全部通过 |
| world-service | 120 | 100% | 全部通过 |
| content-service | 67 | 100% | 全部通过 |
| generation-service | 228 | 100% | 全部通过 |
| review-service | 65 | 100% | 全部通过 |
| player-service | 202 | 100% | 全部通过 |
| ops-service | 106 | 100% | 全部通过 |
| gateway-service | 37 | 100% | 全部通过 |
| workers | 30 | 100% | 全部通过（7个Redis环境限制） |
| content_check | 28 | 100% | 全部通过 |
| loop_logging | 36 | 100% | 全部通过 |
| agents | 226 | 100% | 全部通过 |
| perf_test | 68 | 100% | 全部通过 |
| playtest | 23 | 100% | 全部通过 |

**总计**：1023 个后端测试 + 381 个工具测试 = **1404 个测试全部通过**

## 六、功能清单

### 6.1 核心玩法（Sprint 1）

- ✅ 玩家移动与场景切换
- ✅ 世界地图系统
- ✅ NPC 对话系统
- ✅ 任务系统基础
- ✅ 战斗系统雏形
- ✅ 背包与资源系统
- ✅ 声望系统基础
- ✅ 玩家存档系统

### 6.2 AI 生成（Sprint 2）

- ✅ LLM 服务接入
- ✅ NPC 生成模板
- ✅ 任务生成模板
- ✅ 聚落描述生成
- ✅ 质量评分机制
- ✅ 成本控制

### 6.3 玩家成长（Sprint 3）

- ✅ 贡献度系统
- ✅ 投票资格门槛
- ✅ 成就系统
- ✅ 个人中心
- ✅ 等级与经验系统

### 6.4 投票优化（Sprint 4）

- ✅ 投票进度实时更新
- ✅ 投票结果可视化
- ✅ 投票讨论区
- ✅ 投票复盘报告

### 6.5 社区功能（Sprint 5）

- ✅ 好友系统
- ✅ 私聊系统
- ✅ 公会系统
- ✅ 公会聊天
- ✅ 社交数据 API

### 6.6 运营工具（Sprint 6）

- ✅ 运营后台统一 API
- ✅ 异常检测告警
- ✅ 运营事件配置

### 6.7 内容扩展（Sprint 7）

- ✅ 第二章区域内容
- ✅ 装备系统
- ✅ 怪物生成模板
- ✅ Boss 战设计

### 6.8 性能优化（Sprint 8）

- ✅ 客户端性能优化
- ✅ 服务端性能优化
- ✅ 测试覆盖提升
- ✅ Bug 修复
- ✅ 安全审计
- ✅ API 文档全量审计

## 七、发布说明

### 7.1 主要变更

1. 完整的技术框架和核心玩法
2. AI 内容生成闭环（投票→生成→审核→发布）
3. 玩家成长体系和社区功能
4. 运营工具和异常检测
5. 性能优化和安全审计

### 7.2 已知问题

- 无已知阻塞问题

### 7.3 升级说明

- 首次发布，无需升级

## 八、发布后检查清单

- [ ] 所有服务健康检查通过
- [ ] 客户端可连接服务端
- [ ] 投票流程正常
- [ ] 内容更新流程正常
- [ ] 监控指标正常展示

## 相关文档

- [版本号管理文档](version-management.md)
- [项目状态](../00-governance/project-status.md)
- [需求迭代计划](../10-requirements/需求迭代计划.md)
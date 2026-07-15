# 版本号管理文档

> 文档状态：active
> 适用阶段：项目全周期
> 维护要求：每次发布前更新

## 版本号规范

本项目采用语义化版本（SemVer）规范：`MAJOR.MINOR.PATCH`

- **MAJOR**：不兼容的 API 变更
- **MINOR**：向后兼容的功能新增
- **PATCH**：向后兼容的问题修正

## 当前版本

**v0.1.0**（2026-07-15）

- 首个公测准备版本
- Sprint 0-8 全部完成
- 包含完整的技术框架、核心玩法、AI生成、玩家成长、投票优化、社区功能、运营工具、内容扩展、性能优化与测试

## 版本号配置位置

### 后端服务

| 服务 | 配置文件 | 当前版本 |
|------|---------|----------|
| vote-service | services/vote/pyproject.toml | 0.1.0 |
| world-service | services/world/pyproject.toml | 0.1.0 |
| content-service | services/content/pyproject.toml | 0.1.0 |
| generation-service | services/generation/pyproject.toml | 0.1.0 |
| review-service | services/review/pyproject.toml | 0.1.0 |
| player-service | services/player/pyproject.toml | 0.1.0 |
| ops-service | services/ops/pyproject.toml | 0.1.0 |
| gateway-service | services/gateway/pyproject.toml | 0.1.0 |
| workers | workers/pyproject.toml | 0.1.0 |

### 客户端

| 组件 | 配置文件 | 当前版本 |
|------|---------|----------|
| Godot 客户端 | game/project.godot | 0.1.0 |

### 基础设施

| 组件 | 配置文件 | 当前版本 |
|------|---------|----------|
| Docker Compose | infra/docker-compose.prod.yml | 0.1.0 |

## 版本更新流程

1. **开发阶段**：使用 `-dev` 后缀（如 `0.2.0-dev`）
2. **测试阶段**：使用 `-alpha` 或 `-beta` 后缀（如 `0.2.0-alpha.1`）
3. **发布阶段**：移除后缀（如 `0.2.0`）

## 版本发布检查清单

- [ ] 所有服务版本号已更新
- [ ] 客户端版本号已更新
- [ ] CHANGELOG 已更新
- [ ] Git tag 已创建
- [ ] Docker 镜像已构建并推送

## 历史版本

| 版本 | 发布日期 | 说明 |
|------|---------|------|
| v0.1.0 | 2026-07-15 | 首个公测准备版本 |

## 相关文档

- [发布清单](release-manifest-v0.1.0.md)
- [项目状态](../00-governance/project-status.md)
- [里程碑与验收标准](../10-requirements/项目里程碑与验收标准.md)
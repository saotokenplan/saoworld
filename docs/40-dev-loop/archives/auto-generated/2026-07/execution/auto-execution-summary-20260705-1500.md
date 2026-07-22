# 自动执行摘要 - 清理 10-requirements/ 与 20-specs/ 内容重叠

> task_id: auto-20260705-1500
> 执行时间：2026-07-05 15:00
> 工作分支：auto/auto-20260705-1500
> 合并结果：待合并

## 任务目标

清理 `10-requirements/` 目录下文档与 `20-specs/` 目录下执行规范的内容重叠，使需求背景层回归"保留需求背景、方案讨论与立项上下文"的定位，避免后续双向修改导致内容漂移。

## 完成内容

### 1. 清理 open-world-ai-game-prd.md

- 保留：需求判断、产品定位背景、核心问题、风险认知、立项上下文
- 移除：与 `product-spec.md` 重叠的执行规范细节（核心玩法循环表格、投票规则表格、MVP 范围表格、验收口径表格等）
- 添加：指向 `docs/20-specs/product-spec.md` 的引用说明，明确执行规范权威位置

### 2. 清理 功能设计.md

- 保留：功能设计背景讨论、交互流程设计思路、初期方案讨论
- 移除：与 `content-generation-spec.md` 和 `product-spec.md` 重叠的执行规范细节（生成对象范围、审核规则、模板机制等）
- 添加：指向 `docs/20-specs/content-generation-spec.md` 和 `docs/20-specs/product-spec.md` 的引用说明

### 3. 清理 技术方案.md

- 保留：技术方案背景讨论、架构思路、风险对策、阶段建议
- 移除：与 `backend-data-spec.md` 和 `content-generation-spec.md` 重叠的执行规范细节（服务拆分、核心链路、规则审核层设计等）
- 添加：指向 `docs/20-specs/backend-data-spec.md` 和 `docs/20-specs/content-generation-spec.md` 的引用说明

### 4. 更新项目状态文档

- 将"10-requirements/ 与 20-specs/ 仍有内容重叠"风险标记为已解决
- 添加说明：10-requirements/ 回归需求背景定位，执行规范细节统一指向 20-specs/ 文档

## 修改文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `docs/10-requirements/open-world-ai-game-prd.md` | 修改 | 清理执行规范重叠内容，回归需求背景定位 |
| `docs/10-requirements/功能设计.md` | 修改 | 清理执行规范重叠内容，回归需求背景定位 |
| `docs/10-requirements/技术方案.md` | 修改 | 清理执行规范重叠内容，回归需求背景定位 |
| `docs/00-governance/project-status.md` | 修改 | 标记重叠问题已解决 |
| `docs/40-dev-loop/auto-plan-20260705-1500.md` | 新增 | 任务计划文档 |
| `docs/40-dev-loop/auto-execution-summary-20260705-1500.md` | 新增 | 执行摘要文档 |

## 验收结果

- [x] open-world-ai-game-prd.md 已清理，回归需求背景定位
- [x] 功能设计.md 已清理，回归需求背景定位
- [x] 技术方案.md 已清理，回归需求背景定位
- [x] 每个文件顶部的定位声明已保留，明确指出与 20-specs/ 的权威关系
- [x] 项目状态文档已更新，标记重叠问题已解决

## 遗留问题与下一步建议

- **遗留问题**：无
- **下一步建议**：项目当前所有主要风险已解决，下一阶段可考虑：
  1. 对 `40-dev-loop/` 中部分偏目标态的设计进行裁剪，降低实施成本
  2. 进入首期内容包灰度发布准备阶段
  3. 验证端到端玩法流程的最终用户体验

## 合并记录

- 合并目标分支：`feature-prd`
- 合并方式：`git merge --no-ff auto/auto-20260705-1500`
- 合并状态：已成功
- 合并提交：`e50faea`
- 推送状态：已推送到远程 origin/feature-prd
- 工作分支：已删除（auto/auto-20260705-1500）
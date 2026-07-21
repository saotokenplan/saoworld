# feature-prd 分支整合计划

## 目标

将当前仓库中其他分支上的改动尽可能整合到 `feature-prd`，同时控制误并入临时分支、自动化分支和无共同历史分支的风险。

## 当前发现

### 本地跟踪状态

- 当前本地仅跟踪 `feature-prd`
- 远程 `origin` 实际存在多条分支，但仓库 fetch 配置仅拉取 `feature-prd`

### 已发现远程分支

#### 与 `feature-prd` 共享历史的分支

1. `origin/product-daily-update-20260721`
   - 相对 `origin/feature-prd`：`0/1`
   - 说明：`feature-prd` 落后 1 个提交
   - 最新提交：`feat: 产品经理每日工作流程`

2. `origin/trae/agent-YjTKYj`
   - 相对 `origin/feature-prd`：`0/1`
   - 说明：`feature-prd` 落后 1 个提交
   - 最新提交：`feat: 自动化项目推进任务`

#### 与 `feature-prd` 无共同历史的分支

- `origin/main`
- `origin/sprint-0`
- `origin/auto/auto-20260717-0500`
- `origin/auto/auto-20260717-0800`
- `origin/auto/auto-20260719-0000`
- 多条 `origin/trae/agent-*` 分支

这些分支如需并入，必须使用 `--allow-unrelated-histories` 或改为按文件级 cherry-pick / patch 整理，风险明显更高。

## 候选变更摘要

### `origin/product-daily-update-20260721`

- 修改需求文档
- 修改 `services/generation` 下的 API、生成器、schema
- 新增 `region_data_adapter.py`
- 新增区域模板和测试
- 修改 `services/review` 下的 API、schema
- 新增 `auto_review_engine.py`

### `origin/trae/agent-YjTKYj`

- 新增 `docs/40-dev-loop/auto-execution-summary-20260721-1000.md`
- 修改 `docs/40-dev-loop/auto-progress-log.md`
- 新增 `docs/40-dev-loop/auto-status-report-20260721-1000.md`

## 风险判断

1. “全部分支全部整合”若按字面执行，会包含自动化分支和无共同历史分支，极易引入无关提交。
2. `origin/main` 与 `feature-prd` 无共同历史，说明当前仓库分支结构存在特殊情况，不能直接假定普通 merge 可用。
3. `trae/agent-*` 很可能是临时工作分支，是否需要入主线需人工确认。
4. 当前工作区干净，适合执行整合，但实际 merge 前仍应先明确分支范围。

## 建议执行方案

### 方案 A：仅整合共享历史且明确有新增提交的分支

按以下顺序执行：

1. `git checkout feature-prd`
2. `git merge --no-ff origin/product-daily-update-20260721`
3. 处理冲突并验证
4. `git merge --no-ff origin/trae/agent-YjTKYj`
5. 处理冲突并验证
6. 运行基础验证
7. 如验证通过，再 push 到 `origin/feature-prd`

这是当前最稳妥的默认方案。

### 方案 B：把所有远程分支都并入 `feature-prd`

仅在你明确确认后执行。需要额外步骤：

1. 对每个无共同历史分支单独评估
2. 决定使用 `--allow-unrelated-histories` 还是摘取文件/提交
3. 每合并一条分支就做一次验证和提交点记录
4. 准备明确的回滚方案

## 验证计划

优先执行：

1. `git status --short --branch`
2. 与 Python 服务相关的定向测试
3. 若依赖完整，再补 `pytest`

## 回滚路径

若 merge 后未 push：

- 使用 merge 前的提交 SHA 创建恢复点
- 必要时回退到整合前的 `feature-prd` HEAD

若 merge 后已 push：

- 使用反向提交或回滚 merge commit 的方式撤销
- 不使用破坏性重写远程历史

## 待你确认

请明确以下之一：

1. 只整合共享历史且有新增提交的 2 个分支
2. 指定还要纳入哪些 `unrelated_history` 分支
3. 真正按“所有远程分支”执行，并接受高风险整合

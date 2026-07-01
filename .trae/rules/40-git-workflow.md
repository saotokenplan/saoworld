# 40 - Git 工作流规范

> 适用角色：全员
> 本文件定义 Git 提交格式、分支策略、版本管理、提交时机要求。

---

## 提交信息格式

所有提交信息统一使用以下格式：

```
<type>(<scope>): <summary>
```

- `type`：变更类型（必填）
- `scope`：影响范围（推荐填写，便于快速定位改动）
- `summary`：简短祈使句，说明本次提交做了什么（必填，一行内）

---

## Type 约定

| type | 说明 |
|------|------|
| `docs` | 文档新增、重组、修订 |
| `feat` | 新功能 |
| `fix` | 缺陷修复 |
| `refactor` | 不改变外部行为的代码结构调整 |
| `test` | 测试新增或修订 |
| `chore` | 构建、脚本、依赖、工具链或杂项维护 |

---

## Scope 约定

### 文档相关 Scope

| scope | 说明 |
|-------|------|
| `docs` | 根 README、文档治理相关 |
| `specs` | 20-specs 下的规范变更 |
| `requirements` | 10-requirements 下的需求文档变更 |
| `dev-loop` | 40-dev-loop 研发闭环相关 |
| `skills` | .trae/skills/ 技能文件变更 |
| `api` | 30-api 接口文档变更 |
| `rules` | .trae/rules/ 规则文件变更 |

### 工程相关 Scope（按模块命名）

| scope | 说明 |
|-------|------|
| `gateway` | gateway-service |
| `player` | player-service |
| `world` | world-service |
| `vote` | vote-service |
| `generation` | generation-service |
| `review` | review-service |
| `content` | content-service |
| `ops` | ops-service |
| `workers` | Celery workers |
| `game` | Godot 客户端 |
| `infra` | 基础设施、Docker、部署配置 |
| `telemetry` | 遥测、监控、日志配置 |
| `tools` | 工具脚本 |

> **Scope 维护规则**：新增或删除 scope 时，必须同步更新以下三处：
> 1. 本文件（`.trae/rules/40-git-workflow.md`）
> 2. `tools/validate-commit-msg.py` 中的 `VALID_SCOPES`
> 3. `tools/generate-commit-msg.py` 中的 `SCOPE_PATH_MAPPING`
>
> 以本文件为权威来源，工具脚本必须与之保持一致。

---

## 提交要求（必须严格遵守）

1. **一次提交只表达一个清晰主题**，禁止把无关变更混在同一次提交里
2. `summary` 必须基于**本次实际改动**生成
   - 禁止照抄整段会话总结
   - 禁止照抄任务描述或长篇计划说明
   - 使用"新增/补充/调整/修复"这类明确动作动词开头
3. AI 提交时，提交信息应基于"这一次提交改了什么"生成，**不是**基于"整个会话聊了什么"生成
4. 如果一次会话中包含多个独立改动，**必须拆成多次提交**，分别为每次提交写对应的简明摘要
5. 提交前自检：
   - 无无关文件混入
   - 无明显遗漏（文档/代码/配置同步更新）
   - 无失效引用
6. **规范变更优先于实现提交**：如果本次提交依赖规范变更，优先先提交规范，再提交实现代码

---

## 提交时机判断

### 应立即提交

满足以下条件时，应及时提交：
- 一个清晰主题已经完成（例如：一份治理文档新增完成、一组同主题引用同步完成、一个独立接口样例补齐完成）
- 本次改动已经达到"可交付中间状态"，即使后续还会继续做下一主题，也不需要依赖未提交改动才能成立
- 已完成最小自检，确认没有混入无关文件、明显遗漏或失效引用

### 不应立即提交

满足以下条件时，不应立即提交：
- 当前改动仍处于半完成状态，关键文档、入口或引用还未同步
- 一个主题尚未闭合（例如：只新增了文档正文，但 docs/README.md、映射文档或状态页还没更新）
- 工作区中混有下一主题或无关实验性改动，尚未拆分清楚

### 应拆成多次提交

遇到以下情况时，应拆成多次提交：
- 先改规范，再按规范补实现
- 同一轮工作中同时包含治理文档、API 文档、Skill 引用等多个彼此可独立理解的主题
- 先完成目录或路径调整，再完成内容性补充（两者任一单独提交都能成立）

### 判断原则

以"**这次提交发出去后，其他人能否单独理解并接住这一步**"为判断标准：
- 如果答案是否定的，继续整理后再提交
- 如果答案是肯定的，就不要无谓拖延提交

---

## Git Push 要求

- **每次 `git commit` 完成后，应立即执行一次 `git push`**，把该次提交同步到远程仓库
- 不应长时间只停留在本地
- 若同一轮工作拆成多次提交，则每次提交后都应分别推送，不应等到多次提交累积后再统一推送
- 若远程推送失败，应先确认失败原因，再决定修复配置、同步远程变更或记录阻塞原因
- 在问题未说明清楚前，不应默认视为"已完成同步"
- AI 或自动化 Agent 在具备远程权限时，应把"提交后立即推送"视为默认动作

---

## 提交示例

```
docs(specs): 补充 git 提交规范
docs(specs): 调整 AI 提交说明
docs(api): 新增接口总览文档
feat(vote): 增加投票提交接口与幂等处理
fix(content): 修正内容包回滚状态判断
test(vote): 补充投票流程集成测试
chore(infra): 更新 docker-compose 配置
refactor(vote): 抽取投票Repository公共方法
```

---

## 分支策略

| 分支 | 用途 | 合并方向 |
|------|------|----------|
| `main` | 稳定可发布版本 | 只接受 release/hotfix 合并 |
| `develop` | 集成分支，日常开发主分支 | feature/fix 合并到 develop |
| `feature/<name>` | 功能分支 | 从 develop 切出，合并回 develop |
| `fix/<name>` | 修复分支 | 从 develop/main 切出，合并回对应分支 |
| `release/<version>` | 发布分支 | 从 develop 切出，合并到 main 和 develop |
| `hotfix/<name>` | 紧急修复分支 | 从 main 切出，合并到 main 和 develop |

### 分支命名

- 功能分支：`feature/<模块>-<简短描述>`（如 `feature/vote-history-api`）
- 修复分支：`fix/<问题描述>`（如 `fix/vote-duplicate-submit`）
- 发布分支：`release/v<version>`（如 `release/v0.1.0`）
- 热修复分支：`hotfix/<问题描述>`

---

## 版本规范

| 类型 | 格式 | 示例 |
|------|------|------|
| 服务端版本 | 语义化版本 SemVer | `0.1.0`、`1.2.3` |
| 内容包版本 | `pkg_<chapter>_<region>_<yyyymmdd>_<seq>` | `pkg_ch02_waste_20260701_01` |
| 模板版本 | `tpl_<domain>_v<major>.<minor>` | `tpl_npc_v2.1` |

客户端版本与内容版本必须可映射，确保客户端能正确识别和加载对应版本的内容包。

---

## Git Hooks

项目使用 `.githooks/` 目录管理 Git hooks，通过 `core.hooksPath` 指定。

### 安装

```bash
bash tools/install-git-hooks.sh
```

安装后每次提交会自动：
- **pre-commit**：检查大文件、合并冲突标记、调试断点、.env 文件、潜在密钥泄露
- **prepare-commit-msg**：分析暂存文件，注入建议提交信息（仅空消息时）
- **commit-msg**：验证提交消息格式、检查 scope 是否合法、拦截模糊表述

### Worktree 兼容

hooks 使用 `git rev-parse --show-toplevel` 解析仓库根目录，兼容主仓库和 git worktree。
`install-git-hooks.sh` 使用相对路径设置 `core.hooksPath`，worktree 内独立生效。

### 紧急绕过

```bash
git commit --no-verify
```

仅在紧急情况下使用，并在后续补交合规的提交信息。

---

## Worktree 注意事项

使用 `git worktree` 并行开发时，需注意：

1. **Hooks 独立生效**：每个 worktree 需独立运行 `bash tools/install-git-hooks.sh`
2. **分支隔离**：每个 worktree 检出不同分支，提交直接进入对应分支
3. **Push 不冲突**：不同 worktree 的 push 不应互相阻塞，但需注意同一远程分支的 push 顺序
4. **提交信息一致**：所有 worktree 的提交信息都遵循同一套规范

---

## 相关规则

- 仓库结构与命名 → [01-repository-structure.md](./01-repository-structure.md)
- 发布与回滚规范 → [42-release-rollback.md](./42-release-rollback.md)

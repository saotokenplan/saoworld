---
alwaysApply: true
---

# 循环文件操作权限规则

## 白名单目录（循环可自由读写）
- `.trae/loop-log/`        # 循环日志目录
- `.trae/output/`         # 循环输出目录
- `docs/`                 # 文档目录
- `reports/`              # 报告目录
- `data/processed/`       # 处理后数据目录
- `tools/`                # 工具脚本目录

## 黑名单目录（禁止循环修改）
- `.git/`                 # Git 配置目录
- `.trae/rules/`          # 规则配置目录
- `.trae/hooks/`          # Hook 脚本目录
- `.trae/agents/`         # Subagent 配置目录
- `.trae/skills/`         # Skill 配置目录（仅允许在用户指令下修改）
- `infra/`                # 基础设施配置
- `services/*/config/`    # 服务配置目录
- `.env*`                 # 环境变量文件

## 特殊文件（需显式授权）
- `README.md`             # 项目说明文件
- `pyproject.toml`        # Python 项目配置
- `package.json`          # Node.js 项目配置
- `docker-compose*.yml`   # Docker 配置
- 任何以 `.secret.` 开头的文件
- 任何以 `.private.` 开头的文件
- `game/` 目录下的核心游戏逻辑文件

## 跨目录操作规则
1. 操作不在白名单的文件，必须在 `task-plan.md` 中显式声明
2. 用户确认规划时同步授权文件操作范围
3. 未授权文件操作请求将被拒绝并记录日志

## 项目专属权限（游戏开发项目）

### 代码修改权限层级
| 层级 | 目录 | 修改要求 |
|------|------|---------|
| L1 自由修改 | `docs/`, `.trae/output/` | 无需额外授权 |
| L2 需规划声明 | `game/`, `services/` | 需在 task-plan.md 中声明 |
| L3 需显式授权 | `infra/`, `.trae/rules/` | 需用户逐条确认 |

### 测试文件同步规则
- 修改 `services/*/app/` 下的代码时，必须同步更新 `services/*/tests/` 下的对应测试
- 修改游戏逻辑时，必须同步更新相关测试用例
- 测试覆盖率不得低于修改前水平

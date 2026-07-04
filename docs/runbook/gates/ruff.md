# Runbook: Ruff Lint (G-STATIC-001)

> gate_id: G-STATIC-001
> gate_name: Ruff Lint
> gate_type: static
> owner: QA Agent

## 门禁概述

Ruff Lint 是项目的静态代码检查门禁，使用 Ruff 工具检查 Python 代码的风格、质量和潜在问题。

**触发条件**：
- 路径：`services/**`, `workers/**`, `tools/**`
- 触发：`on_pr`

**执行命令**：
```bash
cd services/<service> && ruff check .
```

**预期耗时**：30 秒

## 常见失败原因

### 1. 代码风格问题（最常见）

**现象**：
- `E501`：行长度超过 120 字符
- `E101`：缩进错误
- `E302`：类/函数前缺少空行

**解决方案**：
```bash
# 自动修复可修复的问题
cd services/<service> && ruff fix .

# 手动修复剩余问题
# 检查并修复行长度问题
cd services/<service> && ruff check --select E501 .
```

### 2. 未使用的导入

**现象**：
- `F401`：导入但未使用
- `F403`：`from x import *` 使用

**解决方案**：
```bash
# 自动移除未使用的导入
cd services/<service> && ruff fix --select F401 .

# 手动检查剩余问题
cd services/<service> && ruff check --select F401,F403 .
```

### 3. 变量命名不符合规范

**现象**：
- `E741`：模糊变量名（如 `l`, `O`, `I`）
- `N802`：函数名应使用 snake_case

**解决方案**：
```bash
# 检查命名问题
cd services/<service> && ruff check --select E741,N802,N806 .

# 手动重命名变量/函数
```

### 4. 类型提示问题

**现象**：
- `E999`：语法错误（通常是类型提示语法问题）

**解决方案**：
```bash
# 检查语法错误
cd services/<service> && ruff check --select E999 .

# 修复语法错误，确保使用正确的类型提示语法
# Python 3.11+: 使用 X | None 而非 Optional[X]
```

## 手动执行

```bash
# 检查单个服务
cd services/vote && ruff check .

# 检查所有服务
for service in services/*; do
  cd "$service" && ruff check . && cd ../..
done

# 检查 workers
cd workers && ruff check .

# 检查 tools
cd tools && ruff check .
```

## 升级路径

| 级别 | 处理方式 |
|------|----------|
| 自动修复即可 | 执行 `ruff fix .` |
| 需要手动修改 | 检查具体文件和行号，手动修复 |
| 规则误报 | 在 `pyproject.toml` 的 `[tool.ruff]` 中添加忽略规则 |
| 无法解决 | 联系 QA Agent 或 Backend Agent |

## 相关链接

- 规范文档：`.trae/rules/10-python-backend.md`
- Ruff 配置：`services/<service>/pyproject.toml`
- 门禁注册表：`docs/40-dev-loop/gate_registry.yaml`
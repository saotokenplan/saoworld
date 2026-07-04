# Runbook: Mypy Typecheck (G-STATIC-002)

> gate_id: G-STATIC-002
> gate_name: Mypy Typecheck
> gate_type: static
> owner: QA Agent

## 门禁概述

Mypy Typecheck 是项目的类型检查门禁，使用 Mypy 工具检查 Python 代码的类型安全性。

**触发条件**：
- 路径：`services/**`, `workers/**`
- 触发：`on_pr`

**执行命令**：
```bash
cd services/<service> && mypy app
```

**预期耗时**：90 秒

## 常见失败原因

### 1. 类型不匹配

**现象**：
- `error: Incompatible types in assignment`
- `error: Argument 1 to "xxx" has incompatible type`

**解决方案**：
```bash
# 查看详细错误信息
cd services/<service> && mypy app --show-traceback

# 修复方式：
# 1. 检查变量赋值的类型是否正确
# 2. 添加类型注解
# 3. 使用类型转换（如 int(), str()）
# 4. 使用类型提示（如 Union, Optional）
```

### 2. 未定义的属性或方法

**现象**：
- `error: "xxx" has no attribute "yyy"`
- `error: "xxx" has no attribute "yyy" (not accessed)`

**解决方案**：
```bash
# 查看详细错误信息
cd services/<service> && mypy app --show-traceback

# 修复方式：
# 1. 检查类定义，确保属性/方法已定义
# 2. 检查拼写错误
# 3. 添加类型提示（如 `@property`）
```

### 3. 忽略的类型检查

**现象**：
- `error: Unsupported dynamic typing`
- 使用了 `# type: ignore` 但未说明原因

**解决方案**：
```bash
# 检查所有忽略的类型检查
cd services/<service> && mypy app --warn-unused-ignores

# 修复方式：
# 1. 尽量移除 `# type: ignore`，添加正确的类型提示
# 2. 如果确实无法推断类型，使用 `# type: ignore[reason]` 说明原因
```

### 4. 循环依赖

**现象**：
- `error: Cannot find implementation or library stub for module`
- `error: Circular dependency detected`

**解决方案**：
```bash
# 查看导入链
cd services/<service> && mypy app --verbose

# 修复方式：
# 1. 将共用类型提取到独立模块
# 2. 使用字符串类型注解（如 `from __future__ import annotations`）
# 3. 调整导入顺序
```

### 5. SQLAlchemy 模型类型问题

**现象**：
- `error: Unexpected keyword argument "xxx" for "mapped_column"`

**解决方案**：
```bash
# 确保使用 SQLAlchemy 2.0 语法
# 使用 Mapped[...] 和 mapped_column 正确组合

# 示例：
# from sqlalchemy.orm import Mapped, mapped_column
# class MyModel(Base):
#     id: Mapped[int] = mapped_column(primary_key=True)
```

## 手动执行

```bash
# 检查单个服务
cd services/vote && mypy app

# 检查所有服务
for service in services/*; do
  cd "$service" && mypy app && cd ../..
done

# 检查 workers
cd workers && mypy .
```

## 升级路径

| 级别 | 处理方式 |
|------|----------|
| 简单类型错误 | 添加正确的类型注解 |
| 复杂类型问题 | 使用 `typing` 模块（Union, Optional, Any） |
| 第三方库类型缺失 | 添加 `types-xxx` 包或创建类型 stub |
| 无法解决 | 联系 QA Agent 或 Backend Agent |

## 相关链接

- 规范文档：`.trae/rules/10-python-backend.md`
- Mypy 配置：`services/<service>/pyproject.toml`
- 门禁注册表：`docs/40-dev-loop/gate_registry.yaml`
# Runbook: Ruff Lint (G-STATIC-001)

> gate_id: G-STATIC-001
> gate_name: Ruff Lint
> gate_type: static
> owner: QA Agent

## 1. 门禁概述

Ruff Lint 是项目的静态代码检查门禁，使用 Ruff 工具对 Python 代码进行风格、质量和潜在问题检查，确保代码符合项目编码规范。

**门禁基本信息**：
- **门禁名称**：Ruff Lint
- **门禁 ID**：G-STATIC-001
- **门禁类型**：static（静态检查）
- **负责人**：QA Agent

**触发条件**：
- 触发时机：`on_pr`（PR 提交时触发）
- 触发路径：`services/**`、`workers/**`、`tools/**`

**覆盖的风险类型**：
- `style`：代码风格风险（命名、格式、缩进等不规范）
- `regression`：代码质量回归风险（未使用导入、潜在 bug 等）

**执行命令**：
```bash
cd services/<service> && ruff check .
```

**预期耗时**：30 秒

**严重级别**：blocker（门禁失败将阻止 PR 合并）

---

## 2. 常见失败原因

以下按出现频率从高到低排序：

### 2.1 格式错误（最常见）

**现象**：
- `E501`：行长度超过 120 字符
- `E101`：缩进包含混合的制表符和空格
- `E302`：类或函数定义前缺少 2 个空行
- `E303`：空行数量超过预期
- `W291`：行尾存在空白字符
- `W293`：空白行包含空格或制表符

### 2.2 命名问题

**现象**：
- `N802`：函数名应使用 snake_case 风格
- `N803`：参数名应使用 snake_case 风格
- `N806`：变量名应使用 snake_case 风格
- `N815`：类属性应使用 snake_case 风格
- `E741`：模糊变量名（如 `l`、`O`、`I` 等易混淆单字母）
- `D100`：模块缺少 docstring
- `D103`：函数缺少 docstring

### 2.3 导入问题

**现象**：
- `F401`：导入模块但未使用
- `F403`：使用 `from x import *` 通配符导入
- `F405`：名称可能未定义（来自通配符导入）
- `E402`：模块级导入不在文件顶部
- `I001`：导入排序不符合规范（isort 规则）
- `I002`：导入分组不正确

### 2.4 类型注解缺失

**现象**：
- `ANN001`：函数参数缺少类型注解
- `ANN002`：函数返回值缺少类型注解
- `ANN003`：类方法第一个参数缺少类型注解（self/cls）
- `ANN101`：self 参数缺少类型注解
- `ANN206`：使用 `# type: ignore` 未指定具体错误码

### 2.5 循环导入

**现象**：
- `F821`：未定义的名称（可能由循环导入导致）
- 模块 A 导入模块 B，模块 B 又导入模块 A

### 2.6 其他常见问题

**现象**：
- `F841`：变量赋值后未使用
- `F632`：使用 `==` 比较 bool 值（应使用 `is True`/`is False`）
- `E711`：与 None 比较应使用 `is` 而非 `==`
- `E712`：与 True/False 比较应使用 `is` 而非 `==`
- `B006`：可变的默认参数（如 `def func(x=[])`）
- `B008`：函数调用作为默认参数

---

## 3. 解决方案

### 3.1 格式错误

**解决步骤**：

```bash
# 步骤1：运行 ruff 自动修复（可修复大部分格式问题）
cd services/<service> && ruff fix .

# 步骤2：检查剩余未修复的行长度问题
cd services/<service> && ruff check --select E501 .

# 步骤3：手动修复行长度超过 120 字符的行
# - 长字符串拆分多行
# - 长参数列表换行对齐
# - 长表达式提取为变量
```

**示例**：
```python
# 修复前
def calculate_total_price(items: list[Item], discount: float, tax_rate: float, shipping_fee: float) -> float:
    return sum(item.price * item.quantity for item in items) * (1 - discount) * (1 + tax_rate) + shipping_fee

# 修复后
def calculate_total_price(
    items: list[Item],
    discount: float,
    tax_rate: float,
    shipping_fee: float,
) -> float:
    base_price = sum(item.price * item.quantity for item in items)
    discounted_price = base_price * (1 - discount)
    price_with_tax = discounted_price * (1 + tax_rate)
    return price_with_tax + shipping_fee
```

### 3.2 命名问题

**解决步骤**：

```bash
# 步骤1：检查所有命名相关问题
cd services/<service> && ruff check --select N802,N803,N806,N815,E741 .

# 步骤2：使用全局搜索替换修改变量/函数名
# 注意：确保替换是安全的，避免误替换
```

**命名规范参考**：
| 类型 | 规范 | 正确示例 | 错误示例 |
|------|------|----------|----------|
| 函数/方法 | snake_case | `get_user_by_id` | `GetUserByID`, `getUserByID` |
| 变量 | snake_case | `user_name` | `UserName`, `userName` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT` | `maxRetryCount`, `MaxRetryCount` |
| 类名 | PascalCase | `UserService` | `user_service`, `USER_SERVICE` |

### 3.3 导入问题

**解决步骤**：

```bash
# 步骤1：自动移除未使用的导入并整理导入顺序
cd services/<service> && ruff fix --select F401,I001,I002 .

# 步骤2：检查剩余导入问题
cd services/<service> && ruff check --select F403,F405,E402 .

# 步骤3：手动修复
# - 替换通配符导入为明确导入
# - 将导入移到文件顶部
# - 按标准库、第三方库、本地模块分组
```

**导入排序规范**：
1. 标准库导入（如 `os`, `sys`, `datetime`）
2. 第三方库导入（如 `fastapi`, `sqlalchemy`, `pydantic`）
3. 本地项目导入（如 `app.core.config`, `app.domain.models`）

### 3.4 类型注解缺失

**解决步骤**：

```bash
# 步骤1：检查所有类型注解缺失问题
cd services/<service> && ruff check --select ANN .

# 步骤2：按文件逐个添加类型注解
# 从核心模块开始，逐步扩展
```

**常用类型注解示例**：
```python
from datetime import datetime
from typing import Any

# 基本类型
def greet(name: str) -> str:
    return f"Hello, {name}"

# 集合类型
def process_items(items: list[int]) -> dict[str, int]:
    result: dict[str, int] = {}
    for i, item in enumerate(items):
        result[f"item_{i}"] = item
    return result

# 可选类型
def get_user(user_id: str) -> User | None:
    return db.query(User).filter(User.id == user_id).first()

# 异步函数
async def fetch_data(url: str) -> dict[str, Any]:
    ...
```

### 3.5 循环导入

**解决步骤**：

```bash
# 步骤1：定位循环导入链
cd services/<service> && ruff check --verbose

# 步骤2：识别循环依赖关系
# 画出模块间的导入关系图

# 步骤3：解决方案（按优先级排序）
# 方案A：将共用类型提取到独立的 types 模块
# 方案B：使用 TYPE_CHECKING 延迟导入
# 方案C：重新组织模块结构，消除循环依赖
```

**使用 TYPE_CHECKING 示例**：
```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.user_service import UserService

class OrderService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service
```

### 3.6 其他常见问题

**未使用变量（F841）**：
```bash
# 移除未使用的变量，或使用下划线前缀表示有意不使用
result = some_function()  # 如果 result 未使用，改为:
_ = some_function()
```

**可变默认参数（B006）**：
```python
# 错误
def add_item(item: str, items: list[str] = []) -> list[str]:
    items.append(item)
    return items

# 正确
def add_item(item: str, items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    items.append(item)
    return items
```

---

## 4. 手动执行

### 4.1 单个服务检查

```bash
# 检查 vote 服务
cd services/vote && ruff check .

# 检查 world 服务
cd services/world && ruff check .

# 检查 content 服务
cd services/content && ruff check .
```

### 4.2 所有服务批量检查

```bash
# 在项目根目录执行
for service_dir in services/*/; do
    echo "Checking $service_dir..."
    cd "$service_dir" && ruff check . && cd ../..
done
```

### 4.3 检查其他目录

```bash
# 检查 workers 目录
cd workers && ruff check .

# 检查 tools 目录
cd tools && ruff check .
```

### 4.4 常用检查选项

```bash
# 只检查特定规则（如只检查导入问题）
cd services/vote && ruff check --select F401,I001 .

# 排除特定规则（如暂时忽略 docstring 要求）
cd services/vote && ruff check --ignore D100,D103 .

# 显示统计信息
cd services/vote && ruff check --statistics .

# 输出 JSON 格式（便于脚本处理）
cd services/vote && ruff check --output-format json .

# 自动修复所有可修复的问题
cd services/vote && ruff fix .

# 试运行自动修复（不实际修改文件）
cd services/vote && ruff fix --dry-run .
```

### 4.5 配置文件位置

每个服务的 Ruff 配置在对应目录的 `pyproject.toml` 中：
- 路径：`services/<service>/pyproject.toml`
- 配置段：`[tool.ruff]`

全局规范参考：`.trae/rules/10-python-backend.md`

---

## 5. 升级路径

### 5.1 问题分级处理

| 级别 | 问题类型 | 处理方式 | 预期解决时间 |
|------|----------|----------|--------------|
| L1 | 格式问题、简单导入问题 | 执行 `ruff fix .` 自动修复 | 5 分钟内 |
| L2 | 命名问题、简单类型注解缺失 | 手动修改，参考本 Runbook 第 3 节 | 30 分钟内 |
| L3 | 循环导入、复杂类型问题 | 分析依赖关系，重构代码结构 | 2 小时内 |
| L4 | 规则误报、配置问题 | 提交 issue，联系负责人 | 1 个工作日内 |

### 5.2 升级流程

```
问题出现
    ↓
尝试自动修复（ruff fix）
    ↓ 失败
查阅本 Runbook 常见原因与解决方案
    ↓ 仍无法解决
在团队频道咨询后端同事
    ↓ 仍无法解决
提交 Issue 并指派 QA Agent
    ↓
QA Agent 评估是否需要调整规则配置
    ↓
如需规则变更，更新 pyproject.toml 并提交 PR
```

### 5.3 联系人和职责

| 角色 | 负责人 | 职责范围 |
|------|--------|----------|
| 门禁负责人 | QA Agent | 规则配置、门禁策略、误报处理 |
| 技术支持 | Backend Agent | 代码重构、循环导入解决方案 |
| 最终审批 | 技术负责人 | 规则例外审批、重大配置变更 |

### 5.4 规则例外申请

如果确认某条规则不适用于特定场景，可申请例外：

1. 在代码中使用 `# noqa: <rule_code>` 忽略单行
2. 在 `pyproject.toml` 中添加全局忽略（需说明原因）
3. 提交 PR 并说明理由，由技术负责人审批

**示例 - 单行忽略**：
```python
result = some_complicated_function()  # noqa: F841 - 保留供后续使用
```

**示例 - 文件级忽略（在文件顶部）**：
```python
# ruff: noqa: D100 - 测试文件不需要模块 docstring
```

---

## 相关链接

- 规范文档：`.trae/rules/10-python-backend.md`
- Ruff 配置：`services/<service>/pyproject.toml`
- 门禁注册表：`docs/40-dev-loop/gate_registry.yaml`
- Ruff 官方文档：https://docs.astral.sh/ruff/

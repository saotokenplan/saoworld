# Runbook: Mypy Typecheck (G-STATIC-002)

> gate_id: G-STATIC-002
> gate_name: Mypy Typecheck
> gate_type: static
> owner: QA Agent

## 1. 门禁概述

Mypy Typecheck 是项目的类型检查门禁，使用 Mypy 静态类型检查器对 Python 代码进行类型安全验证，确保代码符合类型注解规范，提前发现潜在的类型相关 bug。

**门禁基本信息**：
- **门禁名称**：Mypy Typecheck
- **门禁 ID**：G-STATIC-002
- **门禁类型**：static（静态检查）
- **负责人**：QA Agent

**触发条件**：
- 触发时机：`on_pr`（PR 提交时触发）
- 触发路径：`services/**`、`workers/**`

**覆盖的风险类型**：
- `type-safety`：类型安全风险（类型不匹配、属性不存在、参数错误等）
- `regression`：代码质量回归风险（类型注解缺失、隐式类型转换等）

**执行命令**：
```bash
cd services/<service> && mypy app
```

**预期耗时**：90 秒

**严重级别**：blocker（门禁失败将阻止 PR 合并）

---

## 2. 常见失败原因

以下按出现频率从高到低排序：

### 2.1 类型不匹配（最常见）

**现象**：
- `error: Incompatible types in assignment (expression has type "X", variable has type "Y")`：赋值类型不匹配
- `error: Argument 1 to "xxx" has incompatible type "X"; expected "Y"`：函数参数类型不匹配
- `error: Return value expected "X", got "Y"`：返回值类型不匹配
- `error: Incompatible return value type`：返回值类型与声明不匹配
- `error: Incompatible types in "await"`：await 表达式类型不匹配

### 2.2 未定义的属性或方法

**现象**：
- `error: "X" has no attribute "y"`：对象没有指定属性
- `error: "X" has no attribute "y"  [attr-defined]`：属性未定义
- `error: Module has no attribute "X"`：模块没有指定属性
- `error: "X" not callable`：对象不可调用

### 2.3 导入问题

**现象**：
- `error: Cannot find implementation or library stub for module named "x"`：找不到模块的类型存根
- `error: Library stubs not installed for "x"`：缺少第三方库的类型存根
- `error: Module "x" does not explicitly export attribute "y"`：模块未明确导出属性
- `error: Name "x" is not defined`：名称未定义

### 2.4 类型注解缺失

**现象**：
- `error: Function is missing a type annotation`：函数缺少类型注解
- `error: Function parameter "x" is untyped`：函数参数缺少类型注解
- `error: Missing return type annotation`：缺少返回值类型注解
- `error: Call to untyped function "x" in typed context`：在类型化上下文中调用无类型函数

### 2.5 循环导入

**现象**：
- `error: Cannot resolve name "X" (possible cyclic import)`：可能存在循环导入
- `error: Module "x" has no attribute "y" (due to cycle)`：循环导入导致属性不可见
- 两个模块互相导入对方的类型

### 2.6 泛型和类型变量问题

**现象**：
- `error: Missing type parameters for generic type "X"`：泛型类型缺少类型参数
- `error: Type variable "T" is unbound`：类型变量未绑定
- `error: Argument of type "X" cannot be assigned to parameter "y" of type "T" in function "z"`：泛型参数不匹配

### 2.7 SQLAlchemy 模型类型问题

**现象**：
- `error: Unexpected keyword argument "x" for "mapped_column"`：mapped_column 参数错误
- `error: "Column[int]" has no attribute "x"`：Column 类型属性不存在
- `error: Incompatible types in assignment (expression has type "Column[X]", variable has type "X")`：ORM 类型不匹配
- `error: "Base" has no attribute "metadata"`：基类属性问题

---

## 3. 解决方案

### 3.1 类型不匹配

**解决步骤**：

```bash
# 步骤1：查看详细错误信息和上下文
cd services/<service> && mypy app --show-error-codes --show-error-context

# 步骤2：定位具体文件和行号
# 检查变量声明和赋值是否一致

# 步骤3：根据情况修复
# - 修改变量类型声明
# - 添加类型转换
# - 修改函数签名
```

**常见修复示例**：

```python
# 示例1：赋值类型不匹配
# 错误
user_id: int = "123"

# 正确
user_id: int = 123
# 或
user_id: str = "123"

# 示例2：函数参数类型不匹配
# 错误
def greet(name: str) -> str:
    return f"Hello, {name}"

greet(123)  # 传入 int 而非 str

# 正确
greet("Alice")
# 或修改函数接受多种类型
def greet(name: str | int) -> str:
    return f"Hello, {name}"

# 示例3：返回值类型不匹配
# 错误
def get_user(user_id: str) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    return user  # user 可能是 None

# 正确
def get_user(user_id: str) -> User | None:
    user = db.query(User).filter(User.id == user_id).first()
    return user
```

### 3.2 未定义的属性或方法

**解决步骤**：

```bash
# 步骤1：确认属性/方法是否真的存在
cd services/<service> && mypy app --show-error-codes

# 步骤2：检查拼写错误
# 注意 Python 大小写敏感

# 步骤3：检查类定义和导入
# 确保正确导入了类或模块
```

**常见修复示例**：

```python
# 示例1：属性拼写错误
# 错误
user = User()
user.usre_name = "Alice"  # usre_name 拼写错误

# 正确
user.user_name = "Alice"

# 示例2：动态添加的属性
# 错误
class User:
    def __init__(self, name: str):
        self.name = name

user = User("Alice")
user.age = 25  # 动态添加的属性 mypy 不知道

# 正确 - 在类中声明所有属性
class User:
    age: int | None

    def __init__(self, name: str):
        self.name = name
        self.age = None

# 或使用 dataclass
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int | None = None

# 示例3：使用 cast 或 type: ignore
from typing import cast

# 如果你确定类型正确但 mypy 推断不出来
obj: Any = get_dynamic_object()
user = cast(User, obj)  # 告诉 mypy 这是 User 类型
```

### 3.3 导入问题

**解决步骤**：

```bash
# 步骤1：检查是否缺少类型存根包
cd services/<service> && mypy app --ignore-missing-imports

# 步骤2：安装缺失的类型存根
# 常见的类型存包包名：types-requests, types-redis, types-PyYAML 等
pip install types-xxx

# 步骤3：如果第三方库没有类型存根，在配置中忽略
```

**常见修复示例**：

```python
# 示例1：安装类型存根
# 如果使用了 requests 库但缺少类型存根
pip install types-requests

# 示例2：在 pyproject.toml 中配置忽略缺少存根的模块
# [tool.mypy]
# ignore_missing_imports = true  # 全局忽略（不推荐）

# 或者针对特定模块忽略
# [[tool.mypy.overrides]]
# module = "redis.*"
# ignore_missing_imports = true

# 示例3：创建本地类型存根文件
# 在项目中创建 stubs/ 目录，添加 .pyi 文件
# stubs/redis/__init__.pyi

# 示例4：使用 TYPE_CHECKING 避免运行时导入
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.user_service import UserService

class OrderService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service
```

### 3.4 类型注解缺失

**解决步骤**：

```bash
# 步骤1：检查所有缺少类型注解的函数
cd services/<service> && mypy app --disallow-untyped-defs

# 步骤2：按优先级添加类型注解
# 从核心模块、公共 API 开始，逐步扩展
```

**常用类型注解模式**：

```python
# 基本函数
def add(a: int, b: int) -> int:
    return a + b

# 无返回值
def log(message: str) -> None:
    print(message)

# 可选参数
def greet(name: str, greeting: str = "Hello") -> str:
    return f"{greeting}, {name}!"

# 可变参数
def sum_all(*numbers: int) -> int:
    return sum(numbers)

# 关键字参数
def create_user(**kwargs: str) -> dict[str, str]:
    return kwargs

# 异步函数
async def fetch_user(user_id: str) -> User | None:
    ...

# 生成器
from typing import Generator

def generate_numbers(n: int) -> Generator[int, None, None]:
    for i in range(n):
        yield i

# 回调函数
from typing import Callable

def process_data(data: list[int], callback: Callable[[int], str]) -> list[str]:
    return [callback(item) for item in data]
```

### 3.5 循环导入

**解决步骤**：

```bash
# 步骤1：定位循环导入链
cd services/<service> && mypy app --verbose --show-traceback

# 步骤2：分析导入关系，找出循环
# 画出模块依赖图

# 步骤3：选择解决方案（按优先级排序）
# 方案A：提取共用类型到独立的 types 模块
# 方案B：使用 TYPE_CHECKING 和 forward references
# 方案C：重构模块结构，消除循环依赖
```

**方案 A：提取共用类型**

```python
# 原结构：
# models/user.py 导入 models/order.py
# models/order.py 导入 models/user.py

# 解决：创建 models/types.py，放共用类型
# models/types.py
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass  # 这里放基础类型定义

# 然后两个模块都从 types.py 导入
```

**方案 B：使用 TYPE_CHECKING**

```python
# models/user.py
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.order import Order

class User:
    orders: list[Order]

# models/order.py
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.user import User

class Order:
    user: User
```

### 3.6 泛型和类型变量问题

**解决步骤**：

```python
# 示例1：泛型类型缺少类型参数
# 错误
def process_items(items: list) -> None:  # list 缺少类型参数
    for item in items:
        print(item)

# 正确
def process_items(items: list[int]) -> None:
    for item in items:
        print(item)

# 如果类型不确定，使用 Any
from typing import Any

def process_items(items: list[Any]) -> None:
    for item in items:
        print(item)

# 示例2：使用 TypeVar
from typing import TypeVar

T = TypeVar("T")

def get_first(items: list[T]) -> T | None:
    if items:
        return items[0]
    return None

# 示例3：有界类型变量
from typing import TypeVar

NumberT = TypeVar("NumberT", int, float)

def add(a: NumberT, b: NumberT) -> NumberT:
    return a + b
```

### 3.7 SQLAlchemy 模型类型问题

**解决步骤**：

```bash
# 步骤1：确保使用 SQLAlchemy 2.0 风格的类型映射
# 参考 .trae/rules/10-python-backend.md 中的规范

# 步骤2：检查是否安装了 sqlalchemy[mypy] 插件
pip install sqlalchemy[mypy]
```

**正确的 SQLAlchemy 2.0 模型写法**：

```python
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_name: Mapped[str] = mapped_column(String(64), nullable=False)
    email: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # 可选字段使用 Optional 或 | None
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
```

**mypy 配置（pyproject.toml）**：

```toml
[tool.mypy]
python_version = "3.11"
strict = true

plugins = [
    "sqlalchemy.ext.mypy.plugin",
]

[tool.sqlalchemy_mypy]
enabled = true
```

---

## 4. 手动执行

### 4.1 单个服务检查

```bash
# 检查 vote 服务
cd services/vote && mypy app

# 检查 world 服务
cd services/world && mypy app

# 检查 content 服务
cd services/content && mypy app
```

### 4.2 所有服务批量检查

```bash
# 在项目根目录执行
for service_dir in services/*/; do
    echo "Checking $service_dir..."
    cd "$service_dir" && mypy app && cd ../..
done
```

### 4.3 检查 workers 目录

```bash
# 检查 workers 目录
cd workers && mypy .
```

### 4.4 常用检查选项

```bash
# 显示错误码（便于定位规则）
cd services/vote && mypy app --show-error-codes

# 显示错误上下文
cd services/vote && mypy app --show-error-context

# 更严格的检查
cd services/vote && mypy app --strict

# 忽略缺失的导入（用于调试）
cd services/vote && mypy app --ignore-missing-imports

# 警告未使用的 ignore 注释
cd services/vote && mypy app --warn-unused-ignores

# 生成 HTML 报告
cd services/vote && mypy app --html-report mypy_report

# 检查单个文件
cd services/vote && mypy app/api/routes.py

# 显示进度
cd services/vote && mypy app --verbose
```

### 4.5 增量检查（加快速度）

```bash
# mypy 支持增量检查，会缓存结果
# 默认启用，缓存目录在 .mypy_cache/

# 清除缓存并重新检查
cd services/vote && mypy app --no-incremental

# 使用不同的缓存目录
cd services/vote && mypy app --cache-dir /tmp/mypy_cache
```

### 4.6 配置文件位置

每个服务的 Mypy 配置在对应目录的 `pyproject.toml` 中：
- 路径：`services/<service>/pyproject.toml`
- 配置段：`[tool.mypy]`

全局规范参考：`.trae/rules/10-python-backend.md`

---

## 5. 升级路径

### 5.1 问题分级处理

| 级别 | 问题类型 | 处理方式 | 预期解决时间 |
|------|----------|----------|--------------|
| L1 | 简单类型不匹配、注解缺失 | 添加类型注解，修复明显的类型错误 | 15 分钟内 |
| L2 | 属性未定义、导入问题 | 检查类定义、安装类型存根、配置忽略 | 1 小时内 |
| L3 | 循环导入、复杂泛型问题 | 重构模块结构、使用 TYPE_CHECKING | 3 小时内 |
| L4 | 第三方库类型问题、工具 bug | 提交 issue，联系负责人评估 | 1 个工作日内 |

### 5.2 升级流程

```
问题出现
    ↓
查看错误信息，定位具体文件和行号
    ↓ 失败
查阅本 Runbook 常见原因与解决方案
    ↓ 仍无法解决
尝试添加类型注解或类型转换
    ↓ 仍无法解决
在团队频道咨询后端同事
    ↓ 仍无法解决
提交 Issue 并指派 QA Agent
    ↓
QA Agent 评估是否需要调整配置或规则
    ↓
如需配置变更，更新 pyproject.toml 并提交 PR
```

### 5.3 联系人和职责

| 角色 | 负责人 | 职责范围 |
|------|--------|----------|
| 门禁负责人 | QA Agent | 类型检查配置、门禁策略、误报处理 |
| 技术支持 | Backend Agent | 类型系统设计、循环导入解决方案 |
| 最终审批 | 技术负责人 | 规则例外审批、重大配置变更 |

### 5.4 类型检查例外申请

如果确认某段代码无法通过类型检查（如动态特性、第三方库限制），可申请例外：

**方式 1：单行忽略（推荐）**
```python
result = some_dynamic_function()  # type: ignore[attr-defined] - 动态属性，运行时存在
```

**方式 2：代码块忽略**
```python
# mypy: disable-error-code="attr-defined"
# 这里的代码块都忽略属性未定义错误
dynamic_object.attr = value
# mypy: enable-error-code="attr-defined"
```

**方式 3：文件级忽略（在文件顶部）**
```python
# mypy: ignore-errors
# 整个文件忽略类型检查（不推荐，尽量少用）
```

**方式 4：配置级忽略（pyproject.toml）**
```toml
[[tool.mypy.overrides]]
module = "app.dynamic_modules.*"
ignore_errors = true
```

**申请流程**：
1. 优先使用 `# type: ignore[error-code]` 并说明原因
2. 如果需要配置级忽略，提交 PR 并说明理由
3. 由技术负责人审批

---

## 相关链接

- 规范文档：`.trae/rules/10-python-backend.md`
- Mypy 配置：`services/<service>/pyproject.toml`
- 门禁注册表：`docs/40-dev-loop/gate_registry.yaml`
- Mypy 官方文档：https://mypy.readthedocs.io/
- Python 类型检查指南：https://typing.readthedocs.io/

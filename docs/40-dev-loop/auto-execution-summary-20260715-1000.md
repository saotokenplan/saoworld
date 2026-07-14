# 执行摘要：mypy 类型检查门禁补全

> 任务标识：auto-20260715-1000
> 执行时间：2026-07-15 10:00
> 工作分支：auto/auto-20260715-1000
> 任务状态：已完成

## 一、任务背景

上一轮全量验证（auto-20260715-0900）中，mypy 类型检查因「环境限制，暂跳过」未执行，遗留一个 P1 级质量缺口。`10-python-backend.md` 规范要求 mypy >= 1.10 作为类型检查门禁，CI 配置已将 mypy 设为阻塞门禁（移除了 `|| true` 绕过），但本地验证不完整。

本轮任务目标：为全部 8 个后端服务安装 dev 依赖，运行 mypy 收集并修复所有类型错误，使 mypy 类型检查门禁真正生效，为灰度发布提供额外质量保障。

## 二、完成的工作

### 1. 安装 dev 依赖并收集 mypy 错误

- 为全部 8 个后端服务安装 dev 依赖（mypy、ruff、pytest 等）
- 运行 mypy 收集到 **46 个类型错误**，跨 7 个服务（content-service 无错误）

### 2. 修复 tracing.py 类型错误（6 个服务）

world/generation/review/player/ops/gateway 6 个服务的 `app/core/tracing.py` 存在相同的 `Returning Any from function declared to return "Response"` 错误，原因是 `call_next: Callable` 参数未标注完整签名。

修复方式：
- 添加 `Awaitable` 导入
- 将 `call_next: Callable` 改为 `call_next: Callable[[Request], Awaitable[Response]]`

### 3. 修复 ops-service 类型错误（23 个错误）

**3.1 `raise_ops_error` 返回类型修复（修复 7 个 union-attr 错误）**

`app/core/errors.py` 中 `raise_ops_error` 函数返回类型为 `-> None`，mypy 无法识别其后 `event` 为 `None` 的分支不可达，导致 7 个 union-attr 错误。

修复：将返回类型改为 `-> NoReturn`，并添加 `from typing import NoReturn` 导入。

**3.2 服务客户端 `resp.json()` 返回类型修复（修复 15 个 no-any-return 错误）**

`vote_service_client.py`、`review_service_client.py`、`content_service_client.py` 三个客户端共 15 处 `return resp.json()`，httpx 的 `resp.json()` 返回 `Any`，触发 no-any-return 错误。

修复：添加 `from typing import cast`，将所有 `return resp.json()` 改为 `return cast(dict, resp.json())`。

**3.3 tracing.py 同步修复**（同上）

### 4. 修复其他服务类型错误

**4.1 vote-service vote_repo.py（修复 4 个错误）**

- `row.count` 类型被推断为 `Callable[[Any], int]`，使用 `cast(int, row.count)` 包装
- 排序键 `x["weighted_score"]` 返回 `object` 类型，使用 `cast(float, x["weighted_score"])` 包装

**4.2 world-service routes.py（修复 12 个错误）**

- `ItemResponse(**item_dict)` 解包触发 arg-type 错误，改用 `ItemResponse.model_validate(item_dict)` 进行 ORM 风格转换
- `PaginatedMeta(...).model_dump()` 返回 `dict[str, Any]` 而非 `PaginatedMeta | None`，移除 `.model_dump()` 直接传递模型实例

**4.3 generation-service item_data_adapter.py（修复 1 个错误）**

- `defaults = {...}` 字面量缺少类型注解，改为 `defaults: dict[str, Any] = {...}`

**4.4 player-service guild_repo.py（修复 1 个错误）**

- `GuildMember.__table__.delete()` 访问低层 FromClause 触发 `attr-defined` 错误，改用 SQLAlchemy 2.0 的 `delete(GuildMember).where(...)` 构造

## 三、验证结果

### mypy 类型检查

全部 8 个后端服务 mypy 检查通过，**0 错误**（修复前 46 错误）：

| 服务 | 修复前 | 修复后 |
|------|--------|--------|
| vote-service | 4 | 0 |
| world-service | 13 | 0 |
| content-service | 0 | 0 |
| generation-service | 2 | 0 |
| review-service | 1 | 0 |
| player-service | 1 | 0 |
| ops-service | 23 | 0 |
| gateway-service | 1 | 0 |
| **合计** | **46** | **0** |

### ruff 代码质量检查

全部 8 个后端服务 ruff 检查通过。

### 测试回归验证

全部 8 个后端服务测试通过，**913 个测试无回归**：

| 服务 | 测试数量 | 状态 |
|------|---------|------|
| vote-service | 112 | ✅ 全部通过 |
| world-service | 120 | ✅ 全部通过 |
| content-service | 67 | ✅ 全部通过 |
| generation-service | 228 | ✅ 全部通过 |
| review-service | 41 | ✅ 全部通过 |
| player-service | 202 | ✅ 全部通过 |
| ops-service | 106 | ✅ 全部通过 |
| gateway-service | 37 | ✅ 全部通过 |
| **合计** | **913** | **✅ 100% 通过** |

## 四、修改的文件清单

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `services/world/app/core/tracing.py` | 修改 | call_next 类型注解：`Callable[[Request], Awaitable[Response]]` |
| `services/generation/app/core/tracing.py` | 修改 | 同上 |
| `services/review/app/core/tracing.py` | 修改 | 同上 |
| `services/player/app/core/tracing.py` | 修改 | 同上 |
| `services/ops/app/core/tracing.py` | 修改 | 同上 |
| `services/gateway/app/core/tracing.py` | 修改 | 同上 |
| `services/ops/app/core/errors.py` | 修改 | `raise_ops_error` 返回类型改为 `NoReturn` |
| `services/ops/app/core/vote_service_client.py` | 修改 | `resp.json()` 添加 `cast(dict, ...)` |
| `services/ops/app/core/review_service_client.py` | 修改 | 同上 |
| `services/ops/app/core/content_service_client.py` | 修改 | 同上 |
| `services/vote/app/repositories/vote_repo.py` | 修改 | 排序键 `cast(int, ...)` / `cast(float, ...)` |
| `services/world/app/api/routes.py` | 修改 | `ItemResponse.model_validate` + `PaginatedMeta` 直接传递 |
| `services/generation/app/core/item_data_adapter.py` | 修改 | `defaults: dict[str, Any]` 类型注解 |
| `services/player/app/repositories/guild_repo.py` | 修改 | `delete(GuildMember)` 替代 `__table__.delete()` |
| `docs/40-dev-loop/auto-plan-20260715-1000.md` | 新建 | 工作计划文档 |
| `docs/40-dev-loop/auto-execution-summary-20260715-1000.md` | 新建 | 执行摘要（本文件） |
| `docs/40-dev-loop/auto-progress-log.md` | 修改 | 新增本轮执行记录 |
| `docs/00-governance/project-status.md` | 修改 | 记录 mypy 修复结果，标记 52-58 项为已完成 |

**总计：18 个文件（2 新建 + 16 修改，其中 14 个代码文件 + 4 个文档文件）**

## 五、遗留问题与下一步建议

### 遗留问题

1. **Godot 客户端 GUT 测试**：因引擎未安装无法执行，与本轮任务无关
2. **workers 集成测试**：需后端服务启动才能完整验证，与本轮任务无关
3. **mypy 严格度**：当前 mypy 配置未启用 `strict` 模式，部分类型错误可能未触发。后续可考虑逐步收紧 mypy 严格度

### 下一步建议

1. **启动灰度发布**：mypy 类型检查门禁已补全，项目所有质量门禁（ruff + mypy + pytest）全部通过，建议由运营团队决策启动首期内容包灰度发布流程
2. **验证线上效果**：观察灰度期间的关键指标（投票参与率、任务完成率、区域到达率、异常率）
3. **持续监控**：通过 Prometheus/Grafana 监控系统状态和业务指标
4. **mypy 严格度提升**（可选）：在灰度稳定后可考虑逐步启用 `disallow_untyped_defs`、`warn_return_any` 等严格选项

## 六、合并结果

- **合并状态**：待合并（详见后续更新）
- **工作分支**：auto/auto-20260715-1000
- **合并方式**：--no-ff

## 七、结论

本轮 mypy 类型检查门禁补全完成。修复 46 个类型错误，覆盖 7 个服务的 14 个代码文件，遵循以下修复模式：

1. **Callable 参数完整签名标注**：`Callable[[Request], Awaitable[Response]]`
2. **NoReturn 返回类型**：用于会抛出异常的函数，帮助 mypy 识别不可达分支
3. **cast 类型包装**：用于第三方库返回 Any 的场景（如 httpx `resp.json()`、SQLAlchemy `row.count`）
4. **model_validate 替代 ** 解包**：Pydantic v2 推荐的 ORM 风格转换
5. **SQLAlchemy 2.0 delete() 构造**：替代低层 `__table__.delete()` 访问

修复后所有质量门禁通过（ruff + mypy + pytest），项目持续保持**灰度发布就绪状态**。

---

*本摘要由自动化推进任务自动生成*

# 执行摘要：auto-20260726-0000（WP2 DuplicateDetectionRule 死参数接线）

> 任务标识：auto-20260726-0000
> 工作分支：auto/auto-20260726-0000
> 合并目标：feature-prd
> 执行时间：2026-07-26 00:00
> 关联工作包：M4-WP2 自动审核规则调优（实施期改造前置项）

## 一、本轮结论

M4 实施期 WP2 推进的首个可自主落地代码项已完成：`services/review` 的 `DuplicateDetectionRule.max_similarity=0.8` 死参数（M4 阈值调优预案第二节「已发现死参数」显式登记）**已接线为单对象自相似度阈值，默认值 0.8 正式生效**；同时补充 `self_similarity` / `cross_similarity`（字符级 Jaccard）两个纯函数，为 WP2 场景 D 的跨样本相似度接线提供可单测基础。WP2 由此进入实施期。

## 二、关键改动

### 代码（services/review/app/core/auto_review_engine.py）
- `DuplicateDetectionRule.evaluate`：移除硬编码 `diversity_ratio < 0.3` 常量，改为以 `1 - 字符多样度` 近似「自相似度」，当 `self_similarity >= max_similarity` 时判 `rejected`（默认 0.8 → 自相似度 ≥0.8 拦截）。
- 新增静态纯函数：
  - `self_similarity(description)`：单对象内自相似度，空串返回 0.0，对 `str()` 输入安全。
  - `cross_similarity(a, b)`：字符级 Jaccard 相似度（跨样本重复检测基础），空串操作数返回 0.0。
- 构造函数默认值保持 0.8，与 M4 阈值调优预案登记一致。

### 测试（services/review/tests/test_duplicate_detection_rule.py，新增）
- 14 个用例：自相似度受控数值（"aaaa"=0.75、"abab"=0.5、"a"=0.0、空串=0.0、非字符串 coercion）、跨样本 Jaccard 数值（相同=1.0、不相交=0.0、部分重叠=0.5、空串=0.0）、短描述跳过、高重复拦截、多样长文本通过、**参数真正被使用**（放宽阈值到 0.99 即不拦截）、默认值 0.8。

### 测试基础设施修复（services/review/pyproject.toml）
- `dev` extras 缺少 `greenlet`：SQLAlchemy 异步引擎（`sqlalchemy[asyncio]`）运行需 `greenlet`，但项目仅声明 `sqlalchemy>=2.0.0`，导致 review 测试套件在 `setup_db` 夹具连接 in-memory sqlite 时抛 `ValueError: the greenlet library is required`。本轮补加 `greenlet>=3.0.0` 到 dev extras，使 `pip install -e ".[dev]"` 后测试可运行。

### 文档
- `docs/10-requirements/M4-阈值调优预案.md`：死参数行状态回填为「已接线（2026-07-26, auto-20260726-0000）」，补充接线范围与不做调优说明。
- `docs/00-governance/project-status.md`：当前阶段补充 WP2 首个代码项落地；当前待办 WP2 由「未开始」改为「进行中」，WP3–WP5 保持未开始。

## 三、验证结果

- review venv（Python 3.13）下运行 `pytest tests/`：**79 passed**（含新增 14 例），无回归。
- ruff：变更文件 `auto_review_engine.py` / `test_duplicate_detection_rule.py` 中本次新增代码（DuplicateDetectionRule 块）无新增 lint 问题；文件内其余 5 处 ruff 提示（RUF012×3 / SIM114 / BLE001）均为既有代码，非本轮引入。
- 不依赖真实运行时即可完成验证（规则逻辑仅用标准库）。

## 四、范围与边界（明确不做）

- **不做数值调优**：规划期与预案明确禁止在无真实样本回放前提下降/升 `max_similarity`；本轮仅将其接线为登记的默认 0.8。
- **不接入跨样本语料**：WP2 场景 D 完整跨样本相似度接线需 PostgreSQL 运行时中的既有对象集合，留待运行时验证阶段；本轮仅补齐 `cross_similarity` 纯函数与单对象阈值接线。
- **未改动安全边界**：敏感词/高风险词一票否决、规则短路顺序等不可调项未触碰。

## 五、提交与合并

- 主题拆分提交：`feat(review)`（接线 + 纯函数）/ `test(review)`（新增测试）/ `fix(review)`（greenlet dev extras）/ `docs(requirements)`（阈值调优预案回填）/ `docs(docs)`（project-status 更新）/ `docs(dev-loop)`（计划 + 摘要 + 进度日志）。
- 工作分支提交均推送 `origin/auto/auto-20260726-0000`。
- `--no-ff` 合并回 `origin/feature-prd`（合并提交类型随代码 payload 用 `feat(review)`），fetch 校验通过后删除本地工作分支。

## 六、下一步建议

- WP2 后续：在真实样本（sampleset_v2）回放脚本就绪后，按阈值调优预案闭环做数值调优；并择机将 `cross_similarity` 接线进引擎（注入同章节既有 description 语料）。
- WP3–WP5 仍按序未开始，其中 WP3 指标埋点（M1–M6 缺口）部分可自主落地，待下一轮评估。

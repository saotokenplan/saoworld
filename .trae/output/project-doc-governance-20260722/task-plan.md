# 整仓文档治理任务规划

> 任务名称：对整个项目进行文档治理
> 任务状态：completed
> 规划日期：2026-07-22
> 执行状态：已完成实施与复查

## 1. 任务目标

本轮任务用于对整个项目执行一次整仓级文档治理，目标不是继续扩写文档，而是完成以下四类治理收口：

- 统一 `docs/` 内部的分层、入口、命名和权威边界
- 统一仓库根入口、`quick-start`、项目状态页对仓库现状的口径
- 将 `tools/README.md`、`services/README.md` 及服务 README 纳入文档治理闭环
- 修复 docs 外代码与测试中已经漂移或失效的文档路径引用

## 2. 当前判断

根据已完成扫描，当前主要问题集中在以下几类：

1. **仓库现状口径冲突**
   - 根 `README.md` 与 `docs/00-governance/project-status.md` 的项目阶段描述不一致
   - `docs/00-governance/quick-start.md` 仍保留“尚无 `game/`、`services/`、`workers/`”等过期表述
2. **文档治理边界只覆盖 `docs/`，未覆盖根入口与 README 族群**
   - `.trae/rules/52-documentation.md` 当前未把根 `README.md`、`tools/README.md`、`services/README.md` 纳入同步检查范围
3. **`docs/` 深层目录入口仍不完整**
   - `docs/40-dev-loop` 下多处深层目录仍缺局部 `README.md`
   - 自动归档目录存在可读性断层
4. **外部代码和测试中存在坏路径**
   - `tools/perf_test/threshold.py` 仍引用旧的专题包目录写法
   - `tools/agents/ops_agent/tests/test_ops_agent.py` 仍引用已过时的历史报告目录写法
5. **专题化再包装目录存在双写风险**
   - `docs/10-requirements/packages/first-slice/` 已收瘦，但仍需防止回到“第二套规范”

## 3. 治理原则

- **权威单源**：执行规范以 `docs/20-specs/` 为准，其他层只做导航、背景、摘要或流程说明
- **入口收口**：每一层只保留清晰入口，避免多个文档争夺同一角色
- **最小必要修改**：优先修复口径冲突、坏路径和阅读断点，不进行无必要的大规模改写
- **文档外同步**：README、工具说明、测试引用也视为文档治理范围的一部分
- **可回滚**：优先做可审查、可拆分、可单独回退的修改
- **归档保留优先**：历史自动产物优先保留审计价值，仅在明显影响检索和阅读时做小范围路径修正

## 4. 本轮范围

### 4.1 明确纳入范围

- `docs/README.md`
- `docs/00-governance/`
- `docs/10-requirements/`
- `docs/40-dev-loop/`
- `.trae/rules/52-documentation.md`
- 根 `README.md`
- `tools/README.md`
- `services/README.md`
- `services/*/README.md`
- `tools/perf_test/threshold.py`
- `tools/agents/ops_agent/tests/test_ops_agent.py`

### 4.2 本轮不做

- 不对 `docs/20-specs/` 做大规模内容重写
- 不引入新的治理层级或新增一级目录
- 不批量重命名大范围历史文件
- 不顺带改动与文档治理无关的业务逻辑

## 5. 六阶段执行方案

### 阶段 1：治理基线确认

目标：确认本轮治理的权威关系、目标文件集、同步范围和风险边界。

输出：

- 最终任务规划
- 最终验收清单
- 执行批次划分

### 阶段 2：`docs/` 体系入口与分层收口

目标：继续收紧 `docs/` 内部入口和职责边界，避免总入口、项目状态页、专题包和过程层互相越界。

重点动作：

- 复查 `docs/README.md` 与 `document-map.md` 是否准确反映当前体系
- 为缺失的深层目录补齐局部 `README.md`
- 统一 `40-dev-loop` 深层目录的阅读入口
- 为 `first-slice` 再包装目录补强“非权威、回指源规范”提示

### 阶段 3：根入口与项目现状口径统一

目标：让根 `README.md`、`quick-start.md`、`project-status.md` 对仓库当前状态给出一致描述。

重点动作：

- 修正“当前仓库不是工程仓库”的过期口径
- 同步仓库已存在 `game/`、`services/`、`workers/` 等事实
- 统一“阅读入口 / 项目现状 / 实施基线”的表达顺序

### 阶段 4：README 族群治理纳入规则闭环

目标：把 docs 外关键 README 纳入同一套治理机制，减少未来再次失同步。

重点动作：

- 更新 `.trae/rules/52-documentation.md`
- 明确根 `README.md`、`tools/README.md`、`services/README.md` 的同步职责
- 收口 `services/*/README.md` 与 `docs/20-specs/`、`docs/30-api/` 的关系说明

### 阶段 5：文档路径引用修复

目标：修复工具、测试和说明文本中已失效的 docs 路径，恢复引用可用性。

重点动作：

- 修复 `tools/perf_test/threshold.py` 的旧路径
- 修复 `tools/agents/ops_agent/tests/test_ops_agent.py` 的旧路径
- 视扫描结果补修其他明显漂移的路径引用

### 阶段 6：终验、同步与回滚说明

目标：完成全局复查，确认入口一致、引用可用、阅读路径清晰，并记录回滚点。

重点动作：

- 复查受影响 README、治理文档和代码引用
- 检查是否引入新的失效链接或描述冲突
- 记录本轮治理的回滚最小单元

## 6. 执行批次建议

为控制单轮产出规模，本轮实施按 4 个批次执行：

1. `docs/` 内治理入口与局部 README
2. 根入口与治理规则同步
3. `tools/README.md`、`services/README.md` 与服务 README 同步
4. 代码/测试中的 docs 路径修复与终验

## 7. 风险与应对

### 风险 1：现状口径修正影响多个入口

应对：

- 统一以 `docs/00-governance/project-status.md` 的最新阶段判断为事实基线
- 在根入口文档中只做摘要表达，不复制完整状态内容

### 风险 2：README 族群同步范围扩大

应对：

- 只纳入关键 README，不一次性扩展到全仓所有说明文件
- 通过规则文档明确“哪些 README 必须同步检查”

### 风险 3：代码中的 docs 路径修复引发测试快照变化

应对：

- 仅修复路径常量和断言文本
- 如测试依赖路径存在性，补做定向验证

### 风险 4：历史再包装目录回潮

应对：

- 在 `first-slice` 目录继续强化“摘要层 / 阅读包 / 非权威”定位
- 避免再次把规范正文回填到专题包中

## 8. 需要重点关注的文件

- `README.md`
- `docs/README.md`
- `docs/00-governance/quick-start.md`
- `docs/00-governance/project-status.md`
- `docs/00-governance/document-map.md`
- `.trae/rules/52-documentation.md`
- `tools/README.md`
- `services/README.md`
- `services/vote/README.md`
- `tools/perf_test/threshold.py`
- `tools/agents/ops_agent/tests/test_ops_agent.py`

## 9. 完成定义

本轮整仓文档治理完成，需同时满足以下条件：

- `docs/` 总入口、治理入口、项目状态页、快速开始页不再互相冲突
- 根 `README.md`、`tools/README.md`、`services/README.md` 被纳入治理同步链路
- 深层目录的主要阅读断点已补齐局部 `README.md`
- 外部代码与测试中的典型失效 docs 路径已修复
- 本轮修改具备清晰回滚边界与复查结果

## 10. 执行门槛

本计划已按既定范围执行完成，相关结果以下列文件和循环日志为准：

- `.trae/output/project-doc-governance-20260722/checklist.md`
- `.trae/loop-log/round-1.md`
- `.trae/loop-log/round-2.md`
- `.trae/loop-log/round-3.md`

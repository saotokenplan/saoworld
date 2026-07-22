# 整仓文档治理验收清单

> 任务名称：对整个项目进行文档治理
> 清单状态：draft
> 日期：2026-07-22
> 使用方式：用户确认规划后，执行阶段逐项勾选

## A. 规划与边界

- [ ] 已确认本轮以“文档治理”为主，不夹带无关功能开发
- [ ] 已确认执行规范仍以 `docs/20-specs/` 为最高基线
- [ ] 已确认本轮纳入范围包含 `docs/`、根 `README`、`tools/README`、`services/README` 和典型坏路径修复
- [ ] 已确认本轮不做大规模历史文档重写和全仓文件重命名

## B. `docs/` 总入口与治理层

- [ ] `docs/README.md` 的目录说明与当前仓库实际结构一致
- [ ] `docs/README.md` 的阅读顺序未与 `quick-start.md` 冲突
- [ ] `docs/00-governance/document-map.md` 的权威关系与当前治理口径一致
- [ ] `docs/00-governance/project-status.md` 继续只承担项目级主状态页角色
- [ ] `docs/00-governance/quick-start.md` 已移除明显过期的仓库现状表述
- [ ] `docs/00-governance/quick-start.md` 的“最小实施顺序”与当前仓库阶段一致

## C. `docs/` 深层目录入口

- [ ] `docs/40-dev-loop/runbooks/gates/` 已具备局部入口或明确阅读说明
- [ ] `docs/40-dev-loop/runbooks/operations/` 已具备局部入口或明确阅读说明
- [ ] `docs/40-dev-loop/p2-agent-design/` 已具备局部入口或明确阅读说明
- [ ] `docs/40-dev-loop/player-guide/` 已具备局部入口或明确阅读说明
- [ ] `docs/40-dev-loop/archives/auto-generated/2026-07/plan/` 已具备局部入口或明确阅读说明
- [ ] `docs/40-dev-loop/archives/auto-generated/2026-07/execution/` 已具备局部入口或明确阅读说明
- [ ] `docs/40-dev-loop/archives/auto-generated/2026-07/status/` 已具备局部入口或明确阅读说明
- [ ] `docs/40-dev-loop/archives/auto-generated/2026-07/analysis/` 已具备局部入口或明确阅读说明
- [ ] `docs/10-requirements/packages/first-slice/` 继续明确为专题阅读包而非第二套规范

## D. 根入口与 README 族群

- [ ] 根 `README.md` 已改为反映当前真实仓库状态
- [ ] 根 `README.md` 与 `project-status.md` 对“项目阶段”表达一致
- [ ] 根 `README.md` 与 `docs/README.md` 的入口职责分工清晰
- [ ] `tools/README.md` 已说明其与 `docs/40-dev-loop/`、`docs/20-specs/` 的关系
- [ ] `services/README.md` 已从“planned” 更新为当前服务现状说明
- [ ] 至少一个关键服务 README 已补强与 `docs/20-specs/` / `docs/30-api/` 的回链说明

## E. 规则与同步机制

- [ ] `.trae/rules/52-documentation.md` 已纳入根 `README.md` 的同步检查要求
- [ ] `.trae/rules/52-documentation.md` 已纳入 `tools/README.md` 的同步检查要求
- [ ] `.trae/rules/52-documentation.md` 已纳入 `services/README.md` 的同步检查要求
- [ ] `.trae/rules/52-documentation.md` 对 README 族群的职责边界表述清晰

## F. 坏路径与外部引用

- [ ] `tools/perf_test/threshold.py` 中的旧 docs 路径已修复
- [ ] `tools/agents/ops_agent/tests/test_ops_agent.py` 中的旧 docs 路径已修复
- [ ] 本轮触达的活文件中不存在明显残留的专题包旧路径或旧报告目录路径

## G. 终验与回滚

- [ ] 已完成受影响 Markdown 文档的交叉复读，未发现新的口径冲突
- [ ] 已对受影响代码文件做定向检查，未引入明显语法或断言错误
- [ ] 已记录本轮变更的最小回滚单元
- [ ] 已准备好向用户汇报“已完成项 / 未完成项 / 残留风险”

## H. 执行门槛

- [ ] 用户已明确确认本清单与对应 `task-plan.md`
- [ ] 未获确认前，不进入实际实施阶段

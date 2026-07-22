# P2 Agent 设计入口

> 文档状态：active
> 适用阶段：专题查阅
> 维护要求：持续维护

## 目的

本目录用于收纳 P2 多代理协同阶段的角色设计资料，帮助读者快速理解不同 Agent 的职责、输入输出边界和协作关系。

## 当前定位

- 本目录属于 `docs/40-dev-loop/` 下的专题设计材料。
- 本目录偏角色设计与阶段性方法资料，不替代 `docs/20-specs/agent-loop-spec.md` 的执行约束。
- 角色定义若与当前实现或规则冲突，以最新 spec、规则和工具实现为准。

## 阅读建议

1. 先读 `orchestrator-spec.md` 理解统一调度角色。
2. 再按职能阅读 `backend`、`gameplay`、`world`、`qa`、`ops` 等 Agent 说明。
3. 需要判断正式约束时，回到 `docs/20-specs/agent-loop-spec.md`。

## 与其他文档的关系

- `docs/40-dev-loop/README.md`
  - 研发闭环总入口
- `docs/20-specs/agent-loop-spec.md`
  - Agent 约束与执行基线
- `tools/README.md`
  - 工具侧 Agent 模块入口

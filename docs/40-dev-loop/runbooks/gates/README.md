# 门禁 Runbook 入口

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本目录用于集中存放各类门禁（Gate）的排障 Runbook，帮助研发和自动化流程在 CI 或本地校验失败时快速定位问题、执行修复并完成复验。

## 当前定位

- 本目录是 `docs/40-dev-loop/runbooks/` 下的门禁排障子目录。
- 本目录只回答“某个 gate 失败时该怎么查、怎么修、怎么复验”，不重新定义门禁规则本身。
- 门禁注册与正式约束以 `docs/40-dev-loop/gate_registry.yaml`、`docs/20-specs/` 和 `.trae/rules/` 为准。

## 使用建议

1. 先根据失败日志中的 gate 名称或场景关键词定位对应文档。
2. 按文档中的常见失败原因、手动执行命令和修复步骤排查。
3. 修复后重新运行对应门禁，再回到上游规范确认是否存在规则变更。

## 与其他文档的关系

- `docs/40-dev-loop/runbooks/README.md`
  - Runbook 总入口
- `docs/40-dev-loop/gate_registry.yaml`
  - 门禁注册表和 gate 标识来源
- `docs/20-specs/`
  - 提供正式执行基线

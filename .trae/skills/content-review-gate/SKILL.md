# content-review-gate

## 目标

对生成内容进行结构化审核，判断其是否满足世界一致性、数值边界、内容安全和重复度要求，并输出可执行的审核结论。

## 适用场景

- 世界内容生成后进入上线前审核
- 新模板首次启用
- 关键阵营、关键角色、高风险事件相关内容需要复核

## 规范来源

- 主要来源：
  - `docs/20-specs/content-generation-spec.md`
  - `docs/20-specs/product-spec.md`
- 次要来源：
  - `docs/20-specs/agent-loop-spec.md`
  - `docs/20-specs/backend-data-spec.md`
  - `docs/30-api/openapi-draft.md`
- 说明：
  - 审核对象结构、模板边界和生命周期以 `content-generation-spec.md` 为准
  - 世界一致性、主线骨架和内容边界以 `product-spec.md` 为准
  - 门禁闭环和审核治理流程参考 `agent-loop-spec.md`
  - 审核记录字段和状态迁移参考 `backend-data-spec.md`
  - 审核结果对外暴露的审批接口和状态收敛参考 `openapi-draft.md`

## 输入

- 生成对象集合
- 世界骨架快照
- 规则版本
- 模板版本
- 当前章节和区域边界

## 输出

- `review-report.md`
- `approved.json`
- `rejected.json`
- `manual-review.json`
- 涉及审核审批接口调整时同步更新 `docs/30-api/openapi-draft.md`

## 审核维度

### 世界一致性

- 阵营关系是否冲突
- NPC 身份是否越界
- 聚落资源与地貌是否匹配
- 事件是否影响固定主线骨架

### 数值与经济

- 奖励是否超上限
- 敌人强度是否越区
- 资源刷新与支线收益是否可能破坏经济

### 内容安全

- 是否命中敏感词
- 是否出现高风险主题误用
- 是否超出目标年龄层表达边界

### 重复度与质量

- NPC 是否与历史角色过于相似
- 支线结构是否过度复用
- 文案是否明显重复或失真

## 结论类型

- `approve`
- `reject`
- `manual_review`

## 规则

- 任何高风险安全问题直接 `reject`
- 任何主线骨架冲突直接 `reject`
- 质量分过低直接 `reject`
- 新模板首次上线默认进入 `manual_review`

## 输出要求

每条审核记录至少包含：

- `object_id`
- `object_type`
- `review_result`
- `risk_level`
- `rule_version`
- `reasons`
- `suggested_fix`

## 硬约束

- 不直接修改原始生成对象
- 不绕过审核直接改变对象状态为可发布
- 不使用“整体感觉可以”这类主观判断代替结构化结论
- 若审核审批接口、状态枚举或返回字段变化，必须同步更新 OpenAPI 草案入口

## 不该做的事

- 不负责打包和发布
- 不负责重写整份内容，只指出驳回原因和修复方向

## 提交规范

所有代码和文档提交必须遵守 `docs/20-specs/engineering-conventions.md#git-提交规范` 和 `docs/20-specs/agent-loop-spec.md#ai-提交前自检清单强制执行`。

### 提交格式

`<type>(<scope>): <summary>`

- type: docs / feat / fix / refactor / test / chore
- summary: 使用祈使句（新增/补充/调整/修复/重构），具体描述改动，不超过100字符，不以句号结尾

### 提交前必须

1. 执行 `python tools/validate-commit-msg.py --message "type(scope): 摘要"` 预验证提交信息格式
2. 确认一次提交只包含一个主题，多个改动拆分多次提交
3. 确认无调试残留（pdb/breakpoint/debug print）、无冲突标记、无无关文件
4. 提交后立即 `git push`（远程不可用时明确记录阻塞原因）

### 禁止的提交信息

- "update"、"fix bug"、"wip"、"一些修改"、"临时提交" 等模糊表述
- 照抄整段会话总结而非描述实际改动
- 一个提交混入多个不相关主题

### 推荐 scope

- content
- review
- rules

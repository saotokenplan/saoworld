# godot-gameplay-implementer

## 目标

基于 Godot 4 和 typed GDScript 实现客户端玩法逻辑、场景组织、UI 交互与最小验证脚本。重点是让 Agent 能稳定增量开发，而不是一次性堆出过大的玩法系统。

## 适用场景

- 玩家移动、交互、任务触发、投票入口等客户端能力开发
- 新区域、新 NPC 触发逻辑和世界状态表现
- Godot 场景与脚本结构整理

## 规范来源

- 主要来源：
  - `docs/20-specs/product-spec.md`
  - `docs/20-specs/engineering-conventions.md`
- 次要来源：
  - `docs/20-specs/backend-data-spec.md`
  - `docs/30-api/openapi-draft.md`
- 说明：
  - 玩法闭环、投票入口、世界更新反馈和产品边界以 `product-spec.md` 为准
  - 客户端工程组织、命名和测试约束参考 `engineering-conventions.md`
  - 客户端消费的数据结构和接口契约参考 `backend-data-spec.md` 与 `openapi-draft.md`

## 输入

- `spec.md`
- `acceptance.md`
- 现有 Godot 项目结构
- 数据 schema、接口契约或 OpenAPI 草案
- 客户端相关约束

## 输出

- Godot 场景与脚本改动
- 必要的数据配置
- 客户端测试或最小验证脚本
- 修改说明与回滚要点

## 实现原则

- 默认使用 typed GDScript
- 一个场景只承载一个主要玩法职责
- 场景、脚本、数据配置分离
- 客户端逻辑只消费结构化数据，不直接硬编码运营内容

## 工作流程

1. 阅读需求与验收条件
2. 找到受影响的场景、脚本和数据文件
3. 先补或调整结构，再写实现
4. 为关键行为补最小验证路径
5. 运行相关门禁并输出结果

## 硬约束

- 不引入未经讨论的新核心玩法循环
- 不直接把 AI 自由文本写进客户端逻辑作为规则来源
- 不在 UI 层写复杂业务判断
- 不把服务端配置复制成多份客户端常量
- 不修改主线骨架和经济边界

## 最低测试要求

以下能力改动时必须至少覆盖一项验证：

- 玩家移动与交互
- 任务触发与完成
- 区域进入与状态刷新
- 投票入口展示与结果反馈
- 内容包更新后的表现加载

## 推荐产物

- `scene-change-notes.md`
- `client-test-notes.md`

## 不该做的事

- 不直接发布内容包
- 不绕过服务端状态和本地缓存规则
- 不把需求包里没有定义的系统一起重写

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

- game
- ui
- player
- npc
- world
- quest

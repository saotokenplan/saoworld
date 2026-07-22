# 流程视图

> 说明：本目录用于把“最小投票链路”按流程顺序串起来阅读；正式时序、状态迁移、事件内容和任务边界以 `docs/20-specs/` 与 `docs/30-api/` 为准。

## 本目录看什么

- `vote-lifecycle.md`：从创建到结算的整体生命周期摘要
- `vote-submission-flow.md`：玩家提交一次有效投票的主流程
- `vote-finalization-flow.md`：投票关闭后如何结算并把结果交给后续链路
- `audit-trail.md`：关键操作如何进入审计与追踪链路

## 建议阅读顺序

1. 先看 `vote-lifecycle.md`，建立整体顺序感
2. 再看 `vote-submission-flow.md` 与 `vote-finalization-flow.md`，理解玩家和系统的关键步骤
3. 最后看 `audit-trail.md`，确认关键动作如何被追踪和回查

## 本目录的写法约束

- 以流程摘要、关键检查点和交付结果为主
- 不重复维护完整请求报文、数据库写入步骤和实现级伪代码
- 如需要精确契约或状态机，回到源规范

## 源文档入口

- 产品规范：`docs/20-specs/product-spec.md`
- 后端与数据规范：`docs/20-specs/backend-data-spec.md`
- API 参考：`docs/30-api/`

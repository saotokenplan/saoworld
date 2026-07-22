# 功能视图

> 说明：本目录用于从产品与协作视角快速理解“最小投票链路”包含哪些功能能力；正式状态机、接口路径和字段约束以 `docs/20-specs/` 与 `docs/30-api/` 为准。

## 本目录看什么

- `voting-cycle.md`：投票周期如何被创建、推进、关闭和结算
- `vote-submission.md`：玩家如何完成一次有效投票
- `vote-counting.md`：投票关闭后如何结算并产出结果
- `vote-results.md`：玩家与运营如何查看当前投票和历史结果
- `audit-logging.md`：为什么关键动作必须进入审计链

## 建议阅读顺序

1. 先看 `voting-cycle.md`，理解整个时间窗口如何运行
2. 再看 `vote-submission.md` 与 `vote-counting.md`，串起玩家提交和系统结算
3. 最后看 `vote-results.md` 与 `audit-logging.md`，补齐展示和追踪视角

## 本目录的写法约束

- 以功能目标、关键流程和业务关注点为主
- 不重复维护接口请求结构、错误码表和数据库字段明细
- 如与源规范冲突，以源规范为准

## 源文档入口

- 产品规范：`docs/20-specs/product-spec.md`
- 后端与数据规范：`docs/20-specs/backend-data-spec.md`
- API 参考：`docs/30-api/`

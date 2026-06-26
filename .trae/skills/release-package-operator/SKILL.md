# release-package-operator

## 目标

围绕内容包进行打包、灰度发布、正式上线、回滚和发布说明生成，保证每次上线都有明确版本、范围、观测窗口和回退路径。

## 适用场景

- 新内容包通过审核后准备上线
- 灰度范围扩大
- 上线异常触发快速回滚
- 生成发布记录与复盘摘要

## 规范来源

- 主要来源：
  - `docs/20-specs/backend-data-spec.md`
  - `docs/20-specs/agent-loop-spec.md`
- 次要来源：
  - `docs/20-specs/content-generation-spec.md`
  - `docs/20-specs/engineering-conventions.md`
- 说明：
  - 内容包、发布状态、灰度和回滚约束以 `backend-data-spec.md` 为准
  - 发布治理、审计链和回滚闭环要求以 `agent-loop-spec.md` 为准
  - 进入发布链路的对象生命周期参考 `content-generation-spec.md`
  - 工程发布协作与产物约束参考 `engineering-conventions.md`

## 输入

- 已审核通过的内容对象
- `content_package_id`
- 灰度范围
- 发布窗口与风险约束
- 回滚目标版本

## 输出

- 内容包构建结果
- 灰度发布记录
- 正式上线记录
- 回滚记录
- `release-notes.md`

## 工作流程

1. 校验输入对象是否全部通过审核
2. 组装内容包并写入版本信息
3. 先灰度发布到限定范围
4. 观察关键指标
5. 符合条件后正式发布
6. 若异常则按内容包回滚

## 关键指标

- 发布成功率
- 回滚触发次数
- 上线后错误率
- 内容相关投诉或驳回信号

## 硬约束

- 回滚最小单位必须是 `content_package_id`
- 没有审核通过记录不得发布
- 灰度未完成前不得直接全量上线
- 发布与回滚都必须写操作摘要和关联原因

## 发布摘要要求

`release-notes.md` 至少包含：

- 内容包编号
- 影响区域
- 涉及对象类型
- 来源投票周期
- 上线时间
- 回滚路径

## 不该做的事

- 不跳过灰度直接扩大范围
- 不在没有稳定版本的情况下覆盖线上内容
- 不把多个无关区域强行打成一个无法拆分的大包

# 循环日志 Round 8

> 任务：auto-20260723-0645（M4 模板文本细化，WP1 规划期准备）
> 时间：2026-07-23 06:45
> 分支：auto/auto-20260723-0645

## 本轮输入

- project-status.md：下一阶段建议第 5 条（M4 规划期低风险准备）
- M4 规划第五节：白名单五项已落地四项（样本集/阈值预案/看板指标/运营流程），仅剩模板文本细化
- 自动化记忆：0443 轮指定本轮候选为 WP1 模板文本细化

## 关键实测发现

1. **双源提示词漂移（F0，高）**：`services/generation/templates/` 下 16 个 jinja2 模板为死文本——`content_generator.py` 全部 `generate_*` 方法解析模板名后丢弃，实际使用 `_build_*_prompt` 内联构造。Boss jinja2 缺评分器必填 6 字段（is_boss/boss_rank/phase_count/special_skills/enrage_threshold/reward），按现状评分 -0.18，>0.85 不可达；live `_build_boss_prompt` 已含全部六字段。
2. **score_region 字段错位（F1，高）**：评分器校验 `difficulty`（easy/normal/hard/extreme）+ `features`，而 live prompt 与 `region_data_adapter` 使用 `danger_level`（peaceful/low/medium/high/extreme）+ `landmarks`——场景评分两个维度名存实亡。
3. **数值无锚（F2/F3，中）**：装备仅「确保数值与等级要求和稀有度匹配」、怪物 hp 仅「正整数」，G1/G2 强度区间约束无文本载体。
4. **章节上限缺席（F4，中）**：level_requirement / level / recommended_level 与章节号无映射条款。

## 本轮产出

- 主交付物：`docs/10-requirements/M4-模板文本细化.md`（draft）——缺陷清单 F0–F6、数值锚定表（装备/怪物公式 + 稀有度/类型系数）、章节上限条款、输出格式硬化文本、双源收口方案（推荐方案 A：迁移内联 prompt 回 jinja2 并接线渲染）、score_region 对齐表、实施期动作 A1–A6、WP1 验收路径。
- 同步：M4 规划第五节进展（白名单五项全部落地、规划期准备收口）+ 第八节回链；requirements README 补登。

## 边界遵守

- 未改 services/ 任何代码与模板文件（提示词文本变更影响真实 LLM 输出分布，属实施期动作）。
- 未触碰 project-status.md；.workbuddy 遥测不进主题提交。

## 遗留与下一轮

- M4 规划期白名单全部收口，自动化循环预计回到「无新工作·优雅结束」常态，直至灰度发布决策解锁实施期。
- 实施期启动信号：灰度发布窗口确认 + 运行时验证销项。

# 调研报告任务规划示例

## 任务概述
- **任务名称**：游戏开发技术栈选型调研
- **任务类型**：调研报告
- **预期产出**：docs/technology-stack-research.md
- **循环模式**：Plan

---

## 一、主循环阶段划分

### 阶段1：调研收集子循环
- 执行目标：收集游戏开发主流技术栈信息
- 调用 Subagent：stage-researcher
- 可用工具：WebSearch, WebFetch, Read, Grep
- 输出产物：.trae/output/research-summary.md
- 最大迭代：6轮

### 阶段2：内容生成子循环
- 执行目标：生成技术选型调研报告
- 调用 Subagent：stage-writer
- 可用工具：Read, Write, Edit
- 输出产物：docs/technology-stack-research-draft.md
- 最大迭代：6轮

### 阶段3：自检校验子循环
- 执行目标：对照 checklist 完成校验
- 调用 Subagent：verifier
- 可用工具：Read, Grep, Write
- 输出产物：.trae/output/verification-report.md
- 最大迭代：3轮

### 阶段4：优化修复子循环
- 执行目标：修复校验发现的缺陷
- 调用 Subagent：micro-fixer
- 可用工具：Read, Edit, Grep
- 输出产物：docs/technology-stack-research-optimized.md
- 最大迭代：3轮

### 阶段5：终稿定产子循环
- 执行目标：全量终验、生成交付物
- 调用 Subagent：verifier
- 可用工具：Read, Write, Edit
- 输出产物：docs/technology-stack-research-final.md
- 最大迭代：3轮

---

## 二、异常处理

### 循环溢出处理
- 调研阶段6轮仍未覆盖需求 → 输出当前结果 + 待补充清单
- 内容生成6轮仍未完成 → 输出当前章节 + 进度说明

### 资料不足处理
- 某项技术资料缺失 → 标注"待补充"并列出所需信息
- 无法验证的数据 → 标注"待验证"

---

## 三、风险点

| 风险类型 | 预防措施 |
|---------|---------|
| 技术信息过时 | 优先查看近6个月的资料 |
| 不同来源信息矛盾 | 标注争议点，列出多方观点 |
| 技术术语不统一 | 建立术语表，统一定义 |

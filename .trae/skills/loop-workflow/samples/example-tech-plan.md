# 技术方案任务规划示例

## 任务概述
- **任务名称**：投票服务架构优化方案
- **任务类型**：技术方案
- **预期产出**：docs/vote-service-optimization-plan.md
- **循环模式**：Plan

---

## 一、主循环阶段划分

### 阶段1：现状调研子循环
- 执行目标：调研投票服务当前架构与性能瓶颈
- 调用 Subagent：stage-researcher
- 可用工具：Read, Grep, Glob, Bash（只读）
- 输出产物：.trae/output/current-status.md
- 最大迭代：4轮

### 阶段2：方案设计子循环
- 执行目标：设计架构优化方案
- 调用 Subagent：stage-writer
- 可用工具：Read, Write, Edit
- 输出产物：docs/vote-service-optimization-draft.md
- 最大迭代：6轮

### 阶段3：自检校验子循环
- 执行目标：校验方案可行性与完整性
- 调用 Subagent：verifier
- 可用工具：Read, Grep, Write
- 输出产物：.trae/output/verification-report.md
- 最大迭代：3轮

### 阶段4：优化修复子循环
- 执行目标：修复方案缺陷
- 调用 Subagent：micro-fixer
- 可用工具：Read, Edit, Grep
- 输出产物：docs/vote-service-optimization-optimized.md
- 最大迭代：3轮

### 阶段5：终稿定产子循环
- 执行目标：全量终验、生成交付物
- 调用 Subagent：verifier
- 可用工具：Read, Write, Edit
- 输出产物：docs/vote-service-optimization-final.md
- 最大迭代：3轮

---

## 二、文件权限声明

本任务需要读取以下目录的文件（已授权）：
- services/vote/app/ - 投票服务代码
- services/vote/tests/ - 投票服务测试

本任务写入目录：
- docs/ - 文档输出
- .trae/loop-log/ - 循环日志

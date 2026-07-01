#!/bin/bash
# Session 初始化 Hook - Loop Engineering

mkdir -p .trae/loop-log
mkdir -p .trae/output

echo "0" > .trae/loop-log/round-counter.txt

cat <<'EOF'
{
  "type": "context",
  "content": "【Loop Engineering 模式已启用】已加载全局循环规则。任务开始前必须生成 task-plan.md 和 checklist.md，等待确认后启动循环。"
}
EOF

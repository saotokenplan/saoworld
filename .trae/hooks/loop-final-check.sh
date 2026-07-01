#!/bin/bash
# 循环终止校验 Hook

INPUT=$(cat)
ROUND=$(cat .trae/loop-log/round-counter.txt 2>/dev/null || echo "0")

cat <<EOF
{
  "type": "context",
  "content": "循环执行结束。当前轮次：第${ROUND}轮。请确认 checklist 是否全部通过，如未通过请启动修复循环。"
}
EOF

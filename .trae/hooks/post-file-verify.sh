#!/bin/bash
# L1 即时校验 Hook 脚本

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.toolInput.file_path // empty')
ROUND=$(cat .trae/loop-log/round-counter.txt 2>/dev/null || echo "0")

CHECKS_PASSED=()
CHECKS_FAILED=()

if [ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ]; then
    cat <<'EOF'
{
  "type": "pass"
}
EOF
    exit 0
fi

if [ -s "$FILE_PATH" ]; then
    CHECKS_PASSED+=("1.1:文件存在且非空")
else
    CHECKS_FAILED+=("1.1:文件为空")
fi

if [[ "$FILE_PATH" == *.md ]]; then
    H1_COUNT=$(grep -c "^# " "$FILE_PATH" 2>/dev/null || echo "0")
    H2_COUNT=$(grep -c "^## " "$FILE_PATH" 2>/dev/null || echo "0")
    if [ "$H1_COUNT" -ge 1 ] && [ "$H2_COUNT" -ge 1 ]; then
        CHECKS_PASSED+=("1.2:标题结构完整")
    else
        CHECKS_FAILED+=("1.2:标题结构不完整")
    fi

    CODE_OPEN=$(grep -c '^```' "$FILE_PATH" 2>/dev/null || echo "0")
    if [ $((CODE_OPEN % 2)) -eq 0 ]; then
        CHECKS_PASSED+=("1.5:代码块语法正确")
    else
        CHECKS_FAILED+=("1.5:代码块未闭合")
    fi
fi

ENCODING=$(file -b --mime-encoding "$FILE_PATH" 2>/dev/null || echo "unknown")
if [[ "$ENCODING" == "utf-8" || "$ENCODING" == "us-ascii" ]]; then
    CHECKS_PASSED+=("1.6:编码正确")
else
    CHECKS_FAILED+=("1.6:编码异常($ENCODING)")
fi

PASSED_COUNT=${#CHECKS_PASSED[@]}
FAILED_COUNT=${#CHECKS_FAILED[@]}
TOTAL=$((PASSED_COUNT + FAILED_COUNT))

mkdir -p .trae/loop-log
echo "[$(date)] L1校验: $FILE_PATH" >> .trae/loop-log/round-${ROUND}-verify.log
echo "  通过: $PASSED_COUNT/$TOTAL" >> .trae/loop-log/round-${ROUND}-verify.log
for fail in "${CHECKS_FAILED[@]}"; do
    echo "  失败: $fail" >> .trae/loop-log/round-${ROUND}-verify.log
done

echo "$(date): 修改文件 $FILE_PATH" >> .trae/loop-log/round-${ROUND}-files.log

if [ "$FAILED_COUNT" -eq 0 ]; then
    cat <<EOF
{
  "type": "pass",
  "message": "L1即时校验通过(${PASSED_COUNT}/${TOTAL})"
}
EOF
else
    FAIL_LIST=$(IFS=", "; echo "${CHECKS_FAILED[*]}")
    cat <<EOF
{
  "type": "context",
  "content": "L1即时校验发现${FAILED_COUNT}项问题：${FAIL_LIST}。建议修复后再继续。"
}
EOF
fi

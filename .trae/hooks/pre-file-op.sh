#!/bin/bash
# 文件操作前置校验 Hook

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.toolName // empty')
FILE_PATH=$(echo "$INPUT" | jq -r '.toolInput.file_path // .toolInput.file_paths[]? // empty' | head -1)

BLACKLIST_DIRS=".git .trae/rules .trae/hooks .trae/agents infra services/*/config"
WHITELIST_DIRS=".trae/loop-log .trae/output docs reports tools data/processed"

if [ -z "$FILE_PATH" ]; then
    cat <<'EOF'
{
  "type": "pass"
}
EOF
    exit 0
fi

NORMALIZED_PATH=$(echo "$FILE_PATH" | sed 's|^/workspace/||' | sed 's|^\./||')

for dir in $BLACKLIST_DIRS; do
    if [[ "$NORMALIZED_PATH" == $dir/* || "$NORMALIZED_PATH" == "$dir" ]]; then
        cat <<EOF
{
  "type": "context",
  "content": "警告：文件 $NORMALIZED_PATH 位于受限目录，请确认是否已授权修改。"
}
EOF
        exit 0
    fi
done

for dir in $WHITELIST_DIRS; do
    if [[ "$NORMALIZED_PATH" == $dir/* || "$NORMALIZED_PATH" == "$dir" ]]; then
        cat <<'EOF'
{
  "type": "pass"
}
EOF
        exit 0
    fi
done

cat <<EOF
{
  "type": "context",
  "content": "注意：文件 $NORMALIZED_PATH 不在白名单内，请确认已在 task-plan.md 中声明并获得授权。"
}
EOF

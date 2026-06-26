#!/usr/bin/env bash
#
# install-git-hooks.sh
# Sets up git hooks directory to use project-managed hooks from .githooks/
# Also makes hook scripts executable.
#
# Usage: bash tools/install-git-hooks.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Installing git hooks for repository at: $REPO_ROOT"
cd "$REPO_ROOT"

chmod +x "$REPO_ROOT/.githooks/commit-msg"
chmod +x "$REPO_ROOT/.githooks/pre-commit"
chmod +x "$REPO_ROOT/tools/validate-commit-msg.py"

git config core.hooksPath "$REPO_ROOT/.githooks"

echo ""
echo "Git hooks installed successfully!"
echo ""
echo "Configured hooksPath: $(git config core.hooksPath)"
echo ""
echo "Active hooks:"
ls -la "$REPO_ROOT/.githooks/"
echo ""
echo "From now on, commit messages will be validated against the convention."
echo "Format: <type>(<scope>): <summary>"
echo "Types: docs, feat, fix, refactor, test, chore"
echo ""
echo "To bypass hooks in an emergency (not recommended):"
echo "  git commit --no-verify"

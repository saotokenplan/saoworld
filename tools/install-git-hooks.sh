#!/usr/bin/env bash
#
# install-git-hooks.sh
# Sets up git hooks directory to use project-managed hooks from .githooks/
# Also makes hook scripts executable.
#
# Works in both main repo and git worktrees.
# Uses relative path so core.hooksPath stays valid across worktrees.
#
# Usage: bash tools/install-git-hooks.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Installing git hooks for repository at: $REPO_ROOT"
cd "$REPO_ROOT"

# Make hooks and tools executable
chmod +x "$REPO_ROOT/.githooks/commit-msg"
chmod +x "$REPO_ROOT/.githooks/pre-commit"
chmod +x "$REPO_ROOT/.githooks/prepare-commit-msg"
chmod +x "$REPO_ROOT/tools/validate-commit-msg.py"
chmod +x "$REPO_ROOT/tools/generate-commit-msg.py"

# Use relative path so it works in worktrees
# .githooks/ is relative to the worktree root (where .git or .git file lives)
git config core.hooksPath .githooks

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

# tools/ - Offline Scripts & Utilities

Offline scripts, validators, git hooks installer, packaging tools, and one-off data migrations.

## Available Scripts

| Script | Purpose |
|--------|---------|
| [validate-commit-msg.py](file:///workspace/tools/validate-commit-msg.py) | Validates git commit messages against the project convention (`<type>(<scope>): <summary>`). Used by git `commit-msg` hook and can be used standalone or in CI. |
| [install-git-hooks.sh](file:///workspace/tools/install-git-hooks.sh) | Installs project-managed git hooks from `.githooks/` by setting `git config core.hooksPath`. Run once after cloning the repo. |

## Git Hooks

Hooks live in [.githooks/](file:///workspace/.githooks) (tracked in Git, unlike `.git/hooks/` which is not):

- `commit-msg` — Runs `validate-commit-msg.py` to reject non-conforming commit messages
- `pre-commit` — Checks for large files (>500KB), merge conflict markers, and debug breakpoints (`pdb.set_trace()`, `breakpoint()`, `print(..., # debug)`)

### Installation

```bash
bash tools/install-git-hooks.sh
```

### Manual Validation (before committing)

```bash
python tools/validate-commit-msg.py --message "feat(vote): 增加投票提交接口"
```

### Emergency Bypass

```bash
git commit --no-verify
```

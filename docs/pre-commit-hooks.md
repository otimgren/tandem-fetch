# Quickstart: Pre-Commit Hooks Setup

**Feature**: 002-precommit-hooks
**Target Audience**: Developers contributing to tandem-fetch
**Time to Complete**: 2-5 minutes

## What You'll Get

After following this guide, every `git commit` will automatically:

- ✅ Format Python code with ruff (consistent style)
- ✅ Sort imports alphabetically
- ✅ Remove trailing whitespace
- ✅ Normalize line endings to LF (Unix style)
- ✅ Validate YAML/TOML/JSON files
- ✅ Block commits containing secrets (API keys, passwords)
- ✅ Block commits containing PII (emails, phone numbers in code)
- ✅ Prevent committing files in `sensitive/` directory

**Execution time**: <1 second for typical commits

---

## Prerequisites

- Python 3.12+ installed
- `uv` package manager installed
- Git repository cloned
- Write access to repository

---

## Step 1: Install Prek (One-Time Global Setup)

Choose **one** installation method:

### Option A: Install with uv (Recommended)

```bash
uv tool install prek
```

### Option B: Install with pip

```bash
pip install prek
```

### Option C: Run without installing (using uvx)

```bash
# No installation needed, use uvx each time:
uvx prek install
```

**Verify installation**:
```bash
prek --version
# Should output: prek 0.2.x or higher
```

---

## Step 2: Install Git Hooks (Per-Repository Setup)

Navigate to the tandem-fetch repository root and install the hooks:

```bash
cd /path/to/tandem-fetch
prek install
```

**Expected output**:
```
✓ Installed pre-commit hook
```

This creates `.git/hooks/pre-commit` which runs automatically on every commit.

---

## Step 3: Verify Setup (Optional but Recommended)

Test the hooks on all files to ensure everything works:

```bash
prek run --all-files
```

**Expected output** (first run may be slow as it downloads hooks):
```
Initializing environment for https://github.com/astral-sh/ruff-pre-commit...
Initializing environment for https://github.com/gitleaks/gitleaks...
✓ trailing-whitespace.............................Passed
✓ end-of-file-fixer...............................Passed
✓ mixed-line-ending...............................Passed
✓ check-yaml......................................Passed
✓ check-toml......................................Passed
✓ check-json......................................Passed
✓ check-added-large-files.........................Passed
✓ ruff............................................Passed
✓ ruff-format.....................................Passed
✓ gitleaks........................................Passed
```

**If any hook fails**:
- Review the error message
- Fix the issues in the reported files
- Re-run `prek run --all-files`

---

## Step 4: Make Your First Commit with Hooks

Try making a commit to see hooks in action:

```bash
# Make a small change
echo "# Test comment" >> README.md

# Stage and commit
git add README.md
git commit -m "Test pre-commit hooks"
```

**What happens**:
1. Hooks run automatically before commit
2. If hooks modify files (e.g., formatting), commit is rejected
3. Re-stage modified files: `git add README.md`
4. Commit again: `git commit -m "Test pre-commit hooks"`
5. Commit succeeds if all checks pass

---

## Daily Workflow

### Normal Commits (Hooks Run Automatically)

```bash
# 1. Make changes to files
vim src/tandem_fetch/my_file.py

# 2. Stage changes
git add src/tandem_fetch/my_file.py

# 3. Commit (hooks run automatically)
git commit -m "Add new feature"

# 4. If hooks auto-fixed files, re-stage and commit again
git add src/tandem_fetch/my_file.py
git commit -m "Add new feature"
```

**Typical flow**:
- ✅ Hooks pass → Commit succeeds
- 🔧 Hooks auto-fix → Re-stage and commit again
- ❌ Hooks fail → Fix issues, stage, commit again

### Run Hooks Manually (Before Committing)

```bash
# Run on staged files only
prek run

# Run on all files in repository
prek run --all-files

# Run specific hook
prek run ruff-format

# Run on specific files
prek run --files src/tandem_fetch/my_file.py
```

---

## Handling Special Cases

### Case 1: Secret Detected (False Positive)

**Scenario**: Gitleaks blocks your commit for a test API key

```bash
$ git commit -m "Add test fixture"
✗ gitleaks......Failed
- Secret detected in src/tests/fixtures/api_response.json:12
```

**Solutions** (choose one):

**Option A**: Add to `.gitleaksignore` file
```bash
# Create or edit .gitleaksignore
echo "test-api-key-12345" >> .gitleaksignore
git add .gitleaksignore
git commit -m "Add test fixture"
```

**Option B**: Add pragma comment in code
```python
API_KEY = "test-api-key-12345"  # pragma: allowlist secret
```

**Option C**: Update `.gitleaks.toml` allowlist
```toml
[allowlist]
regexes = [
  '''test-api-key-.*''',  # Allow test API keys
]
```

**Option D**: Skip for this commit only (use sparingly)
```bash
SKIP=gitleaks git commit -m "Add test fixture"
```

### Case 2: Urgent Hotfix (Bypass All Hooks)

**⚠️ Use only in emergencies**:

```bash
git commit --no-verify -m "Emergency hotfix"
```

**Best practice**: Fix issues properly and create a follow-up commit that passes hooks.

### Case 3: Large File Needs to Be Committed

**Default limit**: 1MB (1000KB)

**Increase limit** in `.pre-commit-config.yaml`:
```yaml
- id: check-added-large-files
  args: ['--maxkb=5000']  # Change to 5MB
```

Then run:
```bash
prek run --all-files  # Re-validate config
git add .
git commit -m "Increase large file limit"
```

---

## Understanding Hook Output

### ✅ Hook Passed (No Issues)
```
✓ ruff-format.....................................Passed
```
→ No action needed, file is clean

### 🔧 Hook Fixed Files
```
✓ ruff-format.....................................Fixed
```
→ Hook auto-formatted your code
→ **Action required**: Re-stage files and commit again

### ❌ Hook Failed
```
✗ gitleaks........................................Failed
- Secret detected in sensitive/credentials.toml
```
→ Fix the issue in the file
→ Re-stage and commit again

---

## Maintenance

### Update Hook Versions (Weekly/Monthly)

```bash
# Update all hooks to latest versions
prek auto-update

# Update with cooldown (prevents excessive updates)
prek auto-update --cooldown-days 7
```

**What it does**:
- Checks for newer versions of ruff, gitleaks, etc.
- Updates `.pre-commit-config.yaml` with new versions
- Commits the changes automatically

### Clean Up Cached Environments

```bash
# Interactive cleanup (choose what to delete)
prek cache clean

# Automatic garbage collection
prek cache gc
```

**When to use**:
- Disk space running low
- After many hook version updates
- Before long periods without commits

---

## Troubleshooting

### Problem: Hooks are slow (>5 seconds)

**Causes**:
- First run (downloading hook environments)
- Committing many files at once
- Large files being scanned

**Solutions**:
```bash
# Check cache status
prek cache list

# Run on fewer files
git add src/specific_file.py
git commit -m "Smaller commit"

# Verify prek version (should be 0.2.x+)
prek --version
```

### Problem: "prek: command not found"

**Cause**: Prek not installed or not in PATH

**Solutions**:
```bash
# If installed with uv
uv tool install prek

# If installed with pip
pip install prek

# Check installation
which prek

# Add to PATH if needed (macOS/Linux)
export PATH="$HOME/.local/bin:$PATH"
```

### Problem: Hooks not running at all

**Cause**: Git hooks not installed

**Solutions**:
```bash
# Re-install hooks
prek install

# Verify hook exists
ls -la .git/hooks/pre-commit

# Check hook content
cat .git/hooks/pre-commit | head -5
# Should show: #!/usr/bin/env bash
#              prek run ...
```

### Problem: Gitleaks fails on every commit

**Cause**: Credentials file accidentally staged

**Solutions**:
```bash
# Check what's staged
git status

# Unstage sensitive file
git restore --staged sensitive/credentials.toml

# Ensure sensitive/ is gitignored
echo "sensitive/" >> .gitignore
git add .gitignore
git commit -m "Ensure sensitive/ is ignored"
```

---

## Advanced Configuration

### Customize Ruff Rules

Edit `pyproject.toml`:

```toml
[tool.ruff]
line-length = 120  # Change from default 100

[tool.ruff.lint]
extend-select = ["I", "N", "UP"]  # Add naming, upgrade rules
ignore = ["E501"]  # Ignore specific rules

[tool.ruff.format]
quote-style = "double"  # Change from single
```

### Disable Specific Hooks

Edit `.pre-commit-config.yaml`:

```yaml
# Comment out unwanted hooks
# - id: check-json
```

Or skip at commit time:
```bash
SKIP=check-json git commit -m "Skip JSON validation"
SKIP=check-json,gitleaks git commit -m "Skip multiple hooks"
```

### Add Custom Hooks

Edit `.pre-commit-config.yaml`:

```yaml
repos:
  # ... existing hooks ...

  # Add mypy type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        args: [--strict]
```

Then install new hooks:
```bash
prek install
prek run --all-files  # Test on all files
```

---

## Getting Help

### Documentation
- **Prek docs**: https://prek.j178.dev/
- **Ruff docs**: https://docs.astral.sh/ruff/
- **Gitleaks docs**: https://github.com/gitleaks/gitleaks

### Common Commands Quick Reference

```bash
prek install              # Install git hooks
prek run                  # Run on staged files
prek run --all-files      # Run on all files
prek run <hook-id>        # Run specific hook
prek auto-update          # Update hook versions
prek cache clean          # Clean cache
prek --help               # Show all commands

SKIP=<hook-id> git commit # Skip specific hook
git commit --no-verify    # Skip all hooks (emergency only)
```

### Project-Specific Help

- Check `.pre-commit-config.yaml` for enabled hooks
- Check `.gitleaks.toml` for secret detection rules
- Check `pyproject.toml` for ruff configuration
- Ask in team chat for assistance

---

## Next Steps

After completing this quickstart:

1. ✅ Make a few commits to get familiar with the workflow
2. ✅ Review and customize ruff rules in `pyproject.toml` if needed
3. ✅ Share this guide with other contributors
4. ✅ Report any false positives in gitleaks to add to allowlist

**Happy committing! 🚀**

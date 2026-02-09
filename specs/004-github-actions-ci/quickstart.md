# GitHub Actions CI - Quickstart Guide

**Feature**: 004-github-actions-ci
**Last Updated**: 2026-02-08

## Overview

This guide helps you verify the GitHub Actions CI setup is working correctly and demonstrates how to use it effectively.

## Prerequisites

- GitHub repository with GitHub Actions enabled
- `.github/workflows/ci.yml` workflow file created
- Branch protection configured on main branch
- Local environment with `uv` installed

## Quick Verification Steps

### 1. Verify Workflow File Exists

```bash
# Check that workflow file is present
ls -la .github/workflows/ci.yml

# Expected: File exists with workflow configuration
```

### 2. Validate Workflow Syntax Locally

```bash
# Install act for local workflow validation (optional)
brew install act  # macOS
# or
curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash  # Linux

# List workflows to verify syntax is valid
act -l

# Expected output:
# Stage  Job ID  Job name  Workflow name  Workflow file  Events
# 0      ci      ci        CI             ci.yml         push,pull_request
```

### 3. Test CI Locally Before Pushing

```bash
# Run the local CI script
bash .github/scripts/run-ci-locally.sh

# Expected: All checks pass
# ✓ Dependencies installed
# ✓ Ruff check passed
# ✓ Ruff format check passed
# ✓ Tests passed (37 passed in ~10s)
```

### 4. Create Test Pull Request

```bash
# Create a feature branch
git checkout -b test-ci-workflow

# Make a trivial change
echo "# CI Test" >> test-ci.md
git add test-ci.md
git commit -m "Test: Verify CI workflow runs on PR"

# Push to GitHub
git push origin test-ci-workflow

# Create PR via GitHub UI or gh CLI
gh pr create --title "Test CI Workflow" --body "Testing automated CI"
```

### 5. Verify CI Runs on PR

1. Navigate to your PR on GitHub
2. Check the "Checks" tab or status checks section
3. Verify you see: `ci / ci` check running or completed
4. Click "Details" to view workflow execution logs

**Expected**: Status check appears and shows success ✓

### 6. Test CI Failure Scenario

```bash
# Introduce a linting error
echo "import sys,os" > test_bad_style.py  # Missing space after comma
git add test_bad_style.py
git commit -m "Test: Verify CI catches linting errors"
git push origin test-ci-workflow
```

**Expected**: CI fails with ruff check error, PR shows failure status ❌

### 7. Fix and Verify Recovery

```bash
# Fix the linting error
echo "import os\nimport sys" > test_bad_style.py
git add test_bad_style.py
git commit -m "Fix: Correct linting error"
git push origin test-ci-workflow
```

**Expected**: CI passes, PR shows success status ✓

### 8. Verify Branch Protection

Try merging the PR when CI is failing (if you still have a failing commit):

**Expected**: GitHub shows "Merging is blocked" with reason "Required status check 'ci' must pass"

## Common Usage Patterns

### Daily Development Workflow

```bash
# 1. Create feature branch
git checkout -b feature/my-change

# 2. Make changes
# ... edit files ...

# 3. Run local CI checks BEFORE committing
bash .github/scripts/run-ci-locally.sh

# 4. If local checks pass, commit and push
git add .
git commit -m "Add my feature"
git push origin feature/my-change

# 5. Create PR and wait for CI to confirm
gh pr create --fill

# 6. Monitor CI status in PR
gh pr checks
```

### Debugging CI Failures

```bash
# 1. Check workflow logs on GitHub
gh run view --log  # View most recent run
gh run view 12345678 --log  # View specific run ID

# 2. Reproduce locally
bash .github/scripts/run-ci-locally.sh

# 3. If issue only happens in CI, try act
act -j ci  # Run ci job locally with act

# 4. Check for environment differences
# - Python version (should be 3.12)
# - Dependency versions (check uv.lock is committed)
# - OS-specific issues (CI runs on ubuntu-latest)
```

### Updating Dependencies

```bash
# 1. Update dependencies
uv lock --upgrade

# 2. Verify locally
uv sync
bash .github/scripts/run-ci-locally.sh

# 3. Commit lock file
git add uv.lock
git commit -m "Update dependencies"
git push

# 4. Verify CI passes with new dependencies
# CI will install from updated uv.lock
```

## Performance Monitoring

### Check CI Duration

```bash
# View recent workflow runs
gh run list --workflow=ci.yml

# View timing for specific run
gh run view 12345678

# Look for:
# - Setup time: Should be < 1 min with cache
# - Lint time: Should be < 30 sec
# - Test time: Should be < 2 min
# - Total time: Should be < 5 min
```

### Verify Cache is Working

1. Push a commit without changing dependencies
2. Check workflow logs for: "Cache restored from key: ..."
3. Dependency installation should take < 30 seconds (vs 2-3 minutes without cache)

**Cache key format**: `uv-<hash(uv.lock)>-<calendar-week>`

### Identify Slow Tests

```bash
# Run pytest with duration report
uv run pytest --durations=10

# Look for tests taking > 1 second
# Consider optimizing or marking as slow
```

## Troubleshooting

### CI Fails but Local Passes

**Possible Causes**:
1. **uv.lock not committed**: Ensure `git add uv.lock`
2. **Environment differences**: Check Python version matches (3.12)
3. **Test isolation issues**: Some tests may depend on local state

**Resolution**:
```bash
# Verify uv.lock is committed
git status

# Check Python version
uv run python --version  # Should be 3.12.x

# Run tests with verbose output
uv run pytest -v
```

### CI is Slow (> 5 minutes)

**Possible Causes**:
1. **Cache miss**: uv.lock changed, cache invalidated
2. **Network issues**: Downloading dependencies slow
3. **Parallel execution disabled**: Check pytest config

**Resolution**:
```bash
# Check if pytest-xdist is working
uv run pytest --version  # Should mention xdist plugin

# Verify parallel execution config
grep "addopts" pyproject.toml  # Should have "-n auto"

# Check cache hit rate in workflow logs
# Look for: "Cache restored from key: ..." vs "Cache not found"
```

### Workflow Not Triggering

**Possible Causes**:
1. **Workflow file syntax error**: YAML is invalid
2. **Branch filter mismatch**: Pushing to non-main branch
3. **GitHub Actions disabled**: Repository settings

**Resolution**:
```bash
# Validate workflow syntax
act -l  # Lists workflows, errors on invalid syntax

# Check trigger configuration
cat .github/workflows/ci.yml | grep -A 5 "on:"

# Verify Actions are enabled in repo settings
# GitHub UI: Settings > Actions > General > Actions permissions
```

### Permission Denied Errors

**Possible Causes**:
1. **GITHUB_TOKEN permissions insufficient**: Workflow needs write access
2. **Protected branch rules too strict**: Can't push to branch

**Resolution**:
- For this project, read-only permissions are intentional and sufficient
- If workflow needs to write (e.g., auto-commit), add:
  ```yaml
  permissions:
    contents: write
  ```

## Next Steps

Once CI is verified working:

1. **Enable Dependabot**: Automatically update action versions
   - Settings > Security > Dependabot > Enable
   - Create `.github/dependabot.yml`:
     ```yaml
     version: 2
     updates:
       - package-ecosystem: github-actions
         directory: /
         schedule:
           interval: monthly
     ```

2. **Add Status Badge**: Show CI status in README.md
   ```markdown
   ![CI](https://github.com/USERNAME/tandem-fetch/workflows/CI/badge.svg)
   ```

3. **Monitor Trends**: Track CI duration and failure rates over time
   - GitHub Insights > Actions usage
   - Identify flaky tests or performance regressions

4. **Consider Enhancements**:
   - Code coverage reporting (Codecov/Coveralls)
   - Separate integration test job (if tests grow significantly)
   - Release automation (tagging, changelog generation)

## Reference Commands

```bash
# List all workflow runs
gh run list --workflow=ci.yml

# View specific run
gh run view 12345678

# Re-run failed jobs
gh run rerun 12345678

# Watch a run in real-time
gh run watch

# List status checks for a PR
gh pr checks

# View PR status
gh pr view 123

# Run CI locally (using act)
act push  # Simulate push event
act pull_request  # Simulate PR event

# Run local CI script
bash .github/scripts/run-ci-locally.sh
```

## Success Criteria Verification

Use this checklist to verify all success criteria from the spec are met:

- [ ] **SC-001**: Complete test suite executes within 2 minutes ✓
  ```bash
  # Check workflow duration in logs
  gh run view --log | grep "Run tests"
  ```

- [ ] **SC-002**: Developers receive feedback within 10 minutes of pushing ✓
  ```bash
  # Check total workflow duration
  gh run view 12345678 | grep "Duration"
  ```

- [ ] **SC-003**: 100% of PRs show clear pass/fail status ✓
  ```bash
  # Verify status check appears
  gh pr view 123 | grep "ci"
  ```

- [ ] **SC-004**: Local validation produces identical results (95% parity) ✓
  ```bash
  # Compare local vs CI results
  bash .github/scripts/run-ci-locally.sh
  gh run view --log
  ```

- [ ] **SC-005**: CI setup time under 2 minutes via caching ✓
  ```bash
  # Check cache hit in logs
  gh run view --log | grep -i cache
  ```

- [ ] **SC-006**: Zero broken builds merged to main ✓
  ```bash
  # Verify branch protection is active
  # GitHub UI: Settings > Branches > main
  ```

- [ ] **SC-007**: Developers can identify failing test within 3 minutes ✓
  ```bash
  # Check test output clarity
  uv run pytest -v
  ```

- [ ] **SC-008**: CI costs remain under $50/month ✓
  ```bash
  # Monitor usage (GitHub is free for public repos)
  # GitHub UI: Settings > Billing > Usage
  ```

## Support

For issues with this CI setup:

1. Check workflow logs: `gh run view --log`
2. Review this quickstart guide
3. Consult research.md for technical decisions and alternatives
4. Check GitHub Actions documentation: https://docs.github.com/actions

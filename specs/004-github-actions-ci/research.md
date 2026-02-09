# GitHub Actions CI Research

**Project**: tandem-fetch
**Date**: 2026-02-08
**Context**: Single-user Python 3.12 project using uv package manager, pytest with pytest-xdist, ruff, and pre-commit hooks

---

## 1. GitHub Actions Setup for Python Projects

### Decision
Use a simple, single-version GitHub Actions workflow with the official `astral-sh/setup-uv` action, targeting Python 3.12 only.

### Rationale
- **Single Python version**: The project explicitly constrains to Python 3.12 per CLAUDE.md, eliminating the need for matrix testing across multiple Python versions
- **Speed**: uv is exceptionally fast - complete CI/CD pipelines can run in under 2 minutes even with multiple Python versions
- **Simplicity-first**: Aligns with the project's constitution of preferring simple, practical solutions for a single-user project
- **Official support**: The `astral-sh/setup-uv` action is officially maintained and widely adopted in 2026

### Alternatives Considered

**Matrix Testing (Multiple Python Versions)**
- Pattern: `strategy: matrix: python-version: ["3.10", "3.11", "3.12", "3.13"]`
- Why not chosen: Unnecessary complexity for a single-user project with explicit Python 3.12 constraint
- When to reconsider: If the project needs to support library distribution or multiple Python versions

**actions/setup-python with pip/pip-tools**
- Traditional approach using `actions/setup-python` followed by pip install
- Why not chosen: Significantly slower than uv (minutes vs seconds), less efficient caching
- Performance difference: uv can be 10-100x faster than pip for dependency resolution

### Implementation Guidance

**Basic Workflow Structure**:
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up uv
        uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true
          cache-dependency-glob: "uv.lock"

      - name: Set up Python
        run: uv python install 3.12

      - name: Install dependencies
        run: uv sync --locked --all-extras --group dev --group test

      - name: Run tests
        run: uv run pytest
```

**Key Configuration Details**:
- Use `uv sync --locked` to ensure reproducible builds from `uv.lock`
- Include `--all-extras --group dev --group test` to install all dependency groups
- Pin action versions (e.g., `@v4`, `@v7`) for security and reproducibility
- Enable built-in caching with `enable-cache: true` for automatic cache management

---

## 2. Dependency Caching with uv

### Decision
Use the built-in caching provided by `astral-sh/setup-uv@v7` with `cache-dependency-glob: "uv.lock"`, and run `uv cache prune --ci` at the end of jobs.

### Rationale
- **Automatic optimization**: The `setup-uv` action handles cache key generation based on `uv.lock` hash
- **CI-optimized pruning**: `uv cache prune --ci` removes unnecessary cache entries, reducing storage costs
- **Centralized cache strategy**: Caching on main branch ensures all PRs benefit from pre-built dependencies
- **Weekly refresh**: Default cache key includes calendar week number (`%V`), providing automatic freshness

### Alternatives Considered

**Manual caching with actions/cache**
```yaml
- uses: actions/cache@v4
  with:
    path: |
      ~/.cache/uv
      ~/.local/share/uv
      .venv
    key: uv-${{ hashFiles('uv.lock') }}
```
- Why not chosen: More verbose, requires manual cache management, built-in option is simpler
- When to reconsider: If you need custom cache invalidation logic or multi-layered caching

**Caching .venv in addition to uv cache**
- Some guides suggest caching both the uv cache and the .venv directory
- Why not chosen: Can lead to cache fragmentation in projects with frequent dependency changes
- Trade-off: Faster for stable dependencies, but slower cache restoration times

**hynek/setup-cached-uv (third-party wrapper)**
- Simplified one-line action that wraps setup-uv with opinionated caching
- Why not chosen: Official action now has equivalent built-in caching; prefer official tools
- When to consider: If you want even more opinionated defaults

### Implementation Guidance

**Optimal Caching Strategy**:
```yaml
- name: Set up uv
  uses: astral-sh/setup-uv@v7
  with:
    enable-cache: true
    cache-dependency-glob: "uv.lock"

- name: Install dependencies
  run: uv sync --locked --all-extras --group dev --group test

- name: Run tests
  run: uv run pytest

- name: Prune cache
  if: always()
  run: uv cache prune --ci
```

**Cache Strategy Details**:
- **Cache from source vs pre-built**: uv automatically determines whether to cache wheels built from source (expensive, worth caching) or re-download pre-built wheels (cheap, not worth caching)
- **Centralized cache on main**: The default behavior caches on the main branch, allowing all PRs to benefit
- **Cache size management**: `uv cache prune --ci` removes unused packages and optimizes cache size
- **Weekly rotation**: Cache keys include `+%V` (calendar week), providing automatic weekly refresh

**Avoiding Common Pitfalls**:
- Don't cache with different keys per PR - this leads to cache fragmentation and wasted storage
- Don't skip `uv cache prune --ci` - cache can grow to hundreds of MB without pruning
- Do use `--locked` flag to ensure uv.lock is respected and cache keys are meaningful

---

## 3. Parallel Test Execution with pytest-xdist

### Decision
Use pytest-xdist with `-n auto` for parallel test execution within a single CI job.

### Rationale
- **Already configured**: The project's `pyproject.toml` already has `addopts = "-n auto --dist loadfile"`
- **Cost-effective**: Requires just one dependency and one command line flag
- **Simple scaling**: `-n auto` automatically detects available CPU cores (typically 2-4 on GitHub Actions runners)
- **No overhead**: Single job means dependencies are installed once
- **Module cohesion**: `--dist loadfile` keeps tests from the same file together, useful for shared fixtures

### Alternatives Considered

**Test sharding across multiple jobs with pytest-split**
```yaml
strategy:
  matrix:
    shard: [1, 2, 3, 4]
steps:
  - run: pytest --splits 4 --group ${{ matrix.shard }}
```
- Why not chosen: Adds complexity, requires installing dependencies 4 times, only beneficial for very large test suites (>10 minutes)
- Overhead trade-off: Each shard re-runs dependency installation, setup, and teardown
- When to reconsider: If test suite grows beyond 10-15 minutes on a single runner

**Manual parallelization strategies**
- Using `--dist loadscope` or `--dist loadgroup` instead of `--dist loadfile`
- Why not chosen: `loadfile` is the safest default for tests with shared fixtures
- When to reconsider: If tests are completely independent and you want maximum parallelization

### Implementation Guidance

**Current Configuration** (from pyproject.toml):
```toml
[tool.pytest.ini_options]
addopts = "-n auto --dist loadfile --tb=short"
```

**CI Execution**:
```yaml
- name: Run tests
  run: uv run pytest
```

**Performance Expectations**:
- Don't expect linear speedup (e.g., 4x with 4 cores)
- Typical speedup: 2-3x on GitHub Actions standard runners
- Overhead from worker process spawning and result aggregation

**Optimizations**:
- Keep `--dist loadfile` to maintain test file cohesion
- Use `-n auto` to adapt to available cores
- Consider `--maxfail=1` for fast-fail during development
- Add `--durations=10` to identify slow tests for optimization

**When Not to Use Parallel Execution**:
- During debugging (use `pytest -n0` to disable)
- For tests with global state dependencies
- When test isolation issues exist

---

## 4. CI Optimization Patterns

### Decision
Implement a simple, fast-feedback CI workflow with:
1. Fail-fast linting before running tests
2. Parallel test execution with pytest-xdist
3. Optimized uv caching
4. Minimal job separation (lint + test in same workflow)

### Rationale
- **Fast feedback**: Linting fails fast (seconds), preventing wasted time on faulty code
- **Cost-effective**: Single workflow reduces overhead from repeated dependency installation
- **Simple**: Easy to understand and maintain for a single-user project
- **Aligned with 2026 trends**: GitHub is adding parallel steps in mid-2026, validating this approach

### Alternatives Considered

**Separate jobs for lint, test, type-check**
```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps: [...]
  test:
    runs-on: ubuntu-latest
    needs: lint
    steps: [...]
```
- Why not chosen: Adds overhead from multiple dependency installations, slower for small projects
- When to reconsider: If different jobs have significantly different dependency requirements

**Aggressive job separation with fail-fast matrix**
- Running each test category (unit, integration, slow) in separate matrix jobs
- Why not chosen: Over-engineering for a single-user project with modest test suite
- Trade-off: More granular failure reporting vs increased complexity and cost

**Full matrix testing across Python versions and OS**
```yaml
strategy:
  matrix:
    python-version: [3.11, 3.12, 3.13]
    os: [ubuntu-latest, macos-latest, windows-latest]
```
- Why not chosen: Unnecessary for single-user project targeting Python 3.12 on Linux
- When to reconsider: If distributing a library or supporting multiple platforms

### Implementation Guidance

**Recommended Workflow Structure**:
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up uv
        uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true
          cache-dependency-glob: "uv.lock"

      - name: Set up Python
        run: uv python install 3.12

      - name: Install dependencies
        run: uv sync --locked --all-extras --group dev --group test

      - name: Run ruff check
        run: uv run ruff check .

      - name: Run ruff format check
        run: uv run ruff format --check .

      - name: Run tests
        run: uv run pytest

      - name: Prune cache
        if: always()
        run: uv cache prune --ci
```

**Fast-Failure Pattern**:
- Run ruff first (completes in seconds)
- Exit early on lint failures to save CI minutes
- Run tests only after lint passes

**Optimization Techniques**:
1. **Dependency caching**: Enabled by default with `setup-uv`
2. **Parallel testing**: Already configured with `-n auto` in pyproject.toml
3. **Cache pruning**: Reduces storage costs with `uv cache prune --ci`
4. **Fail-fast linting**: Prevents wasted test execution on syntax errors

**Performance Targets**:
- Lint: <30 seconds
- Test: 1-3 minutes (depending on test suite size)
- Total: <5 minutes for typical runs
- Cache hit: <1 minute for lint + test

**Monitoring and Improvement**:
- GitHub will add parallel steps support in mid-2026
- Use `--durations=10` to identify slow tests
- Consider separating integration tests if they become slow
- Monitor cache hit rates and adjust strategy if needed

---

## 5. Local CI Execution

### Decision
Use `act` for local GitHub Actions testing with awareness of its limitations, but don't require it for regular development workflow.

### Rationale
- **Only viable option**: No alternatives exist in 2026 for local GitHub Actions execution
- **Good enough for basic testing**: Sufficient for validating workflow syntax and basic functionality
- **Not production-equivalent**: Limitations mean it can't fully replicate GitHub Actions environment
- **Optional tool**: Pre-commit hooks and local pytest provide primary quality gates

### Alternatives Considered

**action-tmate (real-time debugging in GitHub)**
- Opens SSH session in running GitHub Actions workflow for interactive debugging
- Why not chosen: Not a local execution tool, but a complementary debugging approach
- When to use: For debugging issues that only occur in CI environment

**Docker-based custom scripts**
- Building custom Docker containers that mimic GitHub Actions environment
- Why not chosen: Significant maintenance overhead, reinventing what act already provides
- Trade-off: More control vs much higher complexity

**Just use GitHub Actions directly**
- Push to a dev branch and test in actual CI environment
- Why not chosen: Slower feedback loop, wastes CI minutes
- When to use: For final validation before merging

### Implementation Guidance

**Installing act**:
```bash
# macOS
brew install act

# Linux
curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
```

**Basic Usage**:
```bash
# Run all workflows
act

# Run specific workflow
act -W .github/workflows/ci.yml

# Run specific job
act -j test

# List available workflows
act -l
```

**Known Limitations** (as of 2026):
1. **Missing GitHub Actions features**:
   - Concurrency controls not implemented
   - Incomplete `github` context
   - No `vars` context support

2. **Environment differences**:
   - Runs in Docker containers, not full VMs
   - systemd not supported
   - Some tools may behave differently

3. **Default images lack tools**:
   - GitHub Actions runners include many tools by default
   - act's default images are minimal
   - May need custom images or manual tool installation

**Best Practices**:
1. **Don't rely on act for full validation**: Use it for quick workflow syntax checks
2. **Use pre-commit hooks as primary gate**: ruff and other checks run locally without act
3. **Test critical changes in real CI**: Push to a dev branch for complex workflow changes
4. **Keep workflows simple**: Complex workflows are harder to test locally

**Workflow Compatibility Tips**:
```yaml
# Detect if running in act
- name: Check environment
  run: |
    if [ "${{ env.ACT }}" = "true" ]; then
      echo "Running in act"
    fi

# Skip steps that don't work in act
- name: Upload coverage
  if: ${{ !env.ACT }}
  uses: codecov/codecov-action@v4
```

**When to Use act**:
- Validating workflow YAML syntax before pushing
- Testing simple workflow logic changes
- Debugging workflow structure issues

**When NOT to Use act**:
- Final validation before merge (use real CI)
- Testing platform-specific behavior
- Workflows with complex GitHub API interactions

---

## 6. GitHub Actions Security

### Decision
Implement security hardening with:
1. Read-only default GITHUB_TOKEN permissions
2. Pinned action versions (not tags like @main)
3. No secrets needed (project doesn't require API credentials for tests)
4. Branch protection on main with required status checks

### Rationale
- **Defense in depth**: Multiple layers of security prevent supply chain attacks
- **Zero trust**: Least privilege GITHUB_TOKEN limits blast radius
- **Reproducibility**: Pinned actions prevent unexpected changes
- **Simple**: No secrets management needed for this project

### Alternatives Considered

**Using @main or @master for actions**
```yaml
- uses: actions/checkout@main
```
- Why not chosen: Actions can change unexpectedly, potentially introducing vulnerabilities
- Security risk: Upstream action could be compromised or change behavior

**Full write permissions for GITHUB_TOKEN**
```yaml
permissions: write-all
```
- Why not chosen: Violates principle of least privilege
- Risk: Compromised workflow could modify repository

**No branch protection**
- Allow direct commits to main without CI passing
- Why not chosen: Defeats the purpose of CI, allows broken code in main

### Implementation Guidance

**Workflow Permissions** (add to workflow file):
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read  # Read-only access to repository contents

jobs:
  ci:
    runs-on: ubuntu-latest
    steps: [...]
```

**Action Pinning Best Practices**:
```yaml
# Good: Pin to major version with v prefix
- uses: actions/checkout@v4
- uses: astral-sh/setup-uv@v7

# Better: Pin to specific commit SHA for maximum security
- uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1

# Bad: Never use branch names
- uses: actions/checkout@main
```

**Branch Protection Configuration** (GitHub UI: Settings > Branches > Branch protection rules):
1. **Protect main branch**:
   - Require pull request before merging
   - Require status checks to pass: `ci`
   - Require branches to be up to date

2. **Additional hardening** (optional for single-user):
   - Require signed commits
   - Include administrators (enforce rules on admins too)

**Security Hardening Checklist**:
- [ ] Set `permissions: contents: read` in workflow
- [ ] Pin all actions to specific versions (not @main/@master)
- [ ] Enable branch protection on main
- [ ] Require CI to pass before merge
- [ ] No secrets in workflow files (use GitHub Secrets if needed)
- [ ] Consider enabling Dependabot for action version updates

**Recent 2026 Security Updates**:
- `pull_request_target` now uses default branch workflows (effective 2025-12-08)
- Prevents outdated/vulnerable workflows from running on PRs
- No action needed if using standard `pull_request` trigger

**Secret Management** (if needed in future):
```yaml
# Use environment secrets with required reviewers
environment: production
steps:
  - name: Use secret
    env:
      API_KEY: ${{ secrets.API_KEY }}
    run: |
      # Secret is only available if reviewer approves
```

**Code Scanning** (optional enhancement):
```yaml
# Enable CodeQL to scan workflow files for vulnerabilities
- name: Initialize CodeQL
  uses: github/codeql-action/init@v3
  with:
    languages: python
```

**Handling Untrusted Input**:
```yaml
# Bad: Directly using PR title in command
- run: echo "PR title: ${{ github.event.pull_request.title }}"

# Good: Use environment variable to prevent injection
- name: Print PR title
  env:
    PR_TITLE: ${{ github.event.pull_request.title }}
  run: echo "PR title: $PR_TITLE"
```

---

## 7. Implementation Priorities

For tandem-fetch, implement in this order:

1. **Basic CI workflow** (highest priority)
   - Single job with lint + test
   - uv-based dependency management
   - Parallel testing with pytest-xdist (already configured)

2. **Security hardening** (high priority)
   - Read-only GITHUB_TOKEN permissions
   - Pin action versions
   - Enable branch protection

3. **Optimization** (medium priority)
   - Enable uv caching (built-in to setup-uv)
   - Add `uv cache prune --ci`
   - Monitor performance

4. **Local testing with act** (low priority)
   - Install act for workflow validation
   - Document limitations
   - Use sparingly, rely on pre-commit hooks

5. **Future enhancements** (deferred)
   - Code coverage reporting
   - Separate integration test job (if needed)
   - CodeQL scanning

---

## Sources

### GitHub Actions with Python and uv
- [Using uv in GitHub Actions | uv](https://docs.astral.sh/uv/guides/integration/github/)
- [TIL: Modern Python Package CI/CD with uv, Trusted Publishing, and GitHub Actions](https://dwflanagan.com/blog/til-publishing-packages/)
- [GitHub - astral-sh/setup-uv](https://github.com/astral-sh/setup-uv)
- [A Github Actions setup for Python projects in 2025](https://ber2.github.io/posts/2025_github_actions_python/)
- [Automated Python Unit Testing Made Easy with Pytest and GitHub Actions](https://pytest-with-eric.com/integrations/pytest-github-actions/)

### Local CI Execution with act
- [GitHub - nektos/act: Run your GitHub Actions locally](https://github.com/nektos/act)
- [How to Run GitHub Actions Locally Using the act CLI Tool](https://www.freecodecamp.org/news/how-to-run-github-actions-locally/)
- [Run GitHub Actions Locally with Act: A Developer's Guide](https://dev.to/tejastn10/run-github-actions-locally-with-act-a-developers-guide-1j33)
- [Running GitHub Actions Locally with Act | Better Stack Community](https://betterstack.com/community/guides/scaling-docker/act-github-actions-tutorial/)

### GitHub Actions Security
- [7 GitHub Actions Security Best Practices - StepSecurity](https://www.stepsecurity.io/blog/github-actions-security-best-practices)
- [GitHub Actions Security Best Practices | Medium](https://medium.com/@amareswer/github-actions-security-best-practices-1d3f33cdf705)
- [How to Implement GitHub Actions Branch Protection Rules](https://oneuptime.com/blog/post/2026-01-28-github-actions-branch-protection/view)
- [Secure use reference - GitHub Docs](https://docs.github.com/en/actions/reference/security/secure-use)
- [How to secure GitHub Actions workflows - The GitHub Blog](https://github.blog/security/supply-chain-security/four-tips-to-keep-your-github-actions-workflows-secure/)

### Dependency Caching and Optimization
- [Optimizing uv in GitHub Actions: One Global Cache to Rule Them All | Medium](https://szeyusim.medium.com/optimizing-uv-in-github-actions-one-global-cache-to-rule-them-all-9c64b42aee7f)
- [Using uv in GitHub Actions | uv](https://docs.astral.sh/uv/guides/integration/github/)
- [Caching | uv](https://docs.astral.sh/uv/concepts/cache/)
- [GitHub - hynek/setup-cached-uv](https://github.com/hynek/setup-cached-uv)
- [How to Optimize GitHub Actions Performance](https://oneuptime.com/blog/post/2026-02-02-github-actions-performance-optimization/view)

### Parallel Testing with pytest-xdist
- [GitHub - pytest-dev/pytest-xdist](https://github.com/pytest-dev/pytest-xdist)
- [Parallel CI-agnostic testing using Python and Github Actions](https://blog.noveogroup.com/2022/11/parallel-ci-agnostic-testing-using-python-and-github-actions)
- [Parallel Testing Made Easy With pytest-xdist | Pytest with Eric](https://pytest-with-eric.com/plugins/pytest-xdist/)
- [Blazing fast CI with pytest-split and GitHub Actions](https://blog.jerrycodes.com/pytest-split-and-github-actions/)
- [How to Build Testing Workflows with GitHub Actions](https://oneuptime.com/blog/post/2026-01-26-testing-workflows-github-actions/view)

### CI Optimization Patterns
- [GitHub Actions in 2026: The Complete Guide](https://dev.to/pockit_tools/github-actions-in-2026-the-complete-guide-to-monorepo-cicd-and-self-hosted-runners-1jop)
- [How to Optimize GitHub Actions Performance](https://oneuptime.com/blog/post/2026-02-02-github-actions-performance-optimization/view)
- [GitHub Actions Day 6: Fail-Fast Matrix Workflows](https://www.edwardthomson.com/blog/github_actions_6_fail_fast_matrix_workflows)
- [Let's talk about GitHub Actions - The GitHub Blog](https://github.blog/news-insights/product-news/lets-talk-about-github-actions/)
- [Cutting Costs with GitHub Actions: Efficient CI Strategies](https://articles.mergify.com/cutting-costs-with-github-actions-efficient-ci-strategies/)

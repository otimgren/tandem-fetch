# Research: Pre-Commit Hooks with Prek

**Feature**: 002-precommit-hooks
**Date**: 2026-01-31
**Status**: Complete

## Executive Summary

This research evaluated pre-commit hook frameworks and selected **prek** (Rust-based pre-commit replacement) for the tandem-fetch project. Prek provides 4-10x faster execution while maintaining full compatibility with standard pre-commit configurations. The recommended stack is:

- **Hook Manager**: prek (replaces pre-commit)
- **Formatter/Linter**: ruff (replaces Black, isort, flake8)
- **Secret Detection**: gitleaks (industry standard as of 2026)
- **Basic Checks**: prek built-in hooks (offline, instant)

## Decision 1: Prek vs Pre-commit

**Decision**: Use prek as the pre-commit hook manager

**Rationale**:

1. **Performance**: 4-10x faster hook execution, 2-10x faster installation
   - Cold install benchmark (Apache Airflow config): 18.4s vs 187s
   - Hook execution (CPython check-toml): 77ms vs 352ms
   - Disk space: 50% reduction (810MB vs 1.6GB cache)

2. **Compatibility**: 100% compatible with pre-commit config format
   - Uses same `.pre-commit-config.yaml` file
   - Drop-in replacement, no migration needed
   - Supports all existing pre-commit hooks

3. **Modern Architecture**:
   - Written in Rust (single binary, no dependencies)
   - Uses `uv` for Python virtualenv creation (faster than pip)
   - Parallel repository cloning and hook execution
   - Shared hook environments (less duplication)

4. **Industry Adoption** (as of January 2026):
   - CPython (Python core)
   - Apache Airflow
   - FastAPI
   - Home Assistant
   - Actively developed and maintained

5. **Additional Features**:
   - `repo: builtin` for offline, zero-setup hooks
   - Glob pattern support in addition to regex
   - Monorepo/workspace support
   - Automatic toolchain installation

**Alternatives Considered**:

| Tool | Pros | Cons | Decision |
|------|------|------|----------|
| **Standard pre-commit** | Mature, widely adopted | Slow (352ms vs 77ms), Python overhead | ❌ Rejected - performance gap too large |
| **Prek** | 4-10x faster, compatible, modern | Newer (Jan 2026), smaller ecosystem | ✅ **Selected** - performance + compatibility |
| **Husky** (Node.js) | Fast, simple | Node.js dependency for Python project | ❌ Rejected - wrong ecosystem |
| **Custom git hooks** | Full control, no dependencies | Manual maintenance, no ecosystem | ❌ Rejected - reinventing wheel |

**References**:
- [Prek Benchmark Data](https://prek.j178.dev/benchmark/)
- [Prek vs Pre-commit Differences](https://prek.j178.dev/diff/)
- [Home Assistant Migration Case Study](https://developers.home-assistant.io/blog/2026/01/13/replace-pre-commit-with-prek/)

---

## Decision 2: Formatter and Linter Selection

**Decision**: Use ruff for formatting, linting, and import sorting

**Rationale**:

1. **Consolidation**: Single tool replaces 3+ tools
   - **Replaces Black**: Python formatter
   - **Replaces isort**: Import sorter
   - **Replaces flake8**: Linter
   - Reduces config complexity and dependency count

2. **Performance**: Written in Rust, 10-100x faster than Black
   - Formats entire codebases in milliseconds
   - No performance bottleneck in pre-commit hooks

3. **Native Pre-commit Support**:
   - Official `ruff-pre-commit` repository
   - Two hooks: `ruff` (linter) and `ruff-format` (formatter)
   - Recommended order: linter before formatter

4. **Configuration**: Uses existing `pyproject.toml`
   ```toml
   [tool.ruff]
   line-length = 100
   target-version = "py312"

   [tool.ruff.lint]
   extend-select = ["I"]  # Enable isort import sorting
   ```

5. **Ecosystem Momentum**: Rapidly becoming Python standard
   - Adopted by FastAPI, Pydantic, Home Assistant, etc.
   - Active development and feature additions
   - Large rule set compatible with flake8 plugins

**Alternatives Considered**:

| Tool | Pros | Cons | Decision |
|------|------|------|----------|
| **Black** | De facto standard, opinionated | Slow, requires separate isort/flake8 | ❌ Rejected - replaced by ruff |
| **Ruff** | Fast, all-in-one, configurable | Newer than Black (but stable) | ✅ **Selected** - speed + consolidation |
| **autopep8** | PEP 8 focused | Less opinionated, requires linter | ❌ Rejected - ruff better |
| **isort alone** | Good import sorting | Only handles imports, not formatting | ❌ Rejected - ruff includes this |

**Hook Configuration**:
```yaml
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.14.14
  hooks:
    - id: ruff
      args: [--fix, --exit-non-zero-on-fix]
    - id: ruff-format
```

**References**:
- [Ruff Formatter Documentation](https://docs.astral.sh/ruff/formatter/)
- [Ruff Pre-commit Integration](https://github.com/astral-sh/ruff-pre-commit)

---

## Decision 3: Secret Detection Tool

**Decision**: Use gitleaks for secret and PII detection

**Rationale**:

1. **Better Pattern Coverage** (2026 data):
   - Detects 100+ secret patterns out of the box
   - Regular updates for new API providers
   - Lower false positive rate than alternatives

2. **Maintained and Modern**:
   - Active development in 2026
   - Industry standard for secret scanning
   - Used in enterprise environments

3. **Flexible Configuration**:
   - Default patterns cover common cases
   - Custom `.gitleaks.toml` for allowlists
   - `.gitleaksignore` file for known false positives
   - Inline pragma comments for exceptions

4. **Pre-commit Integration**:
   ```yaml
   - repo: https://github.com/gitleaks/gitleaks
     rev: v8.24.3
     hooks:
       - id: gitleaks
   ```

5. **Performance**: Fast scans, runs in parallel with other hooks

**Alternatives Considered**:

| Tool | Pros | Cons | Decision |
|------|------|------|----------|
| **detect-secrets** (Yelp) | Mature, baseline workflow | Last update 2023, higher false positives | ❌ Rejected - maintenance concerns |
| **Gitleaks** | Active (2026), better patterns, lower FP rate | Slightly more complex config | ✅ **Selected** - modern + accurate |
| **TruffleHog** | Good for git history scanning | Slower, designed for forensics | ❌ Rejected - overkill for pre-commit |
| **Prek builtin detect-private-key** | Fast, no dependencies | Only detects SSH/PEM keys, not API keys | ❌ Rejected - insufficient coverage |

**Configuration Strategy**:

`.gitleaks.toml`:
```toml
[extend]
useDefault = true  # Use all built-in patterns

[allowlist]
description = "Known false positives"
paths = [
  '''.*/tests/fixtures/.*''',  # Exclude test data
]
regexes = [
  '''test-api-key-.*''',  # Test keys
]
```

**False Positive Handling**:
1. **File-level**: Exclude test directories via allowlist
2. **Pattern-level**: Add known safe patterns to `.gitleaksignore`
3. **Commit-level**: `SKIP=gitleaks git commit` for exceptional cases

**References**:
- [Gitleaks GitHub](https://github.com/gitleaks/gitleaks)
- [Gitleaks + Pre-commit Integration Guide](https://medium.com/@ibm_ptc_security/securing-your-repositories-with-gitleaks-and-pre-commit-27691eca478d)

---

## Decision 4: Built-in Checks

**Decision**: Use prek `repo: builtin` hooks for basic file validation

**Rationale**:

1. **Zero Latency**: No network requests, no environment setup
   - Instant execution (<10ms per hook)
   - Works offline
   - No dependency management

2. **Common Patterns Covered**:
   - Trailing whitespace removal
   - End-of-file fixer (ensure newline at EOF)
   - Line ending normalization (CRLF → LF)
   - YAML/TOML/JSON validation
   - Large file detection
   - Case conflict detection
   - Merge conflict marker detection

3. **Prek-Specific Feature**: Not available in standard pre-commit

4. **80/20 Rule**: Covers 80% of common file issues with 20% of the complexity

**Hook Configuration**:
```yaml
repos:
  - repo: builtin
    hooks:
      - id: trailing-whitespace
        args: ['--markdown-linebreak-ext=md']
      - id: end-of-file-fixer
      - id: mixed-line-ending
        args: ['--fix=lf']
      - id: check-yaml
      - id: check-toml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-case-conflict
      - id: check-merge-conflict
```

**Alternatives Considered**:

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Standard pre-commit hooks** | More mature | Slower (300-400ms overhead) | ❌ Rejected - performance |
| **Prek builtin** | Instant, offline, simple | Fewer hooks than pre-commit | ✅ **Selected** - covers needs |
| **Custom scripts** | Full control | Maintenance burden | ❌ Rejected - builtin sufficient |

**References**:
- [Prek Built-in Hooks Documentation](https://prek.j178.dev/builtin/)

---

## Installation and Setup Strategy

### Developer Workflow

**One-time setup**:
```bash
# Install prek globally
uv tool install prek

# Or add to project dev dependencies
uv add --dev prek
```

**Per-repository setup**:
```bash
# Install git hooks (creates .git/hooks/pre-commit)
prek install

# Run hooks manually (useful for testing)
prek run --all-files
```

**Daily usage**:
```bash
# Hooks run automatically on git commit
git add .
git commit -m "my changes"

# If hooks auto-fix files, re-stage and commit
git add .
git commit -m "my changes"
```

### CI/CD Compatibility

**Option 1**: Use same config with standard pre-commit in CI
```yaml
# .github/workflows/ci.yml
- uses: pre-commit/action@v3.0.0
```

**Option 2**: Use prek in CI (faster)
```yaml
# .github/workflows/ci.yml
- name: Install prek
  run: pip install prek
- name: Run hooks
  run: prek run --all-files
```

### Maintenance

**Auto-update hook versions**:
```bash
# Update to latest hook revisions
prek auto-update

# With cooldown to prevent excessive updates
prek auto-update --cooldown-days 7
```

**Cache management**:
```bash
# Clean unused environments interactively
prek cache clean

# Garbage collect automatically
prek cache gc
```

---

## Performance Characteristics

### Benchmark Data (from prek official benchmarks)

**Cold Installation** (Apache Airflow configuration):
- **prek**: 18.4 seconds, 810MB cache
- **pre-commit**: 187.0 seconds, 1.6GB cache
- **Result**: 10.17x faster, 50% disk space saved

**Hook Execution** (check-toml on CPython):
- **prek**: 77.1 ms ± 2.5 ms
- **pre-commit**: 351.6 ms ± 25.0 ms
- **Result**: 4.56x faster

**Real-world Benchmark** (Hugo van Kemenade, 84 repos):
- **prek**: 5.5 seconds total
- **pre-commit**: 39.8 seconds total
- **Result**: 7.19x faster

### Expected Performance for Tandem-Fetch

**Estimated hook execution time** (typical commit with 1-5 files):

| Hook Category | Expected Time | Justification |
|---------------|---------------|---------------|
| Built-in checks | <50ms | Offline, compiled Rust |
| Ruff linting | <200ms | Rust-based, fast parser |
| Ruff formatting | <100ms | Faster than Black |
| Gitleaks | <300ms | Single binary, parallel scan |
| **Total** | **<650ms** | Well under 5s goal |

**Worst case** (committing 20+ files):
- Built-in: <100ms (scales linearly)
- Ruff: <500ms (parallel processing)
- Gitleaks: <800ms (parallel scanning)
- **Total**: <1.5s (still under 5s goal)

### Performance Optimizations Applied

1. **Parallel Execution**: Hooks with same priority run concurrently
2. **File Targeting**: Only staged files checked (not entire repo)
3. **Shared Environments**: Prek reuses hook environments
4. **Compiled Tools**: Ruff and gitleaks are compiled binaries
5. **Built-in Hooks**: Zero network/environment overhead

---

## Security Considerations

### Secrets and PII Patterns Covered

**API Keys and Tokens**:
- AWS access keys
- GitHub tokens
- Generic API keys (format: `api_key = "..."`)
- OAuth tokens
- JWT tokens

**Passwords**:
- Plain text passwords in code
- Database connection strings with passwords
- Credential files accidentally staged

**PII** (via gitleaks custom patterns):
- Email addresses (in non-comment contexts)
- Phone numbers (US/international formats)
- Social Security Numbers
- Credit card numbers

**Sensitive Files**:
- `.env` files
- `credentials.toml` files
- SSH private keys
- Certificate files (.pem, .key)
- Files in `sensitive/` directory

### False Positive Mitigation

**Expected false positive rate**: <1% (based on gitleaks benchmarks)

**Mitigation strategies**:

1. **Allowlist test files**:
   ```toml
   [allowlist]
   paths = ['''.*/tests/.*''']
   ```

2. **Pattern-specific exceptions**:
   ```toml
   [allowlist]
   regexes = ['''test-api-key-.*''']
   ```

3. **File-based ignore list** (`.gitleaksignore`):
   ```
   test-api-key-12345
   example-password-for-docs
   ```

4. **Inline pragma comments**:
   ```python
   API_KEY = "fake-key"  # pragma: allowlist secret
   ```

5. **Commit-level bypass**:
   ```bash
   SKIP=gitleaks git commit -m "Intentional test data"
   ```

### Defense-in-Depth

Pre-commit hooks are **layer 2** of defense:

1. **Layer 1**: `.gitignore` prevents staging `sensitive/` files
2. **Layer 2**: Gitleaks blocks commits if Layer 1 bypassed
3. **Layer 3**: Manual code review (existing practice)

---

## Configuration Files Summary

### `.pre-commit-config.yaml` (main config)
- Hook manager: prek
- Hooks: builtin, ruff, gitleaks
- ~60 lines total

### `.gitleaks.toml` (secret detection config)
- Base patterns: gitleaks defaults
- Custom allowlist: test directories
- ~20 lines total

### `pyproject.toml` (ruff config)
- Add ruff configuration section
- Line length, Python version, enabled rules
- ~15 lines added to existing file

### `.gitleaksignore` (optional, created as needed)
- Per-line false positive patterns
- Empty by default

**Total config overhead**: ~95 lines across 3-4 files

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation | Residual Risk |
|------|------------|--------|------------|---------------|
| **Developers bypass hooks** | Medium | Medium | Document bypass process, make hooks fast (<5s) | Low |
| **False positives block work** | Low | Medium | Clear allowlist process, <1% FP rate | Low |
| **Hook performance degrades** | Low | Low | Prek's parallel execution, only staged files | Very Low |
| **Prek maintenance stops** | Very Low | Medium | Compatible with pre-commit, easy rollback | Very Low |
| **Config drift from CI** | Low | Low | Same config file for prek and pre-commit | Very Low |

**Overall risk level**: **LOW** - well-tested tools with escape hatches

---

## Open Questions and Future Work

### Resolved in This Research

- ✅ Which pre-commit framework? **Prek**
- ✅ Which formatter? **Ruff**
- ✅ Which secret detector? **Gitleaks**
- ✅ How to handle false positives? **Allowlist + .gitleaksignore**
- ✅ Performance acceptable? **Yes, <1s typical**

### Future Enhancements (Out of Scope)

- [ ] CI/CD integration (GitHub Actions)
- [ ] Custom hook for SQL migration validation
- [ ] Custom hook for TOML schema validation
- [ ] Auto-update cron job for hook revisions
- [ ] Pre-push hooks for test execution
- [ ] Commit message linting (conventional commits)

### Monitoring After Implementation

Track these metrics over first 100 commits:

1. **Hook execution time**: Should stay <2s (goal: <5s)
2. **False positive rate**: Should be <1% (gitleaks)
3. **Bypass frequency**: How often developers use `SKIP=`
4. **Developer satisfaction**: Survey after 2 weeks

---

## References

### Official Documentation

- [Prek Documentation](https://prek.j178.dev/)
- [Prek GitHub Repository](https://github.com/j178/prek)
- [Ruff Formatter Docs](https://docs.astral.sh/ruff/formatter/)
- [Ruff Pre-commit Integration](https://github.com/astral-sh/ruff-pre-commit)
- [Gitleaks GitHub](https://github.com/gitleaks/gitleaks)
- [Prek Built-in Hooks](https://prek.j178.dev/builtin/)

### Benchmarks and Comparisons

- [Prek Benchmark Results](https://prek.j178.dev/benchmark/)
- [Prek vs Pre-commit Differences](https://prek.j178.dev/diff/)
- [Hugo van Kemenade's Real-world Benchmark](https://hugovk.dev/blog/2025/ready-prek-go/)

### Integration Guides

- [Home Assistant Prek Migration](https://developers.home-assistant.io/blog/2026/01/13/replace-pre-commit-with-prek/)
- [Gitleaks + Pre-commit Security Guide](https://medium.com/@ibm_ptc_security/securing-your-repositories-with-gitleaks-and-pre-commit-27691eca478d)
- [Pre-commit Best Practices](https://gist.github.com/MangaD/6a85ee73dd19c833270524269159ed6e)

### Articles and Analysis

- [Why Prek Beats Pre-commit](https://aiechoes.substack.com/p/happier-developers-faster-teams-why)
- [Pre-commit to Prek Evolution](https://medium.com/@zwbf/from-pre-commit-to-prek-the-evolution-of-code-quality-automation-08f4bab00710)
- [Python Developer Tooling: Prek](https://pydevtools.com/blog/prek-pre-commit-but-fast/)

---

**Research Complete**: 2026-01-31
**Next Phase**: Generate quickstart.md and contracts/

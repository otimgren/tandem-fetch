# Feature Specification: CI Security Scanning

**Feature Branch**: `009-ci-security-scanning`
**Created**: 2026-02-28
**Status**: Draft
**Input**: User description: "Could we add some more security scanning to our CI? At least bandit, but also others if you have suggestions"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Detect Insecure Code Patterns in CI (Priority: P1)

When a developer pushes code or opens a pull request, the CI pipeline automatically scans the Python source code for common security issues — such as use of insecure functions, hardcoded credentials, overly broad exception handling, and injection risks. If any security issues are found, the CI run fails and the developer sees a clear report of what was found and where.

**Why this priority**: This is the core request — catching security vulnerabilities in the project's own code before they reach the main branch. This is the most direct and highest-impact security improvement.

**Independent Test**: Push a commit containing a known insecure pattern (e.g., use of `eval()`) and verify the CI pipeline detects it and fails with a clear report.

**Acceptance Scenarios**:

1. **Given** a pull request with no security issues, **When** the CI pipeline runs, **Then** the security scan step passes and the overall CI run succeeds.
2. **Given** a pull request containing a known insecure pattern (e.g., hardcoded password, use of `eval()`), **When** the CI pipeline runs, **Then** the security scan step fails and reports the specific file, line number, and issue description.
3. **Given** a pull request with security findings that have been intentionally suppressed via inline comments, **When** the CI pipeline runs, **Then** the suppressed findings are excluded from the report and the scan passes.

---

### User Story 2 - Detect Vulnerable Dependencies in CI (Priority: P1)

When a developer pushes code or opens a pull request, the CI pipeline automatically checks all project dependencies against known vulnerability databases. If any installed packages have known security vulnerabilities (CVEs), the CI run fails and reports which packages are affected, what the vulnerability is, and what version fixes it.

**Why this priority**: Dependencies are a major attack surface. Even if the project's own code is secure, a vulnerable dependency can introduce serious risks. This is equally important as code scanning and catches a completely different class of issues.

**Independent Test**: Temporarily pin a dependency to a version with a known CVE and verify the CI pipeline detects and reports it.

**Acceptance Scenarios**:

1. **Given** a project with all dependencies at versions without known vulnerabilities, **When** the CI pipeline runs, **Then** the dependency scan step passes.
2. **Given** a project with a dependency that has a known vulnerability, **When** the CI pipeline runs, **Then** the scan fails and reports the package name, installed version, vulnerability ID (CVE), severity, and fixed version (if available).
3. **Given** a known vulnerability has been reviewed and accepted as a false positive or non-applicable, **When** the developer adds it to an allowlist, **Then** the scan passes and excludes that specific vulnerability from future reports.

---

### User Story 3 - Run Security Scans Locally (Priority: P2)

A developer can run the same security scans locally before pushing, using a simple command. This allows catching and fixing security issues early without waiting for CI feedback.

**Why this priority**: Supports a fast feedback loop. Less critical than CI enforcement (which is the safety net), but valuable for developer productivity.

**Independent Test**: Run the local security scan command on a codebase with a known issue and verify it produces the same report as CI would.

**Acceptance Scenarios**:

1. **Given** a developer wants to check for security issues before pushing, **When** they run the local security scan command, **Then** they see the same results as the CI pipeline would produce.
2. **Given** a developer has fixed all security issues locally, **When** they push and CI runs, **Then** the CI security scan also passes.

---

### Edge Cases

- What happens when the vulnerability database is temporarily unavailable? The dependency scan should fail gracefully with a clear error rather than silently passing.
- What happens when a new vulnerability is published for an existing dependency between pushes? The next CI run will catch it — no retroactive scanning of existing branches is needed.
- What happens when a security finding is in test code vs. production code? All code should be scanned by default, but the project may choose to exclude test fixtures or generated files.
- What happens when there are no Python files to scan? The scan should pass without error (no files = no findings).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The CI pipeline MUST run a static analysis security scan on all Python source code for every push to main and every pull request.
- **FR-002**: The CI pipeline MUST check all project dependencies for known security vulnerabilities for every push to main and every pull request.
- **FR-003**: The static analysis scan MUST detect common security issues including: use of insecure functions, hardcoded secrets, injection risks, and overly permissive exception handling.
- **FR-004**: The dependency vulnerability scan MUST report: package name, installed version, vulnerability identifier (CVE), severity level, and fixed version when available.
- **FR-005**: Both security scans MUST cause the CI pipeline to fail if any issues are found, preventing merge until resolved.
- **FR-006**: Developers MUST be able to suppress specific static analysis findings with inline comments for intentional exceptions.
- **FR-007**: Developers MUST be able to maintain an allowlist for accepted dependency vulnerabilities (e.g., false positives or non-applicable findings).
- **FR-008**: Developers MUST be able to run all security scans locally using the same configuration as CI.
- **FR-009**: Security scan reports MUST include the file path, line number, issue description, and severity for each finding.
- **FR-010**: The security scanning steps MUST not significantly increase CI pipeline duration (should add no more than 30 seconds to total CI time).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of pull requests are automatically scanned for code security issues and dependency vulnerabilities before merge.
- **SC-002**: Security findings include actionable details (file, line, description, severity) so developers can fix issues without additional research.
- **SC-003**: Developers can run the same security checks locally in under 15 seconds.
- **SC-004**: The CI pipeline completes security scans within 30 seconds, keeping the total CI time fast.
- **SC-005**: Zero known dependency vulnerabilities exist in the main branch (all findings are either resolved or explicitly allowlisted with justification).

## Assumptions

- The project already has a working CI pipeline (GitHub Actions) that runs linting and tests. Security scanning will be added as additional steps to this existing pipeline.
- The existing local CI script (`.github/scripts/run-ci-locally.sh`) will be extended to include the new security scans.
- Gitleaks (secret detection) is already configured in pre-commit hooks and does not need to be duplicated in CI.
- The scans should cover the `src/` directory for production code. Test files may also be scanned since they can reveal patterns that leak into production code.
- The project is a single-user local tool, so compliance-level scanning (SBOM generation, license auditing) is out of scope.

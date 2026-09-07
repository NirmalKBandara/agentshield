# CI/CD Security Gates

GitHub Actions runs on every pull request and every push to `main`. The workflow
uses read-only repository permissions and treats each required security check as
a blocking job.

| Job | Gate |
| --- | --- |
| Backend | PostgreSQL migration, Ruff, and the complete backend test suite |
| Frontend | Clean install, unit tests, ESLint, TypeScript, and production build |
| Compose | Configuration, image builds, health-gated startup, and cross-service tests |
| Semgrep | Python and TypeScript community rules; any finding fails the job |
| Gitleaks | Full Git history is scanned; a detected secret fails the job |
| Python audit | Runtime requirements are checked against vulnerability advisories |
| npm audit | High or critical runtime dependency advisory fails the job |
| Trivy | High or critical fixed filesystem dependency or IaC issue fails the job |

`ignore-unfixed` is enabled for Trivy so the release is not permanently blocked
on an advisory with no available remediation. Medium and low findings remain
useful review input but do not block the MVP. Semgrep runs without telemetry and
Gitleaks receives only GitHub's scoped workflow token.

Branch protection should require all CI jobs before merge. Dependabot or a
scheduled maintenance issue should update action versions and dependencies;
security-tool failures must be triaged, not bypassed with `continue-on-error`.

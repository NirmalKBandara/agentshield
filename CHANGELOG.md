# Changelog

## v1.0.0 — 2026-09-07

First complete AgentShield MVP release.

### Added

- Next.js dashboard, playground, security-event, tool-call, policy, and Red Team
  workspaces.
- FastAPI agent API, strict model decision schema, deterministic offline provider,
  optional Ollama provider, and four simulated demo tools.
- Fail-closed gateway controls for tool registration and arguments,
  deny-by-default permissions, prompt injection, sensitive-data exfiltration,
  SSRF, refund limits, and request-rate limits.
- Normalized risk scores, stable reason codes, correlated audit records, and
  PostgreSQL migrations.
- Six reproducible attack simulations, unit/integration/adversarial tests,
  Docker Compose, health checks, GitHub Actions security gates, STRIDE threat
  model, product screenshots, and demo documentation.

### Security

- Blocks canonical and legacy decimal, hexadecimal, octal, shortened,
  percent-encoded, and IPv4-mapped loopback URL representations.
- Normalizes Unicode compatibility forms and strips invisible formatting
  controls before prompt/PII pattern evaluation.
- Masks known secret-bearing argument keys in investigation responses.

### Known limitations

This is a local demonstration with simulated tools, one seeded agent, heuristic
content detectors, a process-local rate limiter, and no end-user authentication.
See [docs/limitations.md](docs/limitations.md) before adapting it to real tools.

# MVP Limitations

- The default decision provider is a deterministic rules router. Ollama is
  optional, local, and receives no production-readiness claim.
- Prompt-injection and sensitive-data detection use explainable patterns. Novel
  languages, encodings, semantic attacks, and domain-specific identifiers can
  evade them or cause false positives.
- The rate limiter is process-local and resets on restart. Multiple API replicas
  require a shared atomic store such as Redis.
- There is one seeded support-agent identity and no login, tenant boundary,
  enterprise SSO, or administrative RBAC. Do not expose the MVP publicly.
- Demo customer lookup, email, refund, and URL fetch are fixtures with no real
  side effects. Real integrations require connector credentials, idempotency,
  egress allowlists, DNS/redirect revalidation, and human approval for
  high-impact actions.
- PostgreSQL audit rows are not signed or written to immutable storage. A
  database administrator can alter them.
- Known sensitive argument keys are masked in investigation views, but arbitrary
  free text can still contain unrecognized secrets or personal data.
- Compose is a single-host developer deployment without TLS termination,
  autoscaling, backup automation, centralized observability, or high
  availability.
- Security scanners reduce risk but do not replace review, penetration testing,
  dependency maintenance, or deployment-specific hardening.

These constraints keep the four-week project focused. The security architecture
is intentionally layered so stronger identity, distributed policy services,
real connectors, tamper-evident logs, and network enforcement can be added
without delegating authorization to the model.

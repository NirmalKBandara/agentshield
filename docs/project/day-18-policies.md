# Day 18 — Policies

Day 18 turns the existing database-backed security configuration into a safe,
auditable administration workflow.

## Delivered

- A typed policy overview API for active runtime limits, agent tool permissions,
  and the newest policy audit records.
- Validated partial updates for refund amounts and per-agent request rates, with
  strict server-side bounds and matching browser feedback.
- Permission toggles that update the same deny-by-default rows consulted by the
  runtime gateway.
- A gateway control that blocks refunds above the configured maximum and calls
  above the configured per-minute allowance.
- Immutable audit records containing request ID, actor, action, resource, and
  before/after values for every effective policy mutation.
- A responsive `/policies` workspace with loading, empty, error, and success
  states, plus recent-change visibility.
- An Alembic migration that creates the audit table and seeds a default policy.

The in-memory rate counter is intentionally scoped to one application process
for this local MVP. A distributed deployment should replace it with a shared
store such as Redis.

## Verification

```bash
backend/.venv/bin/ruff check backend/app backend/tests
backend/.venv/bin/pytest backend/tests
npm --prefix frontend test
npm --prefix frontend run lint
npm --prefix frontend run build
```

## Acceptance status

All Day 18 tasks in the four-week MVP plan are complete. Day 19 is the next
milestone and focuses on the Red Team Lab.

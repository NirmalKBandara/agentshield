# Day 19 — Red Team Lab

Day 19 adds a safe, repeatable attack workspace for demonstrating how
AgentShield stops unsafe tool requests before execution.

## Delivered

- Six deterministic scenarios covering prompt injection, unauthorized tools,
  sensitive-data exfiltration, SSRF, dangerous refund parameters, and rate abuse.
- `GET /api/v1/red-team/scenarios` and `POST /api/v1/red-team/run` APIs with
  typed payloads and request correlation.
- Gateway controls for prompt override phrases, sensitive-data email attempts,
  and private or link-local URL destinations.
- Reuse of the existing permission and policy-limit controls, including an
  isolated rate limiter so repeated demos remain predictable.
- A responsive `/red-team` page showing each payload, requested action, final
  decision, reason, triggered controls, risk score, and audit identifiers.
- A `red_team_attack_blocked` security event for every completed simulation.

The lab only authorizes simulated requests. It never invokes the email, refund,
URL-fetch, or customer tools, so the prepared attacks cannot create side effects.

## Verification

```bash
backend/.venv/bin/ruff check backend/app backend/tests
backend/.venv/bin/pytest backend/tests
npm --prefix frontend test
npm --prefix frontend run lint
npm --prefix frontend run build
```

## Acceptance status

All Day 19 tasks in the four-week MVP plan are complete. Day 20 is the next
milestone and focuses on improving and normalizing the risk engine.

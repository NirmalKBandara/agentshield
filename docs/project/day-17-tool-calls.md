# Day 17 — Tool Calls

Day 17 makes agent tool usage transparent, searchable, and safe to inspect.

## Delivered

- A typed Tool Calls API with bounded pagination and filters for agent, tool,
  status, and gateway decision.
- Agent identity, normalized decisions, linked-event risk scores, duration, and
  timestamps for every audit record.
- Recursive masking of secret-bearing argument fields before data leaves the
  backend, including secrets nested in objects and lists.
- A responsive audit table with agent, tool, sanitized argument, decision,
  risk, and timestamp columns plus an accessible detail view.
- Direct investigation links from blocked calls to their related security
  events, with the tool-call filter preserved through the Next.js proxy.
- Backend API and frontend presentation regression tests.

## Verification

```bash
backend/.venv/bin/pytest backend/tests
npm --prefix frontend test
npm --prefix frontend run lint
npm --prefix frontend run build
```

## Acceptance status

All Day 17 tasks in the four-week MVP plan are complete. Day 18 is the next
milestone and focuses on agent security policy management.

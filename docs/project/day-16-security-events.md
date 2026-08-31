# Day 16 — Security Events

Day 16 turns stored security findings into an operational investigation view.

## Delivered

- Security Events API with bounded result sets and filters for severity, event
  type, and minimum risk score.
- A security-events table with readable reasons, consistent severity badges,
  timestamps, and risk scores.
- Filters for severity, event type, and minimum risk score.
- An accessible event detail view containing the source message, reason,
  associated tool call, and structured details.
- A same-origin Next.js proxy that forwards only supported API parameters.
- Backend API and frontend presentation regression tests.

## Verification

```bash
backend/.venv/bin/pytest backend/tests
npm --prefix frontend test
npm --prefix frontend run lint
npm --prefix frontend run build
```

## Acceptance status

All Day 16 tasks in the four-week MVP plan are complete. Day 17 is the next
milestone and focuses on the tool-call investigation workflow.

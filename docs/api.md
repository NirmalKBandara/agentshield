# REST API Guide

FastAPI publishes the live OpenAPI contract at <http://localhost:8000/docs> and
the machine-readable schema at <http://localhost:8000/openapi.json>. JSON error
responses include `request_id`; clients may send `X-Request-ID` using 1–128
letters, digits, dots, underscores, colons, or hyphens.

## Health and agent

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v1/health` | Process liveness without a database dependency |
| GET | `/api/v1/ready` | Database readiness (`503` when unavailable) |
| POST | `/api/v1/agent/run` | Route a 1–4,000 character prompt through the model decision and gateway |
| GET | `/api/v1/agent/tool-calls?limit=50` | Recent raw agent audit entries, maximum 200 |

```bash
curl --fail-with-body -X POST http://localhost:8000/api/v1/agent/run \
  -H 'content-type: application/json' \
  -H 'X-Request-ID: readme-safe-1001' \
  -d '{"prompt":"Look up customer 1001"}'
```

## Investigation

| Method | Path | Important filters |
| --- | --- | --- |
| GET | `/api/v1/dashboard/summary` | Aggregated request and event counters |
| GET | `/api/v1/dashboard/recent-events` | `limit` |
| GET | `/api/v1/security-events` | `severity`, `event_type`, `tool`, `decision`, `min_risk_score`, `tool_call_id`, `limit`, `offset` |
| GET | `/api/v1/security-events/{uuid}` | One full event |
| GET | `/api/v1/tool-calls` | `status`, `decision`, `tool`, `agent`, `limit`, `offset` |

## Policies and Red Team Lab

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v1/policies` | Current permissions, limits, and change history |
| PATCH | `/api/v1/policies/limits` | Update bounded refund/rate limits with actor/reason audit data |
| PATCH | `/api/v1/policies/permissions/{permission_id}` | Enable or deny one stored tool permission |
| GET | `/api/v1/red-team/scenarios` | List the six immutable scenarios |
| POST | `/api/v1/red-team/run` | Evaluate and record one scenario by `scenario_id` |

Use the interactive contract for exact request/response schemas. Invalid JSON,
unknown fields, malformed UUIDs, and out-of-range query values return a
correlated validation response and never reach tool dispatch.

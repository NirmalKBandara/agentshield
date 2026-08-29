# Architecture

## Runtime flow

```text
Browser
  │ GET /api/backend-health
  ▼
Next.js route handler
  │ GET $BACKEND_URL/api/v1/health
  ▼
FastAPI
  │ SELECT 1 (readiness only)
  ▼
PostgreSQL
```

The browser calls a same-origin Next.js endpoint. The route handler uses the
server-only `BACKEND_URL`, so Docker's internal hostname (`backend`) is never
sent to the browser and CORS is not required for this primary flow.

FastAPI still configures an explicit `CORS_ORIGINS` allowlist for intentional
direct browser calls during development.

## Health endpoints

- `GET /api/v1/health` is liveness. It proves the API process can serve requests
  and deliberately has no database dependency.
- `GET /api/v1/ready` is readiness. It runs `SELECT 1` and returns HTTP 503 if
  PostgreSQL is unavailable.
- `GET /api/backend-health` is the frontend proxy. It returns FastAPI's liveness
  response or HTTP 503 if the upstream cannot be reached within five seconds.

## Container startup order

Compose waits for PostgreSQL readiness before starting FastAPI, then waits for
FastAPI readiness before starting Next.js. Healthchecks provide observable
runtime state; `depends_on` alone would only describe process startup order.

## Demo agent flow (Week 1)

```text
Browser → Next.js /api/agent → FastAPI /api/v1/agent/run
                                      ↓
                   provider → strict JSON decision parser
                                      ↓
                   AgentShield gateway → security controls
                                      ↓
                  private tool dispatch → Pydantic validation
                                      ↓
              get_customer | send_email | issue_refund | fetch_url
                                      ↓
                    PostgreSQL tool-call audit record
```

The default provider is an offline deterministic request router. Ollama is an
optional local provider using the same strict decision schema. A model cannot
call a Python function directly: `AgentService` receives a `ToolGateway`, and
the registry exposes no public execution method. The gateway produces a final
allow/block decision before its private dispatcher can run. Security controls
fail closed if they raise an error. Unknown tool names and invalid arguments stop
before execution. All four tools use fictional fixtures; email, refunds, and URL
fetching are simulations with no external side effects.

FastAPI assigns or validates an `X-Request-ID` for every request. Successful and
failed tool attempts store that ID with their arguments, result/error, status,
and duration. `GET /api/v1/agent/tool-calls` exposes a bounded newest-first view
for the Week 1 demo. This is observability for the deliberately insecure initial
flow; security-gateway enforcement begins in Week 2.

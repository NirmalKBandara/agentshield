# Demo and Interview Guide

## Preparation

```bash
cp .env.example .env
docker compose up --build --wait
RUN_INTEGRATION=1 python3 -m unittest tests.integration.test_stack
```

Open the dashboard, playground, Red Team Lab, security events, tool calls, and
policies in separate tabs. Keep FastAPI `/docs` available as implementation
evidence. Never use real customer data or credentials.

## Five-minute version

1. **Problem (30 seconds).** Models can propose actions, but they should not be
   trusted to authorize their own access to APIs, data, email, or refunds.
2. **Architecture (45 seconds).** Show the architecture diagram. Emphasize that
   every tool call crosses a deterministic, fail-closed gateway outside the LLM.
3. **Safe path (45 seconds).** In Playground, look up customer 1001. Show the
   allowed result and correlated audit entry.
4. **Attack (90 seconds).** Run prompt injection and SSRF in Red Team Lab. Show
   BLOCK, stable reason codes, score, and the stored security event.
5. **Policy (45 seconds).** Show deny-by-default refund permission and the
   configurable refund/rate limits with immutable change history.
6. **Close (45 seconds).** Mention adversarial tests, STRIDE, container health,
   CI scanners, and the explicit MVP limitations.

## Ten-minute version

Use the five-minute flow, then add:

- the strict model-output and Pydantic tool schemas;
- all six attacks and why each exercises a separate layer;
- a tool-call-to-security-event investigation using the request ID;
- risk scoring as severity/explanation, not authorization by threshold;
- the CI gates and why control failure denies execution;
- residual risks: heuristic text detection, process-local rate limiting, no auth,
  simulated connectors, and no tamper-evident audit store.

## Interview explanation

AgentShield treats the LLM as an untrusted decision proposer. The model may
select a tool and arguments, but registered schemas, permissions, policies,
content/network controls, and rate limits determine whether the action can run.
This applies least privilege and deny-by-default at the side-effect boundary.
The LLM cannot reliably enforce authorization because its output is
probabilistic and prompt-controlled; deterministic code and trusted identity
must make that decision. STRIDE exposed spoofing and repudiation gaps from the
MVP's missing authentication, disclosure risks in free-form logs, SSRF risk in
future real networking, and availability tradeoffs from fail-closed behavior.

The next production steps are authenticated users/service identities,
multi-tenant policy isolation, a distributed limiter, tamper-evident event
export, real egress enforcement, connector-specific approvals/idempotency, and
continuous evaluation of detector false positives and bypasses.

## Demo acceptance record

For a release rehearsal, record the commit/tag, date, operator, six scenario
decisions, test command results, and any deviations. A release is acceptable
only when the safe call succeeds, all six attacks block, events are stored, and
the automated checks pass.

# Day 20 — Explainable Risk Engine

Day 20 replaces isolated, maximum-only control scores with one deterministic,
explainable assessment for every gateway decision.

## Delivered

- Central weights for prompt injection, unauthorized and unknown tools,
  sensitive-data exfiltration, SSRF, dangerous refund parameters, rate abuse,
  and security-control failures.
- Additive scoring across independent signals, duplicate-reason protection, and
  normalization to the inclusive 0–100 range.
- Documented risk bands: 0–29 low, 30–59 medium, 60–79 high, and 80–100 critical.
- Validated environment settings for deployments that need different medium,
  high, or critical thresholds.
- Stable reason codes and human-readable explanations on final decisions,
  blocked tool-call audit data, security events, and Red Team results.
- Fail-closed handling for unregistered tools and failed security controls.
- Unicode-normalized prompt-injection matching and category-based sensitive-data
  matching to improve coverage without treating ordinary security discussion or
  a single contact term as an attack.

## False-positive and false-negative review

Benign tests cover normal prompts, a single email-related term, authorized
tools, safe public-style demo URLs, refunds within policy, and requests below
the configured rate. Attack-path tests cover all six Red Team scenarios,
additional instruction-override wording, unknown tools, multi-signal
aggregation, duplicate signals, score capping, and control failures.

The gateway continues to enforce an explicit block from a policy or security
control even when its isolated contribution falls below the high-risk band. The
score explains severity; it does not weaken a deny decision.

## Verification

```bash
backend/.venv/bin/ruff check backend/app backend/tests
backend/.venv/bin/pytest backend/tests
npm --prefix frontend test
npm --prefix frontend run lint
npm --prefix frontend run build
git diff --check
```

## Acceptance status

All Day 20 tasks in the four-week MVP plan are complete. Day 21 is the next
milestone and focuses on UI polish and the Week 3 review.

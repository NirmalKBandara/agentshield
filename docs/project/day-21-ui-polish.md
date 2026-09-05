# Day 21 — UI Polish and Week 3 Review

Day 21 makes the investigation workspaces easier to navigate and keeps useful
context visible when data is loading, empty, or unavailable.

## Delivered

- Shared navigation for Home, Dashboard, Playground, Security Events, Tool Calls,
  Policies, and Red Team Lab, with an active-page indicator and skip link.
- Dashboard styling aligned with the application's theme, clear security metrics,
  readable event severity, and links into the investigation workspaces.
- Recoverable error states, descriptive empty states, and announced loading states.
- Responsive navigation, filters, cards, and horizontally scrollable audit tables.
- Consistent risk labels using the backend's assessment for Red Team results.

## Week 3 acceptance review

| Area | Evidence |
| --- | --- |
| Dashboard | Summary metrics and recent-event workspace; loading, empty, and error states |
| Security Events | Filter and detail API tests; browser workspace checks |
| Tool Calls | Audit serialization, sanitization, and filter tests; browser workspace checks |
| Policies | Permission updates, validated limits, and audit-history API tests |
| Red Team Lab | Scenario listing, blocked result, and stored-event API tests |
| Six attacks | `test_each_scenario_returns_a_block_with_controls` runs every scenario |

## Verification

- Backend Ruff: passed. Pytest: 83 passed; one opt-in PostgreSQL test skipped.
- Frontend: 17 tests passed; ESLint and production build passed.
- Docker Compose configuration and `git diff --check`: passed.
- Chromium smoke review at 390px and 1280px: all seven routes checked with empty,
  failed, and populated mocked API responses. Navigation remains available,
  active-page indicators are correct, and no page-level horizontal overflow or
  runtime exceptions were observed. Dashboard screenshots were visually reviewed.

Browser fixtures validate presentation independently of the backend. A live
Docker/PostgreSQL integration run was unavailable because the Docker daemon is
not running. Screen-reader behavior and full accessibility compliance were not
certified. The Week 3 checkboxes record implemented behavior supported by the
available API, frontend, and browser checks; they do not imply deployment approval.

## Next milestone

Day 22 is threat modeling: architecture, assets, trust boundaries, STRIDE,
mitigations, and residual risks in `docs/threat-model.md`.

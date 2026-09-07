# Day 23 — Unit and Integration Testing

The test suite covers the independent security controls, fail-closed gateway,
API validation and error contracts, database models/migrations, permission and
policy stores, all four demo tools, negative paths, and boundary values.

The stack integration test now proves more than health: a safe agent request
crosses Next.js/FastAPI's application boundary, passes through the gateway,
executes the registered demo tool, and appears in the PostgreSQL audit API with
the same request ID.

Validation commands:

```bash
backend/.venv/bin/ruff check backend
backend/.venv/bin/pytest backend/tests
npm --prefix frontend test
RUN_INTEGRATION=1 python3 -m unittest tests.integration.test_stack
```

The final command intentionally requires the running Compose stack.

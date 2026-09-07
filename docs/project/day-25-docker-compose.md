# Day 25 — Docker

The MVP includes multi-stage backend and frontend images, PostgreSQL 17, a
three-service Compose application, dependency-aware health checks, and the
named `postgres_data` volume. Both application containers run as unprivileged
users. The deterministic rules provider is the default; the local Ollama
configuration is documented in the setup guide and exposed through safe
environment templates.

Static validation:

```bash
docker compose config --quiet
```

Runtime validation on a host with Docker Engine running:

```bash
cp .env.example .env
docker compose up --build --wait
docker compose ps
RUN_INTEGRATION=1 python3 -m unittest tests.integration.test_stack
```

The stack deliberately does not embed or download an LLM. `MODEL_PROVIDER=rules`
keeps the demo reproducible and offline; `MODEL_PROVIDER=ollama` connects to a
separately managed local Ollama service.

The CI Compose job performs this runtime validation on every change, prints
container logs on failure, and always removes its containers and test volume.

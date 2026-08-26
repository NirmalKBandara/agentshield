# AgentShield

AgentShield is an AI-agent security gateway starter repository. This bootstrap
delivers a working Next.js frontend, FastAPI backend, PostgreSQL database, and
Docker Compose development stack.

## End-of-day result

- Next.js frontend: <http://localhost:3000>
- FastAPI API: <http://localhost:8000>
- Interactive API docs: <http://localhost:8000/docs>
- PostgreSQL: `localhost:5432`
- Browser → Next.js proxy → FastAPI communication is visible on the home page.
- FastAPI exposes separate liveness and database-readiness checks.
- Unit tests, an opt-in integration test, Docker healthchecks, and CI are included.

## Repository layout

```text
agentshield/
├── frontend/          # Next.js App Router application
├── backend/           # FastAPI application and API tests
├── docs/              # Architecture, setup, and Git workflow guides
├── tests/             # Cross-service integration tests
├── docker/            # Container build definitions
├── .env.example       # Safe environment-variable template
└── docker-compose.yml # PostgreSQL + API + web stack
```

## Quick start with Docker

Requirements: Docker Engine with Docker Compose v2.

```bash
cp .env.example .env
docker compose up --build
```

Open <http://localhost:3000>. The page calls the Next.js route
`/api/backend-health`, which calls FastAPI at `/api/v1/health` using the
server-only `BACKEND_URL` variable.

Verify the services directly:

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/ready
curl http://localhost:3000/api/backend-health
```

Stop the stack while preserving PostgreSQL data:

```bash
docker compose down
```

To also remove the local database volume:

```bash
docker compose down --volumes
```

## Run services without Docker

Start PostgreSQL first, then follow [docs/setup.md](docs/setup.md). In short:

```bash
cp backend/.env.example backend/.env
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements-dev.txt
backend/.venv/bin/uvicorn app.main:app --reload --app-dir backend
```

In a second terminal:

```bash
cp frontend/.env.local.example frontend/.env.local
npm --prefix frontend install
npm --prefix frontend run dev
```

## Tests and validation

```bash
backend/.venv/bin/pytest backend/tests
npm --prefix frontend test
npm --prefix frontend run lint
npm --prefix frontend run build
docker compose config
RUN_INTEGRATION=1 python3 -m unittest tests.integration.test_stack
```

The integration test expects the Compose stack to already be running.

## Environment variables

Copy templates before local use. Real `.env` files are ignored by Git.

| Variable | Used by | Purpose |
| --- | --- | --- |
| `POSTGRES_DB` | Compose | Database name |
| `POSTGRES_USER` | Compose | Database user |
| `POSTGRES_PASSWORD` | Compose | Local database password |
| `DATABASE_URL` | FastAPI | Async SQLAlchemy PostgreSQL URL |
| `CORS_ORIGINS` | FastAPI | Comma-separated allowed browser origins |
| `BACKEND_URL` | Next.js server | Internal FastAPI base URL; never exposed to browser JS |

## Git and GitHub workflow

The repository uses `main` plus short-lived branches such as `feat/*`,
`fix/*`, `docs/*`, and `chore/*`. See [docs/git-workflow.md](docs/git-workflow.md)
for the exact commands, PR flow, and recommended branch protection.

## More documentation

- [Local development guide](docs/setup.md)
- [Architecture and request flow](docs/architecture.md)
- [Git and GitHub guide](docs/git-workflow.md)

## License

MIT — see [LICENSE](LICENSE).

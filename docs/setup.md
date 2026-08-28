# Local development guide

## Prerequisites

- Node.js 22 or newer and npm
- Python 3.13 or newer
- PostgreSQL 17, or Docker with Compose v2

## Option A: run the complete stack in Docker

```bash
cp .env.example .env
docker compose up --build
docker compose ps
```

Open <http://localhost:3000>. Use `docker compose logs -f backend frontend` to
follow application logs.

## Option B: run applications on the host

Start only PostgreSQL:

```bash
cp .env.example .env
docker compose up -d db
```

Create the backend environment:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/pip install --upgrade pip
backend/.venv/bin/pip install -r backend/requirements-dev.txt
cp backend/.env.example backend/.env
backend/.venv/bin/alembic -c backend/alembic.ini upgrade head
backend/.venv/bin/uvicorn app.main:app --reload --app-dir backend
```

In another terminal, start the frontend:

```bash
cp frontend/.env.local.example frontend/.env.local
npm --prefix frontend install
npm --prefix frontend run dev
```

## Validation

```bash
curl --fail http://localhost:8000/api/v1/health
curl --fail http://localhost:8000/api/v1/ready
curl --fail http://localhost:8000/health
curl --fail -X POST http://localhost:8000/api/v1/agent/run \
  -H 'X-Request-ID: local-demo-1002' \
  -H 'content-type: application/json' \
  -d '{"prompt":"Show customer 1002"}'
curl --fail 'http://localhost:8000/api/v1/agent/tool-calls?limit=10'
curl --fail http://localhost:3000/api/backend-health
backend/.venv/bin/ruff check backend
backend/.venv/bin/pytest backend/tests
npm --prefix frontend test
npm --prefix frontend run lint
npm --prefix frontend run build
docker compose config --quiet
```

## Troubleshooting

- `backend` resolves only inside the Compose network. Host-based Next.js must
  use `BACKEND_URL=http://localhost:8000`.
- If port 5432, 8000, or 3000 is already used, change its value in root `.env`.
- A liveness success with a readiness failure means FastAPI is running but
  PostgreSQL is unavailable or `DATABASE_URL` is incorrect.
- Never commit `.env`; only commit the provided example files.

## Model provider

`MODEL_PROVIDER=rules` is the MVP default: a deterministic local router with no
network, account, or model download requirement. It recognizes the four demo
request shapes and is stable in CI. To experiment with a locally installed
Ollama server, set `MODEL_PROVIDER=ollama` and configure `OLLAMA_BASE_URL` and
`OLLAMA_MODEL`. Malformed model JSON fails closed and no tool is executed.

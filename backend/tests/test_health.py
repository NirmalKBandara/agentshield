import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes import health as health_routes
from app.main import app


@pytest.mark.asyncio
async def test_liveness_endpoint() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"status": "ok", "service": "agentshield-api"}


@pytest.mark.asyncio
async def test_unversioned_health_alias() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_readiness_when_database_is_connected(monkeypatch) -> None:
    async def database_is_ready() -> bool:
        return True

    monkeypatch.setattr(health_routes, "database_is_ready", database_is_ready)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/ready")

    assert response.status_code == 200
    assert response.json()["database"] == "connected"


@pytest.mark.asyncio
async def test_readiness_when_database_is_unavailable(monkeypatch) -> None:
    async def database_is_ready() -> bool:
        return False

    monkeypatch.setattr(health_routes, "database_is_ready", database_is_ready)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == "Database is not ready"
    assert response.json()["request_id"] == response.headers["X-Request-ID"]

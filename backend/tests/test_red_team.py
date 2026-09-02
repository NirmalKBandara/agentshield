import uuid
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_session
from app.main import app


class FakeRedTeamSession:
    def __init__(self) -> None:
        self.runs = []
        self.commits = 0

    def add(self, value) -> None:
        value.id = uuid.uuid4()
        value.created_at = datetime.now(UTC)
        self.runs.append(value)

    async def commit(self) -> None:
        self.commits += 1

    async def refresh(self, _) -> None:
        return None


@pytest.fixture
async def red_team_client():
    session = FakeRedTeamSession()

    async def override_session():
        yield session

    app.dependency_overrides[get_session] = override_session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client, session
    finally:
        app.dependency_overrides.pop(get_session, None)


async def test_lists_six_reproducible_scenarios(red_team_client) -> None:
    client, _ = red_team_client

    response = await client.get("/api/v1/red-team/scenarios")

    assert response.status_code == 200
    scenarios = response.json()
    assert len(scenarios) == 6
    assert {scenario["id"] for scenario in scenarios} == {
        "prompt-injection",
        "unauthorized-tool",
        "pii-exfiltration",
        "ssrf",
        "dangerous-parameter",
        "rate-limit-abuse",
    }
    assert all(scenario["payload"] for scenario in scenarios)
    assert all(scenario["requested_action"] for scenario in scenarios)


async def test_runs_and_stores_attack_result(red_team_client) -> None:
    client, session = red_team_client

    response = await client.post(
        "/api/v1/red-team/run",
        json={"scenario_id": "ssrf"},
        headers={"X-Request-ID": "red-team-run-1"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["scenario_id"] == "ssrf"
    assert result["decision"] == "block"
    assert result["score"] == 100
    assert result["triggered_controls"] == ["network-destination-policy"]
    assert result["request_id"] == "red-team-run-1"
    assert session.commits == 1
    assert len(session.runs) == 1
    assert session.runs[0].event_type == "red_team_attack_blocked"
    assert session.runs[0].details["scenario_id"] == "ssrf"


async def test_each_scenario_returns_a_block_with_controls(red_team_client) -> None:
    client, _ = red_team_client
    scenario_ids = [item["id"] for item in (await client.get("/api/v1/red-team/scenarios")).json()]

    for scenario_id in scenario_ids:
        response = await client.post("/api/v1/red-team/run", json={"scenario_id": scenario_id})
        assert response.status_code == 200
        result = response.json()
        assert result["decision"] == "block"
        assert result["triggered_controls"]
        assert 1 <= result["score"] <= 100


async def test_unknown_scenario_is_not_stored(red_team_client) -> None:
    client, session = red_team_client

    response = await client.post("/api/v1/red-team/run", json={"scenario_id": "does-not-exist"})

    assert response.status_code == 404
    assert session.commits == 0
    assert session.runs == []

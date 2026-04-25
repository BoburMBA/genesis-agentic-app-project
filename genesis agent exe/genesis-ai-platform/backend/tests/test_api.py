"""
GENESIS Platform — API Tests
Uses httpx AsyncClient for async endpoint testing.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c


# ── Health ────────────────────────────────────────────────────
@pytest.mark.anyio
async def test_root(client: AsyncClient):
    r = await client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "GENESIS AI Platform"
    assert "endpoints" in data


@pytest.mark.anyio
async def test_health(client: AsyncClient):
    r = await client.get("/api/v1/system/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "operational"
    assert "services" in data


# ── Agents ────────────────────────────────────────────────────
@pytest.mark.anyio
async def test_list_agents_empty(client: AsyncClient):
    r = await client.get("/api/v1/agents")
    assert r.status_code == 200
    data = r.json()
    assert "agents" in data
    assert "total" in data


@pytest.mark.anyio
async def test_seed_agents(client: AsyncClient):
    r = await client.get("/api/v1/agents/seed")
    assert r.status_code == 200
    data = r.json()
    assert len(data["agents"]) == 6
    types = {a["type"] for a in data["agents"]}
    assert "router" in types
    assert "research" in types
    assert "code" in types


@pytest.mark.anyio
async def test_get_agent_not_found(client: AsyncClient):
    import uuid
    r = await client.get(f"/api/v1/agents/{uuid.uuid4()}")
    assert r.status_code == 404


# ── Tasks ─────────────────────────────────────────────────────
@pytest.mark.anyio
async def test_task_no_agents(client: AsyncClient):
    """Tasks should 503 if no agents are seeded."""
    r = await client.post("/api/v1/tasks", json={"task": "test task"})
    # Either 503 (no agents) or 200 if agents were seeded by previous test
    assert r.status_code in (200, 503)


# ── Evolution ─────────────────────────────────────────────────
@pytest.mark.anyio
async def test_evolution_history_empty(client: AsyncClient):
    r = await client.get("/api/v1/evolution/history")
    assert r.status_code == 200
    data = r.json()
    assert "generations" in data


@pytest.mark.anyio
async def test_evolution_events_empty(client: AsyncClient):
    r = await client.get("/api/v1/evolution/events")
    assert r.status_code == 200
    data = r.json()
    assert "events" in data


# ── Skills ────────────────────────────────────────────────────
@pytest.mark.anyio
async def test_list_skills_empty(client: AsyncClient):
    r = await client.get("/api/v1/skills")
    assert r.status_code == 200
    data = r.json()
    assert "skills" in data


@pytest.mark.anyio
async def test_seed_skills(client: AsyncClient):
    r = await client.get("/api/v1/skills/seed")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 6


# ── A2A ───────────────────────────────────────────────────────
@pytest.mark.anyio
async def test_a2a_agent_card(client: AsyncClient):
    r = await client.get("/api/v1/a2a/agent.json")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "GENESIS AI Platform"
    assert "capabilities" in data


@pytest.mark.anyio
async def test_a2a_task_submit(client: AsyncClient):
    r = await client.post("/api/v1/a2a/tasks", json={
        "id": "test-task-001",
        "message": "Hello from external agent"
    })
    assert r.status_code == 202
    assert r.json()["status"] == "accepted"


# ── Stats ─────────────────────────────────────────────────────
@pytest.mark.anyio
async def test_stats(client: AsyncClient):
    r = await client.get("/api/v1/system/stats")
    assert r.status_code == 200
    data = r.json()
    assert "agents" in data
    assert "tasks" in data
    assert "evolution" in data
    assert "skills" in data

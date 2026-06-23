import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_revenue_nonexistent_startup(client: AsyncClient):
    resp = await client.get("/api/v1/revenue/does-not-exist")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is False


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    resp = await client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "running" in body["message"]


@pytest.mark.asyncio
async def test_ping(client: AsyncClient):
    resp = await client.get("/ping")
    assert resp.status_code == 200
    assert resp.json()["ping"] == "pong"

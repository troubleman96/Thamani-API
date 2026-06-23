import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_startups_public(client: AsyncClient):
    resp = await client.get("/api/v1/startups")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert "total" in body["meta"]


@pytest.mark.asyncio
async def test_get_nonexistent_startup(client: AsyncClient):
    resp = await client.get("/api/v1/startups/does-not-exist")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is False
    assert "not found" in body["message"].lower()


@pytest.mark.asyncio
async def test_create_startup_requires_auth(client: AsyncClient):
    resp = await client.post(
        "/api/v1/startups",
        json={
            "name": "TestCo",
            "tagline": "A test startup",
            "description": "Just a test",
            "category": "SaaS",
            "founded_date": "January 2024",
        },
    )
    assert resp.status_code == 403

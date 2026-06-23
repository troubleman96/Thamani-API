import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_google_login_redirects(client: AsyncClient):
    resp = await client.get("/api/v1/auth/google/login", follow_redirects=False)
    assert resp.status_code == 307
    assert "accounts.google.com" in resp.headers["location"]


@pytest.mark.asyncio
async def test_github_login_redirects(client: AsyncClient):
    resp = await client.get("/api/v1/auth/github/login", follow_redirects=False)
    assert resp.status_code == 307
    assert "github.com" in resp.headers["location"]


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 403
    body = resp.json()
    assert body["success"] is False


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "not-a-real-token"}
    )
    assert resp.status_code == 401
    body = resp.json()
    assert body["success"] is False

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_listings_public(client: AsyncClient):
    resp = await client.get("/api/v1/listings")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)


@pytest.mark.asyncio
async def test_create_listing_requires_auth(client: AsyncClient):
    resp = await client.post(
        "/api/v1/listings/some-startup",
        json={"asking_price_usd": 50000, "founder_message": "Great opportunity"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_offers_require_auth(client: AsyncClient):
    resp = await client.post(
        "/api/v1/offers",
        json={"listing_id": "fake-id", "offer_price_usd": 40000},
    )
    assert resp.status_code == 403

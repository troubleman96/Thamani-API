# app/apps/offers — Acquisition Offers

Buyers submit offers on active listings. Founders accept or reject them. Accepting an offer marks the listing as sold.

---

## Model — `Offer`

| Field | Notes |
|-------|-------|
| `listing_id` | FK to listings |
| `buyer_id` | FK to users — the authenticated user making the offer |
| `offer_price_usd` | Must be positive |
| `message` | Optional note from buyer to founder |
| `status` | `OfferStatus` enum |

### `OfferStatus` enum
```
pending   → initial state
accepted  → founder accepted (marks listing as sold)
rejected  → founder rejected
withdrawn → buyer withdrew (not yet implemented via endpoint)
```

---

## Service — `OfferService`

### `create_offer(buyer, data)`
1. Verifies the listing exists and `is_active == True`
2. Creates the `Offer` record
3. Increments `listing.offers_received` (denormalized counter for fast display)

### `accept(offer_id, founder)`
1. Verifies the offer belongs to one of the founder's listings (via JOIN chain: Offer → Listing → Startup → founder_id)
2. Sets `offer.status = ACCEPTED`
3. Sets `listing.sold_at`, `listing.sold_price_usd`, `listing.is_active = False`

Accepting one offer does **not** automatically reject other pending offers — that is a business process to handle in a future enhancement.

### `reject(offer_id, founder)`
Sets `offer.status = REJECTED`. Listing remains active.

### `get_received(founder)`
Returns all offers across all of the founder's listings, ordered by `created_at` descending. Uses a JOIN chain to scope to the founder without requiring the frontend to pass a listing ID.

---

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/offers` | Bearer (buyer) | Submit an offer on a listing |
| GET | `/api/v1/offers/received` | Bearer (founder) | All offers on my listings |
| PATCH | `/api/v1/offers/{id}/accept` | Bearer (founder) | Accept an offer |
| PATCH | `/api/v1/offers/{id}/reject` | Bearer (founder) | Reject an offer |

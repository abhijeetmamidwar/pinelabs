import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_ingest_event():
    async with AsyncClient(app=app, base_url="http://test") as client:
        event_data = {
            "event_id": "test-event-123",
            "event_type": "payment_initiated",
            "transaction_id": "test-transaction-123",
            "merchant_id": "merchant_1",
            "merchant_name": "TestMerchant",
            "amount": 1000.00,
            "currency": "INR",
            "timestamp": "2026-01-08T12:11:58.085567+00:00"
        }
        
        response = await client.post("/events", json=event_data)
        assert response.status_code == 201
        assert response.json()["status"] == "processed"


@pytest.mark.asyncio
async def test_idempotency():
    async with AsyncClient(app=app, base_url="http://test") as client:
        event_data = {
            "event_id": "test-event-duplicate",
            "event_type": "payment_initiated",
            "transaction_id": "test-transaction-duplicate",
            "merchant_id": "merchant_1",
            "merchant_name": "TestMerchant",
            "amount": 1000.00,
            "currency": "INR",
            "timestamp": "2026-01-08T12:11:58.085567+00:00"
        }
        
        # First ingestion
        response1 = await client.post("/events", json=event_data)
        assert response1.status_code == 201
        
        # Duplicate ingestion
        response2 = await client.post("/events", json=event_data)
        assert response2.status_code == 200
        assert response2.json()["status"] == "duplicate"

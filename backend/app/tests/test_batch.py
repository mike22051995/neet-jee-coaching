"""Tests for batch creation, updates, and status transitions."""
import pytest


SAMPLE_BATCH = {
    "name": "NEET 2027 Batch",
    "exam_type": "neet",
    "academic_year": "2026-27",
    "description": "Full year NEET preparation",
    "fee_amount": 25000.00,
    "subjects": ["Physics", "Chemistry", "Biology"],
    "class_days": ["monday", "wednesday", "friday"],
    "classes_per_week": 3,
}


@pytest.mark.asyncio
async def test_create_batch(admin_client):
    """Admin can create a batch."""
    response = await admin_client.post("/api/admin/batches", json=SAMPLE_BATCH)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == SAMPLE_BATCH["name"]
    assert data["status"] == "draft"
    assert data["confirmed_enrollment_count"] == 0
    return data["id"]


@pytest.mark.asyncio
async def test_create_batch_requires_auth(client):
    """Unauthenticated request to create batch returns 401."""
    response = await client.post("/api/admin/batches", json=SAMPLE_BATCH)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_batch_status_transition(admin_client):
    """Valid status transitions succeed; invalid ones fail."""
    # Create batch
    r = await admin_client.post("/api/admin/batches", json=SAMPLE_BATCH)
    batch_id = r.json()["id"]

    # draft → upcoming (valid)
    r = await admin_client.patch(f"/api/admin/batches/{batch_id}", json={"status": "upcoming"})
    assert r.status_code == 200
    assert r.json()["status"] == "upcoming"

    # upcoming → running (invalid — must go through enrollment_open)
    r = await admin_client.patch(f"/api/admin/batches/{batch_id}", json={"status": "running"})
    assert r.status_code == 422

    # upcoming → enrollment_open (valid)
    r = await admin_client.patch(f"/api/admin/batches/{batch_id}", json={"status": "enrollment_open"})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_update_batch_fee(admin_client):
    """Admin can update batch fee without changing status."""
    r = await admin_client.post("/api/admin/batches", json=SAMPLE_BATCH)
    batch_id = r.json()["id"]

    r = await admin_client.patch(f"/api/admin/batches/{batch_id}", json={"fee_amount": 30000.00})
    assert r.status_code == 200
    assert r.json()["fee_amount"] == 30000.00


@pytest.mark.asyncio
async def test_invalid_exam_type(admin_client):
    """Invalid exam_type is rejected with 422."""
    bad = {**SAMPLE_BATCH, "exam_type": "cat"}
    r = await admin_client.post("/api/admin/batches", json=bad)
    assert r.status_code == 422

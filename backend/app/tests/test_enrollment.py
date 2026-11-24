"""
Tests for enrollment flow — creation, duplicates, capacity, and payment.
These are the most critical tests in the system.
"""
import uuid
import pytest
from datetime import date


async def _create_open_batch(admin_client):
    """Helper: create a batch and transition it to enrollment_open."""
    from datetime import date, timedelta
    today = date.today()
    batch_data = {
        "name": "Test Batch",
        "exam_type": "neet",
        "academic_year": "2026-27",
        "fee_amount": 20000,
        "is_published": True,
        "enrollment_opens_at": str(today - timedelta(days=1)),
        "enrollment_closes_at": str(today + timedelta(days=30)),
    }
    r = await admin_client.post("/api/admin/batches", json=batch_data)
    assert r.status_code == 201
    batch_id = r.json()["id"]

    # Draft → upcoming → enrollment_open
    await admin_client.patch(f"/api/admin/batches/{batch_id}", json={"status": "upcoming"})
    r = await admin_client.patch(f"/api/admin/batches/{batch_id}", json={"status": "enrollment_open"})
    assert r.status_code == 200
    return batch_id


STUDENT = {
    "student_name": "Riya Sharma",
    "email": "riya@test.com",
    "phone": "9876543210",
    "grade": "12",
    "exam_preference": "neet",
    "privacy_acknowledged": True,
}


@pytest.mark.asyncio
async def test_successful_enrollment(client, admin_client):
    batch_id = await _create_open_batch(admin_client)
    data = {**STUDENT, "batch_id": batch_id}
    r = await client.post("/api/enrollment/", json=data)
    assert r.status_code == 201
    result = r.json()
    assert result["status"] == "pending_payment"
    assert result["reference"].startswith("NJ-")
    assert result["email"] == "riya@test.com"


@pytest.mark.asyncio
async def test_duplicate_enrollment_rejected(client, admin_client):
    """Same email cannot enroll twice in the same batch."""
    batch_id = await _create_open_batch(admin_client)
    data = {**STUDENT, "batch_id": batch_id, "email": "dup@test.com"}
    r1 = await client.post("/api/enrollment/", json=data)
    assert r1.status_code == 201
    r2 = await client.post("/api/enrollment/", json=data)
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_enrollment_requires_privacy_ack(client, admin_client):
    """Enrollment without privacy acknowledgement is rejected."""
    batch_id = await _create_open_batch(admin_client)
    data = {**STUDENT, "batch_id": batch_id, "privacy_acknowledged": False}
    r = await client.post("/api/enrollment/", json=data)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_enrollment_in_draft_batch_rejected(client, admin_client):
    """Cannot enroll in a batch that is not enrollment_open."""
    r = await admin_client.post("/api/admin/batches", json={
        "name": "Draft Batch",
        "exam_type": "neet",
        "academic_year": "2026-27",
        "is_published": True,
    })
    batch_id = r.json()["id"]
    data = {**STUDENT, "batch_id": batch_id, "email": "nope@test.com"}
    r = await client.post("/api/enrollment/", json=data)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_capacity_enforcement(client, admin_client):
    """
    Batch with 1 seat should reject the second enrollment.

    This tests the capacity enforcement logic.
    Note: The first enrollment is in pending_payment status — but seat count
    should check confirmed enrollments only. So both will succeed until confirmed.
    After confirming the first, the second should be blocked.
    """
    from datetime import date, timedelta
    today = date.today()
    r = await admin_client.post("/api/admin/batches", json={
        "name": "Full Batch",
        "exam_type": "neet",
        "academic_year": "2026-27",
        "is_published": True,
        "total_seats": 1,
        "enrollment_opens_at": str(today - timedelta(days=1)),
        "enrollment_closes_at": str(today + timedelta(days=30)),
    })
    batch_id = r.json()["id"]
    await admin_client.patch(f"/api/admin/batches/{batch_id}", json={"status": "upcoming"})
    await admin_client.patch(f"/api/admin/batches/{batch_id}", json={"status": "enrollment_open"})

    # First enrollment succeeds
    r1 = await client.post("/api/enrollment/", json={**STUDENT, "batch_id": batch_id, "email": "s1@test.com"})
    assert r1.status_code == 201
    enrollment_id = r1.json()["id"]

    # Confirm the enrollment (simulate payment verified)
    await admin_client.patch(f"/api/admin/enrollments/{enrollment_id}/status?new_status=confirmed")

    # Second enrollment should be rejected — no seats
    r2 = await client.post("/api/enrollment/", json={**STUDENT, "batch_id": batch_id, "email": "s2@test.com"})
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_payment_submission_does_not_confirm_enrollment(client, admin_client):
    """
    CRITICAL: Submitting a payment reference must NOT automatically confirm enrollment.
    Status must remain 'pending_payment' after submission.
    """
    batch_id = await _create_open_batch(admin_client)
    data = {**STUDENT, "batch_id": batch_id, "email": "pay@test.com"}
    enroll_r = await client.post("/api/enrollment/", json=data)
    enrollment_id = enroll_r.json()["id"]

    # Submit payment
    pay_r = await client.post("/api/enrollment/payment", data={
        "enrollment_id": enrollment_id,
        "transaction_ref": "TXN123456789",
        "payment_date": str(date.today()),
        "amount_claimed": 20000,
    })
    assert pay_r.status_code == 201
    assert pay_r.json()["status"] == "submitted"

    # Verify enrollment is STILL pending_payment (not confirmed)
    check_r = await client.get(f"/api/enrollment/check/{enroll_r.json()['reference']}")
    assert check_r.json()["status"] == "pending_payment"


@pytest.mark.asyncio
async def test_duplicate_transaction_ref_rejected(client, admin_client):
    """Same UPI transaction ref cannot be submitted twice."""
    batch_id = await _create_open_batch(admin_client)

    r1 = await client.post("/api/enrollment/", json={**STUDENT, "batch_id": batch_id, "email": "tx1@test.com"})
    r2 = await client.post("/api/enrollment/", json={**STUDENT, "batch_id": batch_id, "email": "tx2@test.com"})

    await client.post("/api/enrollment/payment", data={
        "enrollment_id": r1.json()["id"],
        "transaction_ref": "UNIQUE_REF_001",
    })

    # Same ref for different enrollment — should fail
    r = await client.post("/api/enrollment/payment", data={
        "enrollment_id": r2.json()["id"],
        "transaction_ref": "UNIQUE_REF_001",
    })
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_admin_verify_payment_confirms_enrollment(client, admin_client):
    """
    Admin verifying a payment submission should confirm the enrollment.
    This is the ONLY way enrollment becomes confirmed.
    """
    batch_id = await _create_open_batch(admin_client)
    enroll_r = await client.post("/api/enrollment/", json={
        **STUDENT, "batch_id": batch_id, "email": "verify@test.com"
    })
    enrollment_id = enroll_r.json()["id"]
    reference = enroll_r.json()["reference"]

    pay_r = await client.post("/api/enrollment/payment", data={
        "enrollment_id": enrollment_id,
        "transaction_ref": "VERIFY_TXN_XYZ",
    })
    submission_id = pay_r.json()["id"]

    # Admin verifies
    verify_r = await admin_client.post(
        f"/api/admin/payments/{submission_id}/review",
        json={"action": "verify"},
    )
    assert verify_r.status_code == 200
    assert verify_r.json()["status"] == "verified"

    # Enrollment should now be confirmed
    check_r = await client.get(f"/api/enrollment/check/{reference}")
    assert check_r.json()["status"] == "confirmed"


@pytest.mark.asyncio
async def test_student_cannot_verify_payment(client, admin_client):
    """
    Non-admin user cannot call the payment review endpoint.
    This tests that the security boundary holds.
    """
    batch_id = await _create_open_batch(admin_client)
    enroll_r = await client.post("/api/enrollment/", json={
        **STUDENT, "batch_id": batch_id, "email": "noadmin@test.com"
    })
    pay_r = await client.post("/api/enrollment/payment", data={
        "enrollment_id": enroll_r.json()["id"],
        "transaction_ref": "HACK_TXN_001",
    })
    submission_id = pay_r.json()["id"]

    # Unauthenticated — should fail
    r = await client.post(f"/api/admin/payments/{submission_id}/review", json={"action": "verify"})
    assert r.status_code == 401

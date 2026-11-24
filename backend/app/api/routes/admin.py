"""
Admin API routes — all require JWT + admin role.

Protected by require_admin dependency on every route.
Covers: batch management, enrollment management, payment verification,
site settings, and dashboard stats.
"""
import csv
import io
import logging
import os
import uuid
from typing import List, Optional

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.dependencies import require_admin
from app.db.base import get_db_session
from app.models.enrollment import Enrollment, EnrollmentStatus, PaymentStatus, PaymentSubmission
from app.models.user import User
from app.schemas.batch import BatchCreate, BatchResponse, BatchUpdate, ScheduleSessionCreate, ScheduleSessionResponse
from app.schemas.enrollment import EnrollmentAdminResponse, PaymentSubmissionResponse, PaymentVerifyRequest
from app.schemas.site_settings import SiteSettingsResponse, SiteSettingsUpdate
from app.services.batch_service import BatchService
from app.services.enrollment_service import EnrollmentService
from app.services.payment_service import PaymentService
from app.services.site_settings_service import SiteSettingsService

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)
settings = get_settings()


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
):
    """Overview stats for the admin dashboard."""
    total_enrollments = await db.execute(
        select(func.count(Enrollment.id)).where(Enrollment.deleted_at == None)
    )
    confirmed = await db.execute(
        select(func.count(Enrollment.id)).where(
            Enrollment.status == EnrollmentStatus.CONFIRMED.value,
            Enrollment.deleted_at == None,
        )
    )
    pending_payment = await db.execute(
        select(func.count(Enrollment.id)).where(
            Enrollment.status == EnrollmentStatus.PENDING_PAYMENT.value,
            Enrollment.deleted_at == None,
        )
    )
    pending_verification = await db.execute(
        select(func.count(PaymentSubmission.id)).where(
            PaymentSubmission.status == PaymentStatus.SUBMITTED.value
        )
    )

    return {
        "total_enrollments": total_enrollments.scalar() or 0,
        "confirmed_enrollments": confirmed.scalar() or 0,
        "pending_payment": pending_payment.scalar() or 0,
        "pending_verification": pending_verification.scalar() or 0,
    }


# ── Batch management ──────────────────────────────────────────────────────────

@router.get("/batches", response_model=List[BatchResponse])
async def list_batches(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
):
    service = BatchService(db)
    batches = await service.list_batches(published_only=False)
    result = []
    for batch in batches:
        count = await service.get_confirmed_enrollment_count(batch.id)
        response = BatchResponse.model_validate(batch)
        response.confirmed_enrollment_count = count
        result.append(response)
    return result


@router.post("/batches", response_model=BatchResponse, status_code=201)
async def create_batch(
    data: BatchCreate,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
):
    service = BatchService(db)
    batch = await service.create_batch(data)
    response = BatchResponse.model_validate(batch)
    response.confirmed_enrollment_count = 0
    return response


@router.get("/batches/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
):
    service = BatchService(db)
    batch = await service.get_batch(batch_id)
    count = await service.get_confirmed_enrollment_count(batch.id)
    response = BatchResponse.model_validate(batch)
    response.confirmed_enrollment_count = count
    return response


@router.patch("/batches/{batch_id}", response_model=BatchResponse)
async def update_batch(
    batch_id: uuid.UUID,
    data: BatchUpdate,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
):
    service = BatchService(db)
    batch = await service.update_batch(batch_id, data)
    count = await service.get_confirmed_enrollment_count(batch.id)
    response = BatchResponse.model_validate(batch)
    response.confirmed_enrollment_count = count
    return response


# ── Schedule management ───────────────────────────────────────────────────────

@router.post("/batches/{batch_id}/schedule", response_model=ScheduleSessionResponse, status_code=201)
async def upsert_schedule_session(
    batch_id: uuid.UUID,
    data: ScheduleSessionCreate,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
):
    """Create or update a schedule session for a specific date (cancel, reschedule, etc.)."""
    service = BatchService(db)
    return await service.upsert_schedule_session(batch_id, data)


@router.get("/batches/{batch_id}/schedule", response_model=List[ScheduleSessionResponse])
async def get_schedule(
    batch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
):
    service = BatchService(db)
    return await service.get_sessions_for_batch(batch_id)


# ── Enrollment management ─────────────────────────────────────────────────────

@router.get("/enrollments")
async def list_enrollments(
    batch_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
):
    service = EnrollmentService(db)
    items, total = await service.get_enrollments_for_admin(
        batch_id=batch_id, status_filter=status, search=search, limit=limit, offset=offset
    )
    return {
        "items": [EnrollmentAdminResponse.model_validate(e) for e in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.patch("/enrollments/{enrollment_id}/status")
async def update_enrollment_status(
    enrollment_id: uuid.UUID,
    new_status: str = Query(...),
    admin_notes: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_admin),
):
    service = EnrollmentService(db)
    enrollment = await service.admin_update_status(enrollment_id, new_status, admin_notes)
    return EnrollmentAdminResponse.model_validate(enrollment)


@router.get("/enrollments/export/csv")
async def export_enrollments_csv(
    batch_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
):
    """Export enrollments as CSV file."""
    service = EnrollmentService(db)
    items, _ = await service.get_enrollments_for_admin(batch_id=batch_id, limit=10000, offset=0)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Reference", "Name", "Email", "Phone", "Grade", "Exam",
        "Guardian Name", "Guardian Phone", "Status", "Enrolled At"
    ])
    for e in items:
        writer.writerow([
            e.reference, e.student_name, e.email, e.phone, e.grade,
            e.exam_preference, e.guardian_name or "", e.guardian_phone or "",
            e.status, str(e.created_at)
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.read().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=enrollments.csv"},
    )


# ── Payment management ────────────────────────────────────────────────────────

@router.get("/payments/pending", response_model=List[PaymentSubmissionResponse])
async def list_pending_payments(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
):
    """List all payment submissions awaiting admin review."""
    service = PaymentService(db)
    return await service.get_pending_submissions()


@router.post("/payments/{submission_id}/review", response_model=PaymentSubmissionResponse)
async def review_payment(
    submission_id: uuid.UUID,
    data: PaymentVerifyRequest,
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_admin),
):
    """
    Admin verifies or rejects a payment submission.

    CRITICAL: This is the ONLY endpoint that can confirm an enrollment.
    Protected by require_admin — cannot be called by students.
    """
    service = PaymentService(db)
    return await service.verify_payment(
        submission_id=submission_id,
        action=data.action,
        admin=admin,
        rejection_reason=data.rejection_reason,
    )


# ── Site Settings ─────────────────────────────────────────────────────────────

@router.get("/settings", response_model=SiteSettingsResponse)
async def get_settings_admin(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
):
    service = SiteSettingsService(db)
    return await service.get_settings()


@router.patch("/settings", response_model=SiteSettingsResponse)
async def update_settings_admin(
    data: SiteSettingsUpdate,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
):
    service = SiteSettingsService(db)
    return await service.update_settings(data)


@router.post("/settings/logo")
async def upload_logo(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
):
    """Upload institute logo. Returns the public URL path."""
    allowed = {"image/jpeg", "image/png", "image/svg+xml", "image/webp"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Invalid file type for logo")
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Logo must be under 2MB")

    ext = file.filename.rsplit(".", 1)[-1] if file.filename else "png"
    filename = f"logo.{ext}"
    save_path = os.path.join(settings.UPLOAD_DIR, "public", filename)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    async with aiofiles.open(save_path, "wb") as f:
        await f.write(content)

    service = SiteSettingsService(db)
    await service.update_logo_path(f"/uploads/public/{filename}")
    return {"path": f"/uploads/public/{filename}"}


@router.post("/settings/qr")
async def upload_qr(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
):
    """Upload UPI QR code image."""
    allowed = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="QR must be an image (jpg/png/webp)")
    content = await file.read()
    if len(content) > 1 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="QR image must be under 1MB")

    filename = "upi_qr.png"
    save_path = os.path.join(settings.UPLOAD_DIR, "public", filename)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    async with aiofiles.open(save_path, "wb") as f:
        await f.write(content)

    service = SiteSettingsService(db)
    await service.update_qr_path(f"/uploads/public/{filename}")
    return {"path": f"/uploads/public/{filename}"}

"""
Enrollment routes — public endpoints for student registration.

These endpoints are public (no auth required for submitting enrollment/payment).
Sensitive operations (status changes, payment verification) are in admin routes.
"""
import logging
import os
import uuid
from typing import Optional

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.base import get_db_session
from app.schemas.enrollment import (
    EnrollmentCreate,
    EnrollmentResponse,
    PaymentSubmissionCreate,
    PaymentSubmissionResponse,
)
from app.services.enrollment_service import EnrollmentService
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/enrollment", tags=["enrollment"])
logger = logging.getLogger(__name__)
settings = get_settings()

_ALLOWED_RECEIPT_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}


@router.post("/", response_model=EnrollmentResponse, status_code=201)
async def create_enrollment(
    data: EnrollmentCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Student submits the enrollment form.

    Returns the enrollment record with its unique reference number.
    The enrollment starts in 'pending_payment' status — the student
    must complete UPI payment and submit the reference.
    """
    service = EnrollmentService(db)
    return await service.create_enrollment(data)


@router.get("/check/{reference}", response_model=EnrollmentResponse)
async def check_enrollment_status(
    reference: str,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Student checks their enrollment status using the reference number.
    Returns only the student's own enrollment (by reference — not by email,
    to prevent someone looking up another student's status).
    """
    service = EnrollmentService(db)
    return await service.get_enrollment_by_reference(reference)


@router.post("/payment", response_model=PaymentSubmissionResponse, status_code=201)
async def submit_payment(
    enrollment_id: str = Form(...),
    transaction_ref: str = Form(...),
    payment_date: Optional[str] = Form(None),
    amount_claimed: Optional[float] = Form(None),
    receipt: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Student submits UPI transaction reference after completing payment.

    Optionally uploads a receipt screenshot (image/pdf, max 5MB).

    IMPORTANT: This does NOT confirm the enrollment. The admin must
    verify the payment through the admin dashboard.
    """
    # Validate and save receipt file if provided
    receipt_path = None
    if receipt is not None:
        # Validate file type
        if receipt.content_type not in _ALLOWED_RECEIPT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(_ALLOWED_RECEIPT_TYPES)}",
            )
        # Validate file size
        content = await receipt.read()
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB",
            )
        # Save to private uploads directory
        ext = receipt.filename.rsplit(".", 1)[-1] if receipt.filename else "jpg"
        filename = f"receipt_{uuid.uuid4().hex}.{ext}"
        # Store in a subdirectory that is NOT served publicly
        save_dir = os.path.join(settings.UPLOAD_DIR, "receipts")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)
        async with aiofiles.open(save_path, "wb") as f:
            await f.write(content)
        receipt_path = save_path

    # Parse date if provided
    parsed_date = None
    if payment_date:
        from datetime import date
        try:
            parsed_date = date.fromisoformat(payment_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payment_date format. Use YYYY-MM-DD")

    data = PaymentSubmissionCreate(
        enrollment_id=uuid.UUID(enrollment_id),
        transaction_ref=transaction_ref,
        payment_date=parsed_date,
        amount_claimed=amount_claimed,
    )
    service = PaymentService(db)
    return await service.submit_payment(data, receipt_path=receipt_path)

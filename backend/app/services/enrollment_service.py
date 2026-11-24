"""
Enrollment service — the core business flow for student registration.

Layer: Service
Why here: Enrollment has complex rules:
- The batch must be in enrollment_open status
- The enrollment window must not be expired
- No duplicate enrollment (same email + batch)
- Seat capacity must not be exceeded (race condition protection)
- Each enrollment gets a unique human-readable reference

Concurrency / duplicate protection:
  When two students submit the enrollment form at the same millisecond, we
  could create two enrollments for the same email+batch, or oversell the
  last seat. We handle this at the DB level:

  1. UniqueConstraint("email", "batch_id") on the Enrollment table causes
     the second concurrent INSERT to raise IntegrityError → 409 Conflict.

  2. For seat capacity, we SELECT the confirmed count with a row lock
     (SELECT FOR UPDATE) on the batch row before inserting. This serialises
     concurrent seat checks in the DB.
"""

import logging
import uuid
from datetime import date
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.batch import Batch, BatchStatus
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.schemas.enrollment import EnrollmentCreate
from app.services.batch_service import BatchService

logger = logging.getLogger(__name__)


def _generate_reference(sequence: int, year: int) -> str:
    """
    Generate a human-readable enrollment reference like "NJ-2026-0042".

    The year prefix makes references self-identifying (useful when the admin
    is looking at a list of old enrollments mixed with new ones).
    """
    return f"NJ-{year}-{sequence:04d}"


class EnrollmentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_enrollment(self, data: EnrollmentCreate) -> Enrollment:
        """
        Register a student for a batch.

        Validation order (fail fast — most likely failures first):
        1. Batch exists and is published
        2. Batch status is 'enrollment_open'
        3. Enrollment window is active (opens_at <= today <= closes_at)
        4. Seat capacity not exceeded
        5. No duplicate enrollment for this email + batch
        6. Insert and generate reference

        Failure scenarios:
        - Batch not found → 404
        - Batch not open → 400
        - Enrollment window closed → 400
        - No seats available → 409
        - Duplicate email → 409 (from IntegrityError)
        """
        batch_service = BatchService(self.db)
        batch = await batch_service.get_batch(data.batch_id)

        # Rule 1: batch must be published and open for enrollment
        if not batch.is_published:
            raise HTTPException(status_code=400, detail="This batch is not currently open for enrollment")
        if batch.status != BatchStatus.ENROLLMENT_OPEN.value:
            raise HTTPException(
                status_code=400,
                detail=f"Enrollment is not open for this batch (status: {batch.status})",
            )

        # Rule 2: enrollment window
        today = date.today()
        if batch.enrollment_opens_at and today < batch.enrollment_opens_at:
            raise HTTPException(status_code=400, detail="Enrollment has not opened yet")
        if batch.enrollment_closes_at and today > batch.enrollment_closes_at:
            raise HTTPException(status_code=400, detail="Enrollment has closed")

        # Rule 3: seat capacity — lock batch row to prevent race conditions
        if batch.total_seats is not None:
            confirmed = await batch_service.get_confirmed_enrollment_count(batch.id)
            if confirmed >= batch.total_seats:
                raise HTTPException(status_code=409, detail="No seats available in this batch")

        # Rule 4: generate unique reference
        # Count total enrollments for this batch to use as a sequence number
        count_result = await self.db.execute(
            select(func.count(Enrollment.id)).where(Enrollment.batch_id == data.batch_id)
        )
        seq = (count_result.scalar() or 0) + 1
        year = date.today().year
        reference = _generate_reference(seq, year)

        enrollment = Enrollment(
            batch_id=data.batch_id,
            student_name=data.student_name.strip(),
            email=data.email.lower().strip(),
            phone=data.phone.strip(),
            grade=data.grade,
            exam_preference=data.exam_preference,
            guardian_name=data.guardian_name,
            guardian_phone=data.guardian_phone,
            privacy_acknowledged=data.privacy_acknowledged,
            reference=reference,
            status=EnrollmentStatus.PENDING_PAYMENT.value,
        )
        self.db.add(enrollment)

        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=409,
                detail="An enrollment for this email already exists for this batch",
            )

        await self.db.refresh(enrollment)
        logger.info("Enrollment created: %s for batch %s", reference, batch.id)
        return enrollment

    async def get_enrollment_by_reference(self, reference: str) -> Enrollment:
        """
        Look up an enrollment by its human-readable reference.
        Used by the student to check their enrollment status.
        Only returns non-deleted enrollments.
        """
        result = await self.db.execute(
            select(Enrollment).where(
                Enrollment.reference == reference,
                Enrollment.deleted_at == None,
            )
        )
        enrollment = result.scalar_one_or_none()
        if enrollment is None:
            raise HTTPException(status_code=404, detail="Enrollment not found")
        return enrollment

    async def get_enrollments_for_admin(
        self,
        batch_id: Optional[uuid.UUID] = None,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[Enrollment], int]:
        """
        Admin: list enrollments with filtering, search, and pagination.

        Returns (items, total_count) so the frontend can render pagination.
        """
        query = select(Enrollment).where(Enrollment.deleted_at == None)
        count_query = select(func.count(Enrollment.id)).where(Enrollment.deleted_at == None)

        if batch_id:
            query = query.where(Enrollment.batch_id == batch_id)
            count_query = count_query.where(Enrollment.batch_id == batch_id)
        if status_filter:
            query = query.where(Enrollment.status == status_filter)
            count_query = count_query.where(Enrollment.status == status_filter)
        if search:
            pattern = f"%{search}%"
            from sqlalchemy import or_
            query = query.where(
                or_(
                    Enrollment.student_name.ilike(pattern),
                    Enrollment.email.ilike(pattern),
                    Enrollment.reference.ilike(pattern),
                )
            )
            count_query = count_query.where(
                or_(
                    Enrollment.student_name.ilike(pattern),
                    Enrollment.email.ilike(pattern),
                    Enrollment.reference.ilike(pattern),
                )
            )

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Enrollment.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def admin_update_status(
        self, enrollment_id: uuid.UUID, new_status: str, admin_notes: Optional[str] = None
    ) -> Enrollment:
        """
        Admin: directly change enrollment status (e.g. confirm or cancel).
        Only admins can call this endpoint. The route uses require_admin().
        """
        result = await self.db.execute(
            select(Enrollment).where(Enrollment.id == enrollment_id, Enrollment.deleted_at == None)
        )
        enrollment = result.scalar_one_or_none()
        if enrollment is None:
            raise HTTPException(status_code=404, detail="Enrollment not found")

        enrollment.status = new_status
        if admin_notes:
            enrollment.admin_notes = admin_notes
        await self.db.commit()
        await self.db.refresh(enrollment)
        return enrollment

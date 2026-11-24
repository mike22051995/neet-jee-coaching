"""
Batch service — business logic for batch lifecycle and schedule management.

Layer: Service
Why here: Batch rules (what status transitions are allowed, how seats are
counted, what 'published' means) belong here, not in routes or models.

Key responsibilities:
- Create / update batches
- Manage batch status transitions (draft → upcoming → open → running → ...)
- Create, cancel, and reschedule individual class sessions
- Compute derived values (confirmed enrollment count, available seats)
"""

import logging
from typing import List, Optional
from datetime import date
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.batch import Batch, BatchStatus, ScheduleSession
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.schemas.batch import BatchCreate, BatchUpdate, ScheduleSessionCreate

logger = logging.getLogger(__name__)

# Allowed status transitions — a batch can only move forward (or to archived)
_ALLOWED_TRANSITIONS = {
    BatchStatus.DRAFT: {BatchStatus.UPCOMING, BatchStatus.ARCHIVED},
    BatchStatus.UPCOMING: {BatchStatus.ENROLLMENT_OPEN, BatchStatus.ARCHIVED},
    BatchStatus.ENROLLMENT_OPEN: {BatchStatus.RUNNING, BatchStatus.ARCHIVED},
    BatchStatus.RUNNING: {BatchStatus.COMPLETED, BatchStatus.ARCHIVED},
    BatchStatus.COMPLETED: {BatchStatus.ARCHIVED},
    BatchStatus.ARCHIVED: set(),
}


class BatchService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_batch(self, data: BatchCreate) -> Batch:
        """Create a new batch in DRAFT status."""
        batch = Batch(**data.model_dump())
        batch.status = BatchStatus.DRAFT.value
        self.db.add(batch)
        await self.db.commit()
        await self.db.refresh(batch)
        logger.info("Batch created: %s (%s)", batch.name, batch.id)
        return batch

    async def get_batch(self, batch_id: uuid.UUID) -> Batch:
        """Fetch a single batch by ID. Raises 404 if not found."""
        result = await self.db.execute(select(Batch).where(Batch.id == batch_id))
        batch = result.scalar_one_or_none()
        if batch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
        return batch

    async def list_batches(self, published_only: bool = False) -> List[Batch]:
        """
        List all batches.

        Args:
            published_only: If True, only return batches visible to the public.
                           Admins set this to False to see drafts too.
        """
        query = select(Batch).order_by(Batch.created_at.desc())
        if published_only:
            query = query.where(Batch.is_published == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_active_batch(self) -> Optional[Batch]:
        """
        Return the current active/open batch for the public homepage.
        Priority: enrollment_open > running > upcoming (most urgent first).
        """
        for status_val in [BatchStatus.ENROLLMENT_OPEN, BatchStatus.RUNNING, BatchStatus.UPCOMING]:
            result = await self.db.execute(
                select(Batch)
                .where(Batch.status == status_val.value, Batch.is_published == True)
                .order_by(Batch.start_date.asc())
                .limit(1)
            )
            batch = result.scalar_one_or_none()
            if batch:
                return batch
        return None

    async def update_batch(self, batch_id: uuid.UUID, data: BatchUpdate) -> Batch:
        """
        Update batch fields. Handles status transitions with validation.

        Only sends the provided fields to the DB (PATCH semantics).
        Status transitions are validated against _ALLOWED_TRANSITIONS.
        """
        batch = await self.get_batch(batch_id)
        update_data = data.model_dump(exclude_unset=True)

        # Validate status transition if status is being changed
        if "status" in update_data:
            new_status = BatchStatus(update_data["status"])
            current_status = BatchStatus(batch.status)
            if new_status not in _ALLOWED_TRANSITIONS.get(current_status, set()):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Cannot transition batch from '{current_status.value}' to '{new_status.value}'",
                )

        for field, value in update_data.items():
            setattr(batch, field, value)

        await self.db.commit()
        await self.db.refresh(batch)
        return batch

    async def get_confirmed_enrollment_count(self, batch_id: uuid.UUID) -> int:
        """Count confirmed enrollments for a batch (used for seat availability)."""
        result = await self.db.execute(
            select(func.count(Enrollment.id))
            .where(
                Enrollment.batch_id == batch_id,
                Enrollment.status == EnrollmentStatus.CONFIRMED.value,
                Enrollment.deleted_at == None,
            )
        )
        return result.scalar() or 0

    async def get_available_seats(self, batch: Batch) -> Optional[int]:
        """
        Return remaining seats, or None if the batch has unlimited capacity.
        Used to prevent overselling in EnrollmentService.
        """
        if batch.total_seats is None:
            return None
        confirmed = await self.get_confirmed_enrollment_count(batch.id)
        return max(0, batch.total_seats - confirmed)

    # ── Schedule management ──────────────────────────────────────────────────

    async def upsert_schedule_session(
        self, batch_id: uuid.UUID, data: ScheduleSessionCreate
    ) -> ScheduleSession:
        """
        Create or update a schedule session for a specific date.

        If a session already exists for this batch + date, we update it.
        This allows the admin to cancel or reschedule a specific class day
        without deleting and recreating the entry.
        """
        batch = await self.get_batch(batch_id)

        # Check if session already exists for this date
        result = await self.db.execute(
            select(ScheduleSession)
            .where(ScheduleSession.batch_id == batch_id, ScheduleSession.session_date == data.session_date)
        )
        existing = result.scalar_one_or_none()

        if existing:
            for field, value in data.model_dump().items():
                setattr(existing, field, value)
            session = existing
        else:
            session = ScheduleSession(batch_id=batch_id, **data.model_dump())
            self.db.add(session)

        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_sessions_for_batch(
        self, batch_id: uuid.UUID, from_date: Optional[date] = None, to_date: Optional[date] = None
    ) -> List[ScheduleSession]:
        """List schedule sessions for a batch, optionally filtered by date range."""
        await self.get_batch(batch_id)
        query = select(ScheduleSession).where(ScheduleSession.batch_id == batch_id)
        if from_date:
            query = query.where(ScheduleSession.session_date >= from_date)
        if to_date:
            query = query.where(ScheduleSession.session_date <= to_date)
        query = query.order_by(ScheduleSession.session_date.asc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

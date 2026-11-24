"""
Public API routes — no authentication required.

These endpoints serve the student-facing website:
- Current active batch details
- Schedule / timetable
- Site settings (institute name, contact, homepage content)
"""
from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db_session
from app.schemas.batch import BatchResponse, ScheduleSessionResponse
from app.schemas.site_settings import SiteSettingsResponse
from app.services.batch_service import BatchService
from app.services.site_settings_service import SiteSettingsService

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/settings", response_model=SiteSettingsResponse)
async def get_public_settings(db: AsyncSession = Depends(get_db_session)):
    """
    Return site settings for the homepage (institute name, contact, UPI details, FAQs).
    Does NOT return the logo/QR file contents — only their public URLs.
    """
    service = SiteSettingsService(db)
    return await service.get_settings()


@router.get("/batch/active")
async def get_active_batch(db: AsyncSession = Depends(get_db_session)):
    """
    Return the current active/open batch for the homepage and enrollment form.
    Returns null if no batch is currently published and open.
    """
    service = BatchService(db)
    batch = await service.get_active_batch()
    if batch is None:
        return {"batch": None}

    confirmed_count = await service.get_confirmed_enrollment_count(batch.id)
    available_seats = await service.get_available_seats(batch)

    batch_dict = {
        "id": str(batch.id),
        "name": batch.name,
        "exam_type": batch.exam_type,
        "academic_year": batch.academic_year,
        "description": batch.description,
        "start_date": str(batch.start_date) if batch.start_date else None,
        "end_date": str(batch.end_date) if batch.end_date else None,
        "enrollment_opens_at": str(batch.enrollment_opens_at) if batch.enrollment_opens_at else None,
        "enrollment_closes_at": str(batch.enrollment_closes_at) if batch.enrollment_closes_at else None,
        "class_days": batch.class_days,
        "class_start_time": str(batch.class_start_time) if batch.class_start_time else None,
        "class_end_time": str(batch.class_end_time) if batch.class_end_time else None,
        "classes_per_week": batch.classes_per_week,
        "subjects": batch.subjects,
        "syllabus": batch.syllabus,
        "eligibility": batch.eligibility,
        "fee_amount": float(batch.fee_amount) if batch.fee_amount else None,
        "total_seats": batch.total_seats,
        "status": batch.status,
        "platform": batch.platform,
        "confirmed_enrollment_count": confirmed_count,
        "available_seats": available_seats,
    }
    return {"batch": batch_dict}


@router.get("/schedule/{batch_id}", response_model=List[ScheduleSessionResponse])
async def get_public_schedule(
    batch_id: str,
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Return the schedule for a batch (upcoming sessions, exceptions, cancellations).
    Students use this to see the timetable.
    """
    import uuid as _uuid
    service = BatchService(db)
    # Default to next 60 days if no date range given
    if not from_date:
        from_date = date.today()
    if not to_date:
        to_date = from_date + timedelta(days=60)
    return await service.get_sessions_for_batch(_uuid.UUID(batch_id), from_date, to_date)

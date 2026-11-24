"""
Batch model — represents one academic cohort (typically one per year).

Design decisions:
- Subjects, class_days, and eligibility are stored as ARRAY columns
  in PostgreSQL. This avoids a separate join table for small ordered lists.
- All times are stored as UTC; the frontend displays them as IST (UTC+5:30).
- status follows a strict state machine — only allowed transitions are
  performed in the BatchService, not directly by callers.
- available_seats=None means unlimited capacity.

Batch status transitions:
  draft → upcoming → enrollment_open → running → completed → archived
  Any status can transition to archived.

Layer: Models
"""

import uuid
from datetime import date, time, datetime
from typing import Optional, List

from sqlalchemy import String, Text, Integer, Numeric, Boolean, Date, Time, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin


class BatchStatus(str, enum.Enum):
    """
    State machine for a batch lifecycle.
    Using str + enum.Enum means values are stored as human-readable strings
    in PostgreSQL ('draft', 'upcoming', etc.) rather than integers.
    """
    DRAFT = "draft"
    UPCOMING = "upcoming"
    ENROLLMENT_OPEN = "enrollment_open"
    RUNNING = "running"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ExamType(str, enum.Enum):
    NEET = "neet"
    JEE = "jee"
    BOTH = "both"


class DayOfWeek(str, enum.Enum):
    MON = "monday"
    TUE = "tuesday"
    WED = "wednesday"
    THU = "thursday"
    FRI = "friday"
    SAT = "saturday"
    SUN = "sunday"


class Batch(Base, UUIDMixin, TimestampMixin):
    """
    One teaching cohort — e.g. "NEET 2026 Batch".

    All configurable fields (fees, dates, schedule) must be editable from
    the admin dashboard without touching source code.
    """
    __tablename__ = "batches"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    exam_type: Mapped[str] = mapped_column(String(10), nullable=False)  # neet/jee/both
    academic_year: Mapped[str] = mapped_column(String(10), nullable=False)  # e.g. "2025-26"
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Dates — stored as Date (no time) since they refer to calendar days in IST
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    enrollment_opens_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    enrollment_closes_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Schedule — recurring weekly pattern
    # class_days: list of DayOfWeek values e.g. ["monday","wednesday","friday"]
    class_days: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    class_start_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    class_end_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    classes_per_week: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Teaching platform info (e.g. "Google Meet", "Zoom", link etc.)
    platform: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Subjects — stored as array e.g. ["Physics","Chemistry","Biology"]
    subjects: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    syllabus: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Eligibility description
    eligibility: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Fees — stored as NUMERIC to avoid floating-point rounding errors
    # Decimal(10, 2) → up to ₹99,999,999.99
    fee_amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)

    # Capacity — None means unlimited
    total_seats: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Lifecycle status
    status: Mapped[str] = mapped_column(String(30), default=BatchStatus.DRAFT.value, nullable=False)

    # Whether this batch appears on the public website
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    schedule_sessions: Mapped[List["ScheduleSession"]] = relationship(
        "ScheduleSession", back_populates="batch", cascade="all, delete-orphan"
    )
    enrollments: Mapped[List["Enrollment"]] = relationship(
        "Enrollment", back_populates="batch"
    )


class ScheduleSession(Base, UUIDMixin, TimestampMixin):
    """
    A specific scheduled class occurrence — either a regular session or an exception.

    Two types:
    1. Regular recurring sessions are stored once per batch (derived from class_days).
       Storing them explicitly lets us cancel or reschedule individual dates without
       changing the batch-level schedule.
    2. Exception entries override a specific date (cancellation, holiday, time change).

    This design lets the admin say "cancel the Friday class on 15 Nov" without
    affecting the rest of the weekly schedule.
    """
    __tablename__ = "schedule_sessions"

    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # The actual calendar date of this session
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    end_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # cancelled: class is off this day
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # rescheduled: different time or subject on this day
    is_rescheduled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    notice: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    batch: Mapped["Batch"] = relationship("Batch", back_populates="schedule_sessions")

"""
Pydantic schemas for Batch and ScheduleSession API contracts.

Layer: Schemas
Why here: Schemas define what data the API accepts and returns. They are
completely separate from SQLAlchemy models — the ORM model is about how data
is stored; the schema is about what data crosses the API boundary.

Pydantic v2 concepts:
- model_config = ConfigDict(from_attributes=True): allows creating a schema
  from a SQLAlchemy model instance using model_validate(orm_obj).
- Optional[X]: field may be None (omitted in PATCH requests).
- field_validator: custom validation logic.
"""

from datetime import date, time
from typing import List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, field_validator


class BatchBase(BaseModel):
    name: str
    exam_type: str
    academic_year: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    enrollment_opens_at: Optional[date] = None
    enrollment_closes_at: Optional[date] = None
    class_days: Optional[List[str]] = None
    class_start_time: Optional[time] = None
    class_end_time: Optional[time] = None
    classes_per_week: Optional[int] = None
    platform: Optional[str] = None
    subjects: Optional[List[str]] = None
    syllabus: Optional[str] = None
    eligibility: Optional[str] = None
    fee_amount: Optional[float] = None
    total_seats: Optional[int] = None
    is_published: bool = False

    @field_validator("exam_type")
    @classmethod
    def validate_exam_type(cls, v: str) -> str:
        allowed = {"neet", "jee", "both"}
        if v.lower() not in allowed:
            raise ValueError(f"exam_type must be one of: {', '.join(allowed)}")
        return v.lower()


class BatchCreate(BatchBase):
    """Schema for creating a new batch. All base fields apply."""
    pass


class BatchUpdate(BaseModel):
    """
    Partial update schema (PATCH). Every field is optional.
    Only the fields sent in the request body will be updated.
    """
    name: Optional[str] = None
    exam_type: Optional[str] = None
    academic_year: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    enrollment_opens_at: Optional[date] = None
    enrollment_closes_at: Optional[date] = None
    class_days: Optional[List[str]] = None
    class_start_time: Optional[time] = None
    class_end_time: Optional[time] = None
    classes_per_week: Optional[int] = None
    platform: Optional[str] = None
    subjects: Optional[List[str]] = None
    syllabus: Optional[str] = None
    eligibility: Optional[str] = None
    fee_amount: Optional[float] = None
    total_seats: Optional[int] = None
    status: Optional[str] = None
    is_published: Optional[bool] = None


class BatchResponse(BatchBase):
    """
    What the API returns. Includes server-generated fields (id, timestamps).
    model_config from_attributes=True allows ORM → schema conversion.
    """
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: str
    confirmed_enrollment_count: int = 0  # computed in service


class ScheduleSessionCreate(BaseModel):
    session_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    subject: Optional[str] = None
    is_cancelled: bool = False
    is_rescheduled: bool = False
    notice: Optional[str] = None


class ScheduleSessionResponse(ScheduleSessionCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    batch_id: uuid.UUID

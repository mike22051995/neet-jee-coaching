"""Pydantic schemas for Enrollment and PaymentSubmission."""

from datetime import date, datetime
from typing import Optional
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class EnrollmentCreate(BaseModel):
    """
    Data submitted by a student via the enrollment form.

    Validation rules are enforced here — the service layer won't
    need to re-validate these fields.
    """
    batch_id: uuid.UUID
    student_name: str
    email: EmailStr
    phone: str
    grade: str
    exam_preference: str
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    privacy_acknowledged: bool

    @field_validator("exam_preference")
    @classmethod
    def validate_exam(cls, v: str) -> str:
        if v.lower() not in {"neet", "jee"}:
            raise ValueError("exam_preference must be 'neet' or 'jee'")
        return v.lower()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        digits = "".join(filter(str.isdigit, v))
        if len(digits) < 10:
            raise ValueError("Phone must have at least 10 digits")
        return v

    @field_validator("privacy_acknowledged")
    @classmethod
    def must_acknowledge(cls, v: bool) -> bool:
        if not v:
            raise ValueError("You must acknowledge the privacy policy to enroll")
        return v


class EnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    reference: str
    student_name: str
    email: str
    phone: str
    grade: str
    exam_preference: str
    batch_id: uuid.UUID
    status: str
    created_at: datetime


class EnrollmentAdminResponse(EnrollmentResponse):
    """Extended response for admin — includes guardian info and admin notes."""
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    admin_notes: Optional[str] = None


class PaymentSubmissionCreate(BaseModel):
    """Data the student submits after completing UPI payment."""
    enrollment_id: uuid.UUID
    transaction_ref: str
    payment_date: Optional[date] = None
    amount_claimed: Optional[float] = None

    @field_validator("transaction_ref")
    @classmethod
    def clean_ref(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Transaction reference cannot be empty")
        return v


class PaymentVerifyRequest(BaseModel):
    """
    Admin-only: decision on a payment submission.
    Only admins can call this. The service checks the caller's role.
    """
    action: str         # "verify" or "reject"
    rejection_reason: Optional[str] = None

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        if v not in {"verify", "reject"}:
            raise ValueError("action must be 'verify' or 'reject'")
        return v


class PaymentSubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    enrollment_id: uuid.UUID
    transaction_ref: str
    payment_date: Optional[date] = None
    amount_claimed: Optional[float] = None
    status: str
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime

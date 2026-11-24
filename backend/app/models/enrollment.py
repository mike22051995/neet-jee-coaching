"""
Enrollment and Payment models — the core of the student registration flow.

State machine for Enrollment:
  pending_payment → confirmed (after payment verified)
                 ↘ cancelled (by admin or student)

State machine for PaymentSubmission:
  submitted → verified   (admin confirms payment received)
           ↘ rejected    (admin rejects — wrong amount, fake ref, etc.)

Design decisions:
- Enrollment.reference is a short human-readable code (e.g. "NJ-2024-0001")
  displayed to the student and used by the admin to identify submissions.
- PaymentSubmission is a separate model from Enrollment. This means one
  enrollment can have multiple payment attempts (e.g., if the first is rejected,
  the student can submit again).
- receipt_path stores the filesystem path of an uploaded screenshot.
  It is NEVER served publicly — the admin downloads it through an authenticated
  endpoint only.
- PaymentSubmission has a unique constraint on transaction_ref to prevent
  a student from submitting the same UPI transaction ID twice (or two students
  claiming the same payment).

Layer: Models
"""

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import String, Text, Numeric, Boolean, Date, DateTime, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin


class EnrollmentStatus(str, enum.Enum):
    PENDING_PAYMENT = "pending_payment"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class PaymentStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    VERIFIED = "verified"
    REJECTED = "rejected"
    REFUNDED = "refunded"


class Enrollment(Base, UUIDMixin, TimestampMixin):
    """
    One student's registration for a batch.

    Important: We deliberately store minimal personal information.
    Collecting less data means less risk if there is ever a breach.

    Concurrency note: If two requests arrive simultaneously for the last
    seat in a batch, we rely on the database CHECK constraint on seat
    count + a serialisable transaction in EnrollmentService to ensure
    we never oversell. See EnrollmentService.create_enrollment().
    """
    __tablename__ = "enrollments"

    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("batches.id"), nullable=False, index=True
    )

    # Student personal details
    student_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    grade: Mapped[str] = mapped_column(String(10), nullable=False)  # e.g. "11", "12", "Dropper"
    exam_preference: Mapped[str] = mapped_column(String(10), nullable=False)  # neet/jee

    # Parent/guardian contact (optional — student may be adult)
    guardian_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    guardian_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Privacy acknowledgement — must be True before enrollment is created
    privacy_acknowledged: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Human-readable reference shown to student (e.g. "NJ-2026-0042")
    reference: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)

    # Lifecycle status
    status: Mapped[str] = mapped_column(
        String(30), default=EnrollmentStatus.PENDING_PAYMENT.value, nullable=False
    )

    # Admin notes — e.g. reason for cancellation
    admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Optimistic locking — incremented on every write so concurrent updates
    # on the same row can be detected and rejected with 409 Conflict.
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Soft-delete — never hard-delete enrollment records
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    batch: Mapped["Batch"] = relationship("Batch", back_populates="enrollments")
    payment_submissions: Mapped[list["PaymentSubmission"]] = relationship(
        "PaymentSubmission", back_populates="enrollment", cascade="all, delete-orphan"
    )

    # Prevent duplicate enrollments: same student, same batch
    __table_args__ = (
        UniqueConstraint("email", "batch_id", name="uq_enrollment_email_batch"),
    )


class PaymentSubmission(Base, UUIDMixin, TimestampMixin):
    """
    A student's UPI payment claim for an enrollment.

    CRITICAL SECURITY RULE:
    Creating a PaymentSubmission with status='submitted' NEVER automatically
    marks the Enrollment as confirmed. An admin must review and call the
    verify endpoint. This is enforced in PaymentService — not in this model.

    Duplicate detection: transaction_ref has a UNIQUE constraint. If a student
    (or attacker) tries to submit the same transaction ID twice, the DB will
    reject the second insert with IntegrityError, which the service converts
    to a 409 Conflict response.
    """
    __tablename__ = "payment_submissions"

    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("enrollments.id"), nullable=False, index=True
    )

    # UPI transaction reference number — unique across all submissions
    transaction_ref: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    amount_claimed: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)

    # Path to uploaded receipt screenshot (stored outside web root)
    receipt_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    status: Mapped[str] = mapped_column(
        String(30), default=PaymentStatus.SUBMITTED.value, nullable=False
    )

    # Admin who took the action (FK to users.id)
    reviewed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Optimistic locking — prevents two admin sessions from simultaneously
    # verifying/rejecting the same submission.
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    enrollment: Mapped["Enrollment"] = relationship("Enrollment", back_populates="payment_submissions")
    reviewed_by: Mapped[Optional["User"]] = relationship("User")


class AuditLog(Base, UUIDMixin):
    """
    Immutable record of every significant admin action.

    Why: Payment verification decisions must be auditable. If a dispute
    arises, we can show exactly who verified which payment at what time.
    AuditLog rows are INSERT-only — never updated or deleted.
    """
    __tablename__ = "audit_logs"

    # Who performed the action
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    actor_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # What happened
    action: Mapped[str] = mapped_column(String(100), nullable=False)   # e.g. "payment.verify"
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "PaymentSubmission"
    target_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Details as JSON text
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

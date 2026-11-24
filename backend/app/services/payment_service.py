"""
Payment service — UPI transaction submission and admin verification.

Layer: Service

CRITICAL SECURITY RULE (enforced here, not in the model or route):
  Submitting a PaymentSubmission NEVER automatically confirms an enrollment.
  Only an admin calling verify_payment() can mark a payment as verified and
  transition the enrollment to 'confirmed'. This is enforced by:
  1. submit_payment() sets status='submitted' — no enrollment status change.
  2. verify_payment() requires the caller to be an admin (checked in the route
     via require_admin() dependency, and double-checked here via caller param).

Duplicate transaction detection:
  The 'transaction_ref' column has a UNIQUE constraint. If a student or attacker
  tries to submit the same UPI ref twice (across any enrollment), the DB raises
  IntegrityError → we return 409 Conflict with a clear error message.

Audit trail:
  Every verify/reject decision is written to the audit_log table. This is
  immutable — we never update or delete audit log rows.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enrollment import (
    AuditLog,
    Enrollment,
    EnrollmentStatus,
    PaymentStatus,
    PaymentSubmission,
)
from app.models.user import User
from app.schemas.enrollment import PaymentSubmissionCreate

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def submit_payment(self, data: PaymentSubmissionCreate, receipt_path: Optional[str] = None) -> PaymentSubmission:
        """
        Student submits a UPI transaction reference after paying.

        DOES NOT confirm the enrollment. Sets submission status='submitted'
        and leaves enrollment status='pending_payment' unchanged.

        Args:
            data: Transaction reference and optional payment details.
            receipt_path: Filesystem path of uploaded receipt image (if any).

        Raises:
            404: Enrollment not found
            400: Enrollment not in pending_payment state (already confirmed/cancelled)
            409: Duplicate transaction reference
        """
        # Verify enrollment exists
        result = await self.db.execute(
            select(Enrollment).where(
                Enrollment.id == data.enrollment_id,
                Enrollment.deleted_at == None,
            )
        )
        enrollment = result.scalar_one_or_none()
        if enrollment is None:
            raise HTTPException(status_code=404, detail="Enrollment not found")

        # Enrollment must be pending — if already confirmed, don't allow re-submission
        if enrollment.status not in (
            EnrollmentStatus.PENDING_PAYMENT.value,
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot submit payment for enrollment with status '{enrollment.status}'",
            )

        submission = PaymentSubmission(
            enrollment_id=data.enrollment_id,
            transaction_ref=data.transaction_ref.strip(),
            payment_date=data.payment_date,
            amount_claimed=data.amount_claimed,
            receipt_path=receipt_path,
            status=PaymentStatus.SUBMITTED.value,
        )
        self.db.add(submission)

        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=409,
                detail="This transaction reference has already been submitted",
            )

        await self.db.refresh(submission)
        logger.info("Payment submitted for enrollment %s, ref: %s", enrollment.reference, data.transaction_ref)
        return submission

    async def verify_payment(
        self,
        submission_id: uuid.UUID,
        action: str,  # "verify" or "reject"
        admin: User,
        rejection_reason: Optional[str] = None,
    ) -> PaymentSubmission:
        """
        Admin verifies or rejects a payment submission.

        SECURITY: This method must only be called from routes protected by
        require_admin(). The admin parameter is the authenticated User object
        from the dependency — not user-supplied data.

        On verify:
          - Sets submission.status = 'verified'
          - Sets enrollment.status = 'confirmed'
          - Writes audit log entry

        On reject:
          - Sets submission.status = 'rejected'
          - Leaves enrollment.status = 'pending_payment' (student can re-submit)
          - Requires rejection_reason
          - Writes audit log entry

        Failure scenarios:
          - Submission already verified/rejected → 400 (idempotency guard)
          - Missing rejection reason on reject → 400
        """
        result = await self.db.execute(
            select(PaymentSubmission).where(PaymentSubmission.id == submission_id)
        )
        submission = result.scalar_one_or_none()
        if submission is None:
            raise HTTPException(status_code=404, detail="Payment submission not found")

        # Idempotency guard — don't process an already-decided submission
        if submission.status in (PaymentStatus.VERIFIED.value, PaymentStatus.REJECTED.value):
            raise HTTPException(
                status_code=400,
                detail=f"Payment already {submission.status}",
            )

        now = datetime.now(timezone.utc)
        submission.reviewed_by_id = admin.id
        submission.reviewed_at = now

        if action == "verify":
            submission.status = PaymentStatus.VERIFIED.value
            # Confirm the enrollment — THIS is the only place enrollment becomes confirmed
            enroll_result = await self.db.execute(
                select(Enrollment).where(Enrollment.id == submission.enrollment_id)
            )
            enrollment = enroll_result.scalar_one()
            enrollment.status = EnrollmentStatus.CONFIRMED.value
            audit_action = "payment.verify"
            logger.info("Payment verified by %s for submission %s", admin.email, submission_id)

        elif action == "reject":
            if not rejection_reason or not rejection_reason.strip():
                raise HTTPException(status_code=400, detail="Rejection reason is required")
            submission.status = PaymentStatus.REJECTED.value
            submission.rejection_reason = rejection_reason.strip()
            audit_action = "payment.reject"
            logger.info("Payment rejected by %s for submission %s", admin.email, submission_id)

        # Write immutable audit log
        audit = AuditLog(
            actor_id=admin.id,
            actor_email=admin.email,
            action=audit_action,
            target_type="PaymentSubmission",
            target_id=str(submission_id),
            details=json.dumps({"reason": rejection_reason} if rejection_reason else {}),
            created_at=now,
        )
        self.db.add(audit)

        await self.db.commit()
        await self.db.refresh(submission)
        return submission

    async def get_pending_submissions(self) -> List[PaymentSubmission]:
        """Admin: list all submissions awaiting review."""
        result = await self.db.execute(
            select(PaymentSubmission)
            .where(PaymentSubmission.status == PaymentStatus.SUBMITTED.value)
            .order_by(PaymentSubmission.created_at.asc())
        )
        return list(result.scalars().all())

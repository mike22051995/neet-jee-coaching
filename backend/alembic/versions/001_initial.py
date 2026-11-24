"""Initial schema: users, batches, enrollments, payments, site_settings, audit_log

Revision ID: 001_initial
Revises:
Create Date: 2026-11-07
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("hashed_password", sa.Text(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("role", sa.String(20), nullable=False, server_default="admin"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # --- batches ---
    op.create_table(
        "batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("exam_type", sa.String(10), nullable=False),
        sa.Column("academic_year", sa.String(20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("enrollment_start_date", sa.Date(), nullable=True),
        sa.Column("enrollment_end_date", sa.Date(), nullable=True),
        sa.Column("class_days", postgresql.ARRAY(sa.String(10)), nullable=True),
        sa.Column("class_start_time", sa.Time(), nullable=True),
        sa.Column("class_end_time", sa.Time(), nullable=True),
        sa.Column("subjects", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("syllabus", sa.Text(), nullable=True),
        sa.Column("eligibility", sa.Text(), nullable=True),
        sa.Column("fee_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("total_seats", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- schedule_sessions ---
    op.create_table(
        "schedule_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("batches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("subject", sa.String(100), nullable=True),
        sa.Column("is_cancelled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_rescheduled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("notice", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("batch_id", "session_date", name="uq_session_batch_date"),
    )

    # --- enrollments ---
    op.create_table(
        "enrollments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("batches.id"), nullable=False),
        sa.Column("student_name", sa.String(150), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("grade", sa.String(20), nullable=False),
        sa.Column("exam_preference", sa.String(10), nullable=False),
        sa.Column("guardian_name", sa.String(150), nullable=True),
        sa.Column("guardian_phone", sa.String(20), nullable=True),
        sa.Column("guardian_relation", sa.String(50), nullable=True),
        sa.Column("privacy_acknowledged", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("reference", sa.String(30), nullable=False, unique=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending_payment"),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("email", "batch_id", name="uq_enrollment_email_batch"),
    )

    # --- payment_submissions ---
    op.create_table(
        "payment_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("enrollment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("enrollments.id"), nullable=False),
        sa.Column("transaction_ref", sa.String(100), nullable=False, unique=True),
        sa.Column("payment_date", sa.Date(), nullable=True),
        sa.Column("amount_claimed", sa.Numeric(10, 2), nullable=True),
        sa.Column("receipt_path", sa.Text(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="submitted"),
        sa.Column("reviewed_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- audit_log (insert-only) ---
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_email", sa.String(254), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_id", sa.String(50), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- site_settings (single row) ---
    op.create_table(
        "site_settings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("institute_name", sa.String(200), nullable=False, server_default="NEET/JEE Coaching"),
        sa.Column("tagline", sa.Text(), nullable=True),
        sa.Column("logo_path", sa.Text(), nullable=True),
        sa.Column("contact_email", sa.String(254), nullable=True),
        sa.Column("contact_phone", sa.String(20), nullable=True),
        sa.Column("contact_address", sa.Text(), nullable=True),
        sa.Column("hero_heading", sa.Text(), nullable=True),
        sa.Column("hero_subheading", sa.Text(), nullable=True),
        sa.Column("about_text", sa.Text(), nullable=True),
        sa.Column("why_choose_us_json", sa.Text(), nullable=True),
        sa.Column("faculty_json", sa.Text(), nullable=True),
        sa.Column("faq_json", sa.Text(), nullable=True),
        sa.Column("enrollment_instructions", sa.Text(), nullable=True),
        sa.Column("upi_id", sa.String(100), nullable=True),
        sa.Column("upi_name", sa.String(150), nullable=True),
        sa.Column("upi_qr_path", sa.Text(), nullable=True),
        sa.Column("payment_instructions", sa.Text(), nullable=True),
        sa.Column("facebook_url", sa.Text(), nullable=True),
        sa.Column("instagram_url", sa.Text(), nullable=True),
        sa.Column("youtube_url", sa.Text(), nullable=True),
        sa.Column("twitter_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Indexes for common queries
    op.create_index("ix_enrollments_email", "enrollments", ["email"])
    op.create_index("ix_enrollments_batch_id", "enrollments", ["batch_id"])
    op.create_index("ix_enrollments_status", "enrollments", ["status"])
    op.create_index("ix_payment_submissions_enrollment_id", "payment_submissions", ["enrollment_id"])
    op.create_index("ix_payment_submissions_status", "payment_submissions", ["status"])
    op.create_index("ix_audit_logs_target", "audit_logs", ["target_type", "target_id"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("payment_submissions")
    op.drop_table("enrollments")
    op.drop_table("schedule_sessions")
    op.drop_table("site_settings")
    op.drop_table("batches")
    op.drop_table("users")

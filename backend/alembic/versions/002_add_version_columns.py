"""Add optimistic-locking version columns to enrollments and payment_submissions.

Revision ID: 002_version_columns
Revises: 001_initial
Create Date: 2026-11-24

Why: The architecture spec requires optimistic locking via a version column on
both tables to prevent lost-update races when two admin sessions try to verify
the same payment simultaneously. The application layer increments version on
every write; a stale-read check raises a 409 Conflict before committing.
"""

from alembic import op
import sqlalchemy as sa

revision = '002_version_columns'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # server_default='1' means existing rows get version=1 without an UPDATE sweep.
    op.add_column(
        'enrollments',
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
    )
    op.add_column(
        'payment_submissions',
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
    )


def downgrade() -> None:
    op.drop_column('payment_submissions', 'version')
    op.drop_column('enrollments', 'version')

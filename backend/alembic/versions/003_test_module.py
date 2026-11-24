"""Create exam/test module tables.

Revision ID: 003_test_module
Revises: 002_version_columns
Create Date: 2026-11-24

Why: Adds the online exam system — exam_students, tests, questions,
test_attempts, attempt_answers — supporting the NEET-identical weekly
test feature.

Key constraints:
  - uq_attempt_test_student: one attempt per student per test
  - uq_question_test_number: one question per number per test
  - uq_answer_attempt_question: one answer row per question per attempt
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '003_test_module'
down_revision = '002_version_columns'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # exam_students
    op.create_table(
        'exam_students',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('username', sa.String(100), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_exam_students_username', 'exam_students', ['username'], unique=True)

    # tests
    op.create_table(
        'tests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id'),
    )

    # questions
    op.create_table(
        'questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('test_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_number', sa.Integer(), nullable=False),
        sa.Column('question_image_path', sa.String(500), nullable=False),
        sa.Column('options_image_path', sa.String(500), nullable=False),
        sa.Column('correct_option', sa.String(1), nullable=False),
        sa.ForeignKeyConstraint(['test_id'], ['tests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('test_id', 'question_number', name='uq_question_test_number'),
    )
    op.create_index('ix_questions_test_id', 'questions', ['test_id'])

    # test_attempts
    op.create_table(
        'test_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('test_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('score', sa.Numeric(8, 2), nullable=True),
        sa.Column('correct_count', sa.Integer(), nullable=True),
        sa.Column('wrong_count', sa.Integer(), nullable=True),
        sa.Column('unanswered_count', sa.Integer(), nullable=True),
        sa.Column('is_timed_out', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['test_id'], ['tests.id']),
        sa.ForeignKeyConstraint(['student_id'], ['exam_students.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('test_id', 'student_id', name='uq_attempt_test_student'),
    )
    op.create_index('ix_test_attempts_test_id', 'test_attempts', ['test_id'])
    op.create_index('ix_test_attempts_student_id', 'test_attempts', ['student_id'])

    # attempt_answers
    op.create_table(
        'attempt_answers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('attempt_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('selected_option', sa.String(1), nullable=True),
        sa.Column('is_marked_for_review', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['attempt_id'], ['test_attempts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('attempt_id', 'question_id', name='uq_answer_attempt_question'),
    )
    op.create_index('ix_attempt_answers_attempt_id', 'attempt_answers', ['attempt_id'])


def downgrade() -> None:
    op.drop_table('attempt_answers')
    op.drop_table('test_attempts')
    op.drop_table('questions')
    op.drop_table('tests')
    op.drop_index('ix_exam_students_username', 'exam_students')
    op.drop_table('exam_students')

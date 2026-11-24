"""
Test module models — online exam system identical to NEET.

Layer: Models

Tables:
  exam_students   — Student accounts created by admin for exam access.
  tests           — An exam (title, duration, schedule).
  questions       — 45 questions per test; each has a question image and an
                    options image (A/B/C/D shown as one combined image).
  test_attempts   — One row per student per test; tracks start/submit time
                    and final score. UNIQUE(test_id, student_id) enforces
                    the one-attempt rule at the DB level.
  attempt_answers — One row per question per attempt. Stores the student's
                    selected option (A/B/C/D) and mark-for-review flag.

Scoring (NEET rules):
  Correct  → +4
  Wrong    → -1
  No answer → 0
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, Numeric,
    String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin


class ExamStudent(Base, UUIDMixin, TimestampMixin):
    """
    Student account for the exam portal.

    Created by admin — students cannot self-register.
    Completely separate from the enrollment system.
    """
    __tablename__ = "exam_students"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    attempts: Mapped[List["TestAttempt"]] = relationship("TestAttempt", back_populates="student")


class Test(Base, UUIDMixin, TimestampMixin):
    """
    An exam session — weekly or twice-weekly practice test.

    is_published controls student visibility. Admin can prepare a test in
    advance and only publish it when ready.
    """
    __tablename__ = "tests"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    # When null, the test is available immediately once published
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    questions: Mapped[List["Question"]] = relationship(
        "Question", back_populates="test",
        order_by="Question.question_number",
        cascade="all, delete-orphan",
    )
    attempts: Mapped[List["TestAttempt"]] = relationship("TestAttempt", back_populates="test")


class Question(Base, UUIDMixin, TimestampMixin):
    """
    One question in a test.

    question_image_path  — the question (text + diagram) as a single image.
    options_image_path   — all four options A/B/C/D shown in one image.
    correct_option       — 'A', 'B', 'C', or 'D' (never sent to students
                           during an active attempt).
    """
    __tablename__ = "questions"

    test_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tests.id"), nullable=False, index=True
    )
    question_number: Mapped[int] = mapped_column(Integer, nullable=False)

    question_image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    options_image_path: Mapped[str] = mapped_column(String(500), nullable=False)

    # Never exposed to the student during an active attempt
    correct_option: Mapped[str] = mapped_column(String(1), nullable=False)

    test: Mapped["Test"] = relationship("Test", back_populates="questions")
    answers: Mapped[List["AttemptAnswer"]] = relationship("AttemptAnswer", back_populates="question")

    __table_args__ = (
        UniqueConstraint("test_id", "question_number", name="uq_question_test_number"),
    )


class TestAttempt(Base, UUIDMixin, TimestampMixin):
    """
    One student's single attempt at a test.

    submitted_at being None means the attempt is still in progress.
    score is calculated and stored only on submission.
    UNIQUE(test_id, student_id) prevents duplicate attempts at DB level.
    """
    __tablename__ = "test_attempts"

    test_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tests.id"), nullable=False, index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exam_students.id"), nullable=False, index=True
    )

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Populated on submission
    score: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    correct_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    wrong_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    unanswered_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_timed_out: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    test: Mapped["Test"] = relationship("Test", back_populates="attempts")
    student: Mapped["ExamStudent"] = relationship("ExamStudent", back_populates="attempts")
    answers: Mapped[List["AttemptAnswer"]] = relationship(
        "AttemptAnswer", back_populates="attempt", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("test_id", "student_id", name="uq_attempt_test_student"),
    )


class AttemptAnswer(Base, UUIDMixin):
    """
    One answer within an attempt.

    selected_option is null when the student has visited the question but
    not chosen an answer (contributes 0 marks).
    is_marked_for_review mirrors the NEET palette's purple state.
    """
    __tablename__ = "attempt_answers"

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("test_attempts.id"), nullable=False, index=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False
    )

    selected_option: Mapped[Optional[str]] = mapped_column(String(1), nullable=True)
    is_marked_for_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    attempt: Mapped["TestAttempt"] = relationship("TestAttempt", back_populates="answers")
    question: Mapped["Question"] = relationship("Question", back_populates="answers")

    __table_args__ = (
        UniqueConstraint("attempt_id", "question_id", name="uq_answer_attempt_question"),
    )

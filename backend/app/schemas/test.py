"""Pydantic schemas for the exam/test module."""

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


# ── Admin: Test management ────────────────────────────────────────────────────

class TestCreate(BaseModel):
    title: str
    description: Optional[str] = None
    duration_minutes: int = 60
    scheduled_at: Optional[datetime] = None


class TestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    is_published: Optional[bool] = None


class TestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    description: Optional[str]
    duration_minutes: int
    scheduled_at: Optional[datetime]
    is_published: bool
    question_count: int = 0
    created_at: datetime


# ── Admin: Question management ────────────────────────────────────────────────

class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    test_id: uuid.UUID
    question_number: int
    question_image_path: str
    options_image_path: str
    correct_option: str


# ── Admin: Exam students ──────────────────────────────────────────────────────

class ExamStudentCreate(BaseModel):
    name: str
    username: str
    password: str


class ExamStudentUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class ExamStudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    username: str
    is_active: bool
    created_at: datetime


# ── Student: auth ─────────────────────────────────────────────────────────────

class StudentLoginRequest(BaseModel):
    username: str
    password: str


class StudentMeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    username: str


# ── Student: test list ────────────────────────────────────────────────────────

class StudentTestResponse(BaseModel):
    """Test as seen by a student — no correct answers included."""
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    description: Optional[str]
    duration_minutes: int
    scheduled_at: Optional[datetime]
    question_count: int = 0
    # Student's attempt status
    attempt_id: Optional[uuid.UUID] = None
    is_started: bool = False
    is_submitted: bool = False


# ── Student: question during exam (NO correct_option) ────────────────────────

class ExamQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    question_number: int
    question_image_path: str
    options_image_path: str
    # correct_option intentionally omitted


# ── Student: attempt and answers ──────────────────────────────────────────────

class AttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    test_id: uuid.UUID
    started_at: datetime
    submitted_at: Optional[datetime]
    time_remaining_seconds: Optional[int] = None


class SaveAnswerRequest(BaseModel):
    question_id: uuid.UUID
    selected_option: Optional[str] = None   # A/B/C/D or null to clear
    is_marked_for_review: bool = False


class AnswerState(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    question_id: uuid.UUID
    selected_option: Optional[str]
    is_marked_for_review: bool


# ── Student: result (after submission) ───────────────────────────────────────

class ResultQuestionDetail(BaseModel):
    question_number: int
    question_image_path: str
    options_image_path: str
    correct_option: str
    student_option: Optional[str]
    marks: float   # +4, -1, or 0


class ResultResponse(BaseModel):
    attempt_id: uuid.UUID
    test_title: str
    score: float
    correct_count: int
    wrong_count: int
    unanswered_count: int
    total_questions: int
    questions: List[ResultQuestionDetail]


# ── Admin: results view ───────────────────────────────────────────────────────

class AttemptSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    student_name: str
    student_username: str
    started_at: datetime
    submitted_at: Optional[datetime]
    score: Optional[float]
    correct_count: Optional[int]
    wrong_count: Optional[int]
    unanswered_count: Optional[int]
    is_timed_out: bool

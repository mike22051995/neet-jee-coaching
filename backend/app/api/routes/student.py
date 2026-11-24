"""
Student-facing routes — login, exam access, answer saving, submission.

Layer: API / Routes
All exam routes require a valid student_token cookie set at login.
correct_option is never included in responses while an attempt is active.
"""

import logging
import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.dependencies import get_current_student
from app.core.limiter import limiter
from app.db.base import get_db_session
from app.models.test import ExamStudent
from app.schemas.test import (
    AttemptResponse,
    AnswerState,
    ExamQuestionResponse,
    ResultResponse,
    SaveAnswerRequest,
    StudentLoginRequest,
    StudentMeResponse,
    StudentTestResponse,
)
from app.services.student_service import StudentService
from app.services.test_service import TestService

router = APIRouter(prefix="/student", tags=["student"])
settings = get_settings()
logger = logging.getLogger(__name__)

_COOKIE = "student_token"


@router.post("/login")
@limiter.limit("10/15minutes")
async def student_login(
    request: Request,
    data: StudentLoginRequest,
    db: AsyncSession = Depends(get_db_session),
) -> JSONResponse:
    """Student login — sets httpOnly student_token cookie."""
    service = StudentService(db)
    token_data = await service.authenticate(data.username, data.password)

    response = JSONResponse(content={"message": "ok"})
    response.set_cookie(
        key=_COOKIE,
        value=token_data["access_token"],
        httponly=True,
        max_age=8 * 3600,
        samesite="none" if settings.is_production else "lax",
        secure=settings.is_production,
        path="/",
    )
    return response


@router.post("/logout")
async def student_logout() -> JSONResponse:
    response = JSONResponse(content={"message": "logged out"})
    response.delete_cookie(key=_COOKIE, path="/", samesite="lax")
    return response


@router.get("/me", response_model=StudentMeResponse)
async def student_me(student: ExamStudent = Depends(get_current_student)) -> ExamStudent:
    return student


# ── Tests ─────────────────────────────────────────────────────────────────────

@router.get("/tests")
async def list_tests(
    student: ExamStudent = Depends(get_current_student),
    db: AsyncSession = Depends(get_db_session),
):
    """List all published tests with the student's attempt status."""
    service = TestService(db)
    items = await service.get_available_tests(student)
    result = []
    for item in items:
        t = item["test"]
        result.append({
            "id": str(t.id),
            "title": t.title,
            "description": t.description,
            "duration_minutes": t.duration_minutes,
            "scheduled_at": t.scheduled_at.isoformat() if t.scheduled_at else None,
            "question_count": item["question_count"],
            "attempt_id": str(item["attempt_id"]) if item["attempt_id"] else None,
            "is_started": item["is_started"],
            "is_submitted": item["is_submitted"],
        })
    return result


@router.post("/tests/{test_id}/start", response_model=AttemptResponse)
async def start_test(
    test_id: uuid.UUID,
    student: ExamStudent = Depends(get_current_student),
    db: AsyncSession = Depends(get_db_session),
):
    """Start a test attempt. Can only be done once per student per test."""
    service = TestService(db)
    attempt = await service.start_attempt(test_id, student)
    from datetime import datetime, timezone
    elapsed = (datetime.now(timezone.utc) - attempt.started_at).total_seconds()
    time_remaining = max(0, attempt.test.duration_minutes * 60 - int(elapsed)) if hasattr(attempt, 'test') else None
    return {
        "id": str(attempt.id),
        "test_id": str(attempt.test_id),
        "started_at": attempt.started_at.isoformat(),
        "submitted_at": None,
        "time_remaining_seconds": attempt.test.duration_minutes * 60 if hasattr(attempt, 'test') else None,
    }


@router.get("/attempts/{attempt_id}")
async def get_attempt(
    attempt_id: uuid.UUID,
    student: ExamStudent = Depends(get_current_student),
    db: AsyncSession = Depends(get_db_session),
):
    """Get exam data — questions (without answers) + current answer state."""
    service = TestService(db)
    data = await service.get_attempt_with_questions(attempt_id, student)
    attempt = data["attempt"]

    if attempt.submitted_at:
        return {"submitted": True, "attempt_id": str(attempt.id)}

    questions = [
        {
            "id": str(q.id),
            "question_number": q.question_number,
            "question_image_path": q.question_image_path,
            "options_image_path": q.options_image_path,
            # correct_option intentionally omitted
        }
        for q in data["questions"]
    ]

    answer_states = [
        {
            "question_id": str(qid),
            "selected_option": a.selected_option,
            "is_marked_for_review": a.is_marked_for_review,
        }
        for qid, a in data["answers"].items()
    ]

    return {
        "attempt_id": str(attempt.id),
        "test_id": str(attempt.test_id),
        "test_title": attempt.test.title,
        "duration_minutes": attempt.test.duration_minutes,
        "started_at": attempt.started_at.isoformat(),
        "time_remaining_seconds": data["time_remaining_seconds"],
        "questions": questions,
        "answers": answer_states,
        "submitted": False,
    }


@router.put("/attempts/{attempt_id}/answer")
async def save_answer(
    attempt_id: uuid.UUID,
    data: SaveAnswerRequest,
    student: ExamStudent = Depends(get_current_student),
    db: AsyncSession = Depends(get_db_session),
):
    """Save one answer (called on every option selection)."""
    service = TestService(db)
    answer = await service.save_answer(attempt_id, data, student)
    return {
        "question_id": str(answer.question_id),
        "selected_option": answer.selected_option,
        "is_marked_for_review": answer.is_marked_for_review,
    }


@router.post("/attempts/{attempt_id}/submit", response_model=ResultResponse)
async def submit_attempt(
    attempt_id: uuid.UUID,
    student: ExamStudent = Depends(get_current_student),
    db: AsyncSession = Depends(get_db_session),
    timed_out: bool = False,
):
    """Submit the test and get the result with correct answers."""
    service = TestService(db)
    return await service.submit_attempt(attempt_id, student, timed_out=timed_out)


@router.get("/attempts/{attempt_id}/result", response_model=ResultResponse)
async def get_result(
    attempt_id: uuid.UUID,
    student: ExamStudent = Depends(get_current_student),
    db: AsyncSession = Depends(get_db_session),
):
    """Get result for an already-submitted attempt."""
    service = TestService(db)
    return await service.submit_attempt(attempt_id, student)

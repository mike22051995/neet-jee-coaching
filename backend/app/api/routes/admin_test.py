"""
Admin routes for the exam/test module.

Layer: API / Routes
All routes require admin authentication.

Responsibilities:
  - CRUD for Tests
  - Upload question images + set correct answer
  - Create/manage exam student accounts
  - View attempt results for any test
"""

import logging
import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.dependencies import require_admin
from app.db.base import get_db_session
from app.models.user import User
from app.schemas.test import (
    AttemptSummary,
    ExamStudentCreate,
    ExamStudentResponse,
    ExamStudentUpdate,
    QuestionResponse,
    TestCreate,
    TestResponse,
    TestUpdate,
)
from app.services.student_service import StudentService
from app.services.test_service import TestService

router = APIRouter(prefix="/admin/tests", tags=["admin-tests"])
settings = get_settings()
logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB


# ── Tests ──────────────────────────────────────────────────────────────────────

@router.post("", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
async def create_test(
    data: TestCreate,
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_admin),
):
    service = TestService(db)
    test = await service.create_test(data)
    return {**test.__dict__, "question_count": 0}


@router.get("")
async def list_tests(
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_admin),
):
    service = TestService(db)
    tests = await service.list_tests()
    return [
        {
            "id": str(t.id),
            "title": t.title,
            "description": t.description,
            "duration_minutes": t.duration_minutes,
            "scheduled_at": t.scheduled_at.isoformat() if t.scheduled_at else None,
            "is_published": t.is_published,
            "question_count": len(t.questions) if hasattr(t, "questions") and t.questions else 0,
            "created_at": t.created_at.isoformat(),
        }
        for t in tests
    ]


@router.get("/{test_id}")
async def get_test(
    test_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_admin),
):
    service = TestService(db)
    test = await service.get_test(test_id)
    return {
        "id": str(test.id),
        "title": test.title,
        "description": test.description,
        "duration_minutes": test.duration_minutes,
        "scheduled_at": test.scheduled_at.isoformat() if test.scheduled_at else None,
        "is_published": test.is_published,
        "question_count": len(test.questions),
        "created_at": test.created_at.isoformat(),
        "questions": [
            {
                "id": str(q.id),
                "question_number": q.question_number,
                "question_image_path": q.question_image_path,
                "options_image_path": q.options_image_path,
                "correct_option": q.correct_option,
            }
            for q in test.questions
        ],
    }


@router.patch("/{test_id}", response_model=TestResponse)
async def update_test(
    test_id: uuid.UUID,
    data: TestUpdate,
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_admin),
):
    service = TestService(db)
    test = await service.update_test(test_id, data)
    return {**test.__dict__, "question_count": len(test.questions) if hasattr(test, "questions") else 0}


@router.delete("/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test(
    test_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_admin),
):
    service = TestService(db)
    await service.delete_test(test_id)


# ── Questions ─────────────────────────────────────────────────────────────────

@router.post("/{test_id}/questions", response_model=QuestionResponse)
async def upload_question(
    test_id: uuid.UUID,
    question_number: int = Form(...),
    correct_option: str = Form(...),
    question_image: UploadFile = File(...),
    options_image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_admin),
):
    """
    Upload question + options images and set the correct answer.
    Replaces the question if one already exists for this number.
    """
    if correct_option.upper() not in ("A", "B", "C", "D"):
        raise HTTPException(status_code=400, detail="correct_option must be A, B, C, or D")

    if question_number < 1 or question_number > 200:
        raise HTTPException(status_code=400, detail="question_number must be between 1 and 200")

    # Validate and save both images
    q_path = await _save_image(question_image, test_id, f"q{question_number}_question")
    o_path = await _save_image(options_image, test_id, f"q{question_number}_options")

    service = TestService(db)
    question = await service.upsert_question(
        test_id=test_id,
        question_number=question_number,
        question_image_path=q_path,
        options_image_path=o_path,
        correct_option=correct_option.upper(),
    )
    return question


@router.delete("/{test_id}/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    test_id: uuid.UUID,
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_admin),
):
    service = TestService(db)
    await service.delete_question(test_id, question_id)


# ── Results ───────────────────────────────────────────────────────────────────

@router.get("/{test_id}/results")
async def get_test_results(
    test_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_admin),
):
    service = TestService(db)
    summaries = await service.get_test_results(test_id)
    return [s.model_dump() for s in summaries]


# ── Exam students ─────────────────────────────────────────────────────────────

@router.post("/students", response_model=ExamStudentResponse, status_code=status.HTTP_201_CREATED)
async def create_exam_student(
    data: ExamStudentCreate,
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_admin),
):
    service = StudentService(db)
    return await service.create_student(data)


@router.get("/students")
async def list_exam_students(
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_admin),
):
    service = StudentService(db)
    students = await service.list_students()
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "username": s.username,
            "is_active": s.is_active,
            "created_at": s.created_at.isoformat(),
        }
        for s in students
    ]


@router.patch("/students/{student_id}", response_model=ExamStudentResponse)
async def update_exam_student(
    student_id: uuid.UUID,
    data: ExamStudentUpdate,
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_admin),
):
    service = StudentService(db)
    return await service.update_student(student_id, data)


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _save_image(upload: UploadFile, test_id: uuid.UUID, name: str) -> str:
    """Validate MIME type/size, save to disk, return the served path."""
    if upload.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image type '{upload.content_type}'. Use JPEG, PNG, or WebP.",
        )

    content = await upload.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="Image too large (max 5 MB)")

    ext = upload.filename.rsplit(".", 1)[-1].lower() if upload.filename and "." in upload.filename else "jpg"
    filename = f"{name}.{ext}"

    test_dir = os.path.join(settings.UPLOAD_DIR, "questions", str(test_id))
    os.makedirs(test_dir, exist_ok=True)

    filepath = os.path.join(test_dir, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    # Return the URL path that nginx will serve
    return f"/uploads/questions/{test_id}/{filename}"

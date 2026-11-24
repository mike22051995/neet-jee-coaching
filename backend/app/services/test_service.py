"""
Test service — exam creation, question management, attempt lifecycle, scoring.

Layer: Service

NEET scoring rules (enforced here, not in the model):
  Correct answer  → +4 marks
  Wrong answer    → -1 mark
  Not attempted   → 0 marks

Security rules:
  - correct_option is NEVER included in responses sent during an active attempt.
  - Attempts can only be started once per student per test (DB unique constraint
    + service check).
  - Answers can only be saved while the attempt is still in progress
    (submitted_at is None).
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.test import AttemptAnswer, ExamStudent, Question, Test, TestAttempt
from app.schemas.test import (
    AttemptSummary,
    ResultQuestionDetail,
    ResultResponse,
    SaveAnswerRequest,
    TestCreate,
    TestUpdate,
)

logger = logging.getLogger(__name__)

CORRECT_MARKS = 4.0
WRONG_MARKS = -1.0


class TestService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Admin: test CRUD ──────────────────────────────────────────────────────

    async def create_test(self, data: TestCreate) -> Test:
        test = Test(**data.model_dump())
        self.db.add(test)
        await self.db.commit()
        await self.db.refresh(test)
        return test

    async def list_tests(self, published_only: bool = False) -> List[Test]:
        q = select(Test).order_by(Test.created_at.desc())
        if published_only:
            q = q.where(Test.is_published.is_(True))
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_test(self, test_id: uuid.UUID) -> Test:
        result = await self.db.execute(
            select(Test).where(Test.id == test_id).options(selectinload(Test.questions))
        )
        test = result.scalar_one_or_none()
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        return test

    async def update_test(self, test_id: uuid.UUID, data: TestUpdate) -> Test:
        test = await self.get_test(test_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(test, field, value)
        await self.db.commit()
        await self.db.refresh(test)
        return test

    async def delete_test(self, test_id: uuid.UUID) -> None:
        test = await self.get_test(test_id)
        await self.db.delete(test)
        await self.db.commit()

    # ── Admin: question management ────────────────────────────────────────────

    async def upsert_question(
        self,
        test_id: uuid.UUID,
        question_number: int,
        question_image_path: str,
        options_image_path: str,
        correct_option: str,
    ) -> Question:
        """Create or replace question N in a test."""
        result = await self.db.execute(
            select(Question).where(
                Question.test_id == test_id,
                Question.question_number == question_number,
            )
        )
        question = result.scalar_one_or_none()

        if question:
            question.question_image_path = question_image_path
            question.options_image_path = options_image_path
            question.correct_option = correct_option.upper()
        else:
            question = Question(
                test_id=test_id,
                question_number=question_number,
                question_image_path=question_image_path,
                options_image_path=options_image_path,
                correct_option=correct_option.upper(),
            )
            self.db.add(question)

        await self.db.commit()
        await self.db.refresh(question)
        return question

    async def delete_question(self, test_id: uuid.UUID, question_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(Question).where(Question.id == question_id, Question.test_id == test_id)
        )
        q = result.scalar_one_or_none()
        if not q:
            raise HTTPException(status_code=404, detail="Question not found")
        await self.db.delete(q)
        await self.db.commit()

    # ── Student: attempt lifecycle ────────────────────────────────────────────

    async def get_available_tests(self, student: ExamStudent) -> List[dict]:
        """Return published tests with the student's attempt status."""
        tests_result = await self.db.execute(
            select(Test)
            .where(Test.is_published.is_(True))
            .options(selectinload(Test.questions))
            .order_by(Test.scheduled_at.desc().nullslast(), Test.created_at.desc())
        )
        tests = list(tests_result.scalars().all())

        # Fetch all attempts for this student at once
        attempts_result = await self.db.execute(
            select(TestAttempt).where(TestAttempt.student_id == student.id)
        )
        attempts_map = {a.test_id: a for a in attempts_result.scalars().all()}

        output = []
        for test in tests:
            attempt = attempts_map.get(test.id)
            output.append({
                "test": test,
                "question_count": len(test.questions),
                "attempt_id": attempt.id if attempt else None,
                "is_started": attempt is not None,
                "is_submitted": attempt is not None and attempt.submitted_at is not None,
            })
        return output

    async def start_attempt(self, test_id: uuid.UUID, student: ExamStudent) -> TestAttempt:
        """
        Start a new attempt. Raises 409 if already started, 404 if test not found,
        400 if test not published or not yet reached scheduled time.
        """
        test = await self.get_test(test_id)

        if not test.is_published:
            raise HTTPException(status_code=400, detail="Test is not available")

        if test.scheduled_at and datetime.now(timezone.utc) < test.scheduled_at:
            raise HTTPException(status_code=400, detail="Test has not started yet")

        # Check existing attempt
        existing = await self.db.execute(
            select(TestAttempt).where(
                TestAttempt.test_id == test_id,
                TestAttempt.student_id == student.id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="You have already attempted this test")

        attempt = TestAttempt(
            test_id=test_id,
            student_id=student.id,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(attempt)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status_code=409, detail="You have already attempted this test")

        await self.db.refresh(attempt)
        return attempt

    async def get_attempt_with_questions(
        self, attempt_id: uuid.UUID, student: ExamStudent
    ) -> dict:
        """Return attempt + questions (WITHOUT correct_option)."""
        result = await self.db.execute(
            select(TestAttempt)
            .where(TestAttempt.id == attempt_id, TestAttempt.student_id == student.id)
            .options(
                selectinload(TestAttempt.answers),
                selectinload(TestAttempt.test).selectinload(Test.questions),
            )
        )
        attempt = result.scalar_one_or_none()
        if not attempt:
            raise HTTPException(status_code=404, detail="Attempt not found")

        # Calculate time remaining
        elapsed = (datetime.now(timezone.utc) - attempt.started_at).total_seconds()
        time_remaining = max(0, attempt.test.duration_minutes * 60 - int(elapsed))

        return {
            "attempt": attempt,
            "questions": attempt.test.questions,
            "answers": {str(a.question_id): a for a in attempt.answers},
            "time_remaining_seconds": time_remaining,
        }

    async def save_answer(
        self, attempt_id: uuid.UUID, data: SaveAnswerRequest, student: ExamStudent
    ) -> AttemptAnswer:
        """Save or update one answer. Attempt must still be in progress."""
        result = await self.db.execute(
            select(TestAttempt).where(
                TestAttempt.id == attempt_id,
                TestAttempt.student_id == student.id,
            )
        )
        attempt = result.scalar_one_or_none()
        if not attempt:
            raise HTTPException(status_code=404, detail="Attempt not found")
        if attempt.submitted_at:
            raise HTTPException(status_code=400, detail="Attempt already submitted")

        # Upsert the answer row
        ans_result = await self.db.execute(
            select(AttemptAnswer).where(
                AttemptAnswer.attempt_id == attempt_id,
                AttemptAnswer.question_id == data.question_id,
            )
        )
        answer = ans_result.scalar_one_or_none()

        if answer:
            answer.selected_option = data.selected_option.upper() if data.selected_option else None
            answer.is_marked_for_review = data.is_marked_for_review
        else:
            answer = AttemptAnswer(
                attempt_id=attempt_id,
                question_id=data.question_id,
                selected_option=data.selected_option.upper() if data.selected_option else None,
                is_marked_for_review=data.is_marked_for_review,
            )
            self.db.add(answer)

        await self.db.commit()
        await self.db.refresh(answer)
        return answer

    async def submit_attempt(
        self, attempt_id: uuid.UUID, student: ExamStudent, timed_out: bool = False
    ) -> ResultResponse:
        """
        Submit and score the attempt. Idempotent — returns existing result if
        already submitted.
        """
        result = await self.db.execute(
            select(TestAttempt)
            .where(TestAttempt.id == attempt_id, TestAttempt.student_id == student.id)
            .options(
                selectinload(TestAttempt.answers),
                selectinload(TestAttempt.test).selectinload(Test.questions),
            )
        )
        attempt = result.scalar_one_or_none()
        if not attempt:
            raise HTTPException(status_code=404, detail="Attempt not found")

        if not attempt.submitted_at:
            # Score it
            answers_map = {str(a.question_id): a for a in attempt.answers}
            correct = wrong = unanswered = 0
            total_score = 0.0

            for q in attempt.test.questions:
                ans = answers_map.get(str(q.id))
                if ans and ans.selected_option:
                    if ans.selected_option == q.correct_option:
                        correct += 1
                        total_score += CORRECT_MARKS
                    else:
                        wrong += 1
                        total_score += WRONG_MARKS
                else:
                    unanswered += 1

            attempt.submitted_at = datetime.now(timezone.utc)
            attempt.score = total_score
            attempt.correct_count = correct
            attempt.wrong_count = wrong
            attempt.unanswered_count = unanswered
            attempt.is_timed_out = timed_out
            await self.db.commit()
            await self.db.refresh(attempt)

        return self._build_result(attempt)

    def _build_result(self, attempt: TestAttempt) -> ResultResponse:
        answers_map = {str(a.question_id): a for a in attempt.answers}
        details = []
        for q in attempt.test.questions:
            ans = answers_map.get(str(q.id))
            student_opt = ans.selected_option if ans else None
            if student_opt and student_opt == q.correct_option:
                marks = CORRECT_MARKS
            elif student_opt:
                marks = WRONG_MARKS
            else:
                marks = 0.0
            details.append(ResultQuestionDetail(
                question_number=q.question_number,
                question_image_path=q.question_image_path,
                options_image_path=q.options_image_path,
                correct_option=q.correct_option,
                student_option=student_opt,
                marks=marks,
            ))

        return ResultResponse(
            attempt_id=attempt.id,
            test_title=attempt.test.title,
            score=float(attempt.score or 0),
            correct_count=attempt.correct_count or 0,
            wrong_count=attempt.wrong_count or 0,
            unanswered_count=attempt.unanswered_count or 0,
            total_questions=len(attempt.test.questions),
            questions=details,
        )

    # ── Admin: view results ───────────────────────────────────────────────────

    async def get_test_results(self, test_id: uuid.UUID) -> List[AttemptSummary]:
        result = await self.db.execute(
            select(TestAttempt)
            .where(TestAttempt.test_id == test_id)
            .options(selectinload(TestAttempt.student))
            .order_by(TestAttempt.submitted_at.desc().nullslast())
        )
        attempts = list(result.scalars().all())
        summaries = []
        for a in attempts:
            summaries.append(AttemptSummary(
                id=a.id,
                student_name=a.student.name,
                student_username=a.student.username,
                started_at=a.started_at,
                submitted_at=a.submitted_at,
                score=float(a.score) if a.score is not None else None,
                correct_count=a.correct_count,
                wrong_count=a.wrong_count,
                unanswered_count=a.unanswered_count,
                is_timed_out=a.is_timed_out,
            ))
        return summaries

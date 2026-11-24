"""
Student authentication service — login for exam portal students.

Layer: Service
Students are created by admin. They cannot self-register.
Auth uses the same JWT + httpOnly cookie pattern as the admin,
but stored in a separate 'student_token' cookie.
"""

import logging
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.test import ExamStudent
from app.schemas.test import ExamStudentCreate, ExamStudentResponse

logger = logging.getLogger(__name__)
settings = get_settings()


class StudentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def authenticate(self, username: str, password: str) -> dict:
        """Validate student credentials and return a JWT token dict."""
        result = await self.db.execute(
            select(ExamStudent).where(ExamStudent.username == username.lower())
        )
        student = result.scalar_one_or_none()

        dummy = hash_password("dummy") if student is None else student.hashed_password
        ok = verify_password(password, dummy if student is None else student.hashed_password)

        if student is None or not ok or not student.is_active:
            logger.warning("Failed student login: %s", username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        token = create_access_token(
            subject=str(student.id),
            role="student",
            expires_delta=timedelta(hours=8),   # longer session for exam day
        )
        logger.info("Student login: %s", student.username)
        return {"access_token": token, "token_type": "bearer"}

    async def create_student(self, data: ExamStudentCreate) -> ExamStudent:
        """Admin creates a student account."""
        existing = await self.db.execute(
            select(ExamStudent).where(ExamStudent.username == data.username.lower())
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Username already exists")

        student = ExamStudent(
            name=data.name,
            username=data.username.lower(),
            hashed_password=hash_password(data.password),
            is_active=True,
        )
        self.db.add(student)
        await self.db.commit()
        await self.db.refresh(student)
        return student

    async def list_students(self) -> list[ExamStudent]:
        result = await self.db.execute(
            select(ExamStudent).order_by(ExamStudent.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_student(self, student_id, data) -> ExamStudent:
        result = await self.db.execute(
            select(ExamStudent).where(ExamStudent.id == student_id)
        )
        student = result.scalar_one_or_none()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        if data.name is not None:
            student.name = data.name
        if data.is_active is not None:
            student.is_active = data.is_active
        if data.password:
            student.hashed_password = hash_password(data.password)

        await self.db.commit()
        await self.db.refresh(student)
        return student

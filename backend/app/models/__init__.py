"""
Import all models here so Alembic can find them when generating migrations.

Alembic's autogenerate compares SQLAlchemy's MetaData (populated by importing
models) against the current database schema. If a model is not imported here,
Alembic won't know about it and won't generate migration steps for it.
"""
from app.models.user import User
from app.models.batch import Batch, ScheduleSession
from app.models.enrollment import Enrollment, PaymentSubmission, AuditLog
from app.models.site_settings import SiteSettings
from app.models.test import ExamStudent, Test, Question, TestAttempt, AttemptAnswer

__all__ = [
    "User",
    "Batch",
    "ScheduleSession",
    "Enrollment",
    "PaymentSubmission",
    "AuditLog",
    "SiteSettings",
    "ExamStudent",
    "Test",
    "Question",
    "TestAttempt",
    "AttemptAnswer",
]

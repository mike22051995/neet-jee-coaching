"""
User model — admin accounts only. Students are not system users.

Design decision: Students enroll via a form and are tracked through the
Enrollment model. They have no login, no password, and no user account.
This keeps the data model simple and minimises the personal data we store.
Only institute administrators need a login.

Layer: Models
"""

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin


class User(Base, UUIDMixin, TimestampMixin):
    """
    Admin user account.

    Columns:
    - email: unique login identifier
    - hashed_password: bcrypt hash — never store plain-text
    - name: display name in the admin dashboard
    - is_active: soft-disable an account without deleting it
    - role: always 'admin' for now; extensible for future roles
    """
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="admin", nullable=False)

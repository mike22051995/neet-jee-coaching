"""
SiteSettings model — all configurable website content in the database.

Design decision: Instead of a typical key-value table (which is flexible but
hard to validate), we use a single-row settings table with typed columns.
This means:
- Each setting has a known type (string, text, etc.)
- Pydantic can validate updates
- SQL queries are simple (SELECT * FROM site_settings WHERE id = 1)

The table always has exactly ONE row. The admin dashboard reads and updates
this row. If the row doesn't exist yet, it is created with defaults on first run.

Layer: Models
"""

from typing import Optional
from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin


class SiteSettings(Base, UUIDMixin, TimestampMixin):
    """
    Single-row table storing all public-facing website configuration.

    Every field can be edited through the admin dashboard without
    restarting or redeploying the application.
    """
    __tablename__ = "site_settings"

    # ── Institute Identity ─────────────────────────────────────────────────
    institute_name: Mapped[str] = mapped_column(
        String(200), default="Excellence Coaching Institute", nullable=False
    )
    tagline: Mapped[Optional[str]] = mapped_column(
        String(300), default="Achieving Excellence in NEET & JEE", nullable=True
    )
    logo_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # ── Contact ───────────────────────────────────────────────────────────
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    contact_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Homepage Content ──────────────────────────────────────────────────
    hero_heading: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    hero_subheading: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    about_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Why choose us — stored as JSON text e.g. '[{"title":"...","body":"..."}]'
    why_choose_us_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Faculty section — stored as JSON text array of faculty objects
    faculty_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # FAQ — stored as JSON text array of {question, answer} objects
    faq_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Enrollment instructions shown before the form
    enrollment_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Payment / UPI ─────────────────────────────────────────────────────
    upi_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    upi_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    upi_qr_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    payment_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Social Links ──────────────────────────────────────────────────────
    social_whatsapp: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    social_telegram: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    social_youtube: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

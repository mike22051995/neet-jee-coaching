"""Schemas for SiteSettings."""
from typing import Optional
from pydantic import BaseModel, ConfigDict


class SiteSettingsUpdate(BaseModel):
    """All fields optional — admin updates only the fields they want to change."""
    institute_name: Optional[str] = None
    tagline: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_address: Optional[str] = None
    hero_heading: Optional[str] = None
    hero_subheading: Optional[str] = None
    about_text: Optional[str] = None
    why_choose_us_json: Optional[str] = None
    faculty_json: Optional[str] = None
    faq_json: Optional[str] = None
    enrollment_instructions: Optional[str] = None
    upi_id: Optional[str] = None
    upi_name: Optional[str] = None
    payment_instructions: Optional[str] = None
    social_whatsapp: Optional[str] = None
    social_telegram: Optional[str] = None
    social_youtube: Optional[str] = None


class SiteSettingsResponse(SiteSettingsUpdate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    logo_path: Optional[str] = None
    upi_qr_path: Optional[str] = None

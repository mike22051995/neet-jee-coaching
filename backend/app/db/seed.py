"""
Seed script: creates a sample NEET batch and site settings for development.

Run with:
    cd backend
    python -m app.db.seed
"""

import asyncio
import uuid
from datetime import date, time
from sqlalchemy import select
from app.db.base import AsyncSessionLocal
from app.models.batch import Batch, BatchStatus, ExamType
from app.models.site_settings import SiteSettings
from app.services.auth_service import AuthService


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        # Ensure admin account exists
        await AuthService.ensure_admin_exists(session)

        # Create site settings if missing
        result = await session.execute(select(SiteSettings).limit(1))
        settings = result.scalar_one_or_none()
        if not settings:
            settings = SiteSettings(
                institute_name="Bright Future Coaching",
                tagline="Your Success, Our Mission — NEET & JEE Excellence Since 2010",
                contact_email="info@brightfuturecoaching.in",
                contact_phone="+91 98765 43210",
                contact_address="123, Knowledge Park, Near City Mall, Patna, Bihar 800001",
                hero_heading="Crack NEET & JEE with Confidence",
                hero_subheading="Expert faculty, structured curriculum, and personalised guidance for students across Bihar. Join thousands of successful alumni.",
                about_text=(
                    "Bright Future Coaching was founded in 2010 with one goal: "
                    "to make quality medical and engineering entrance coaching accessible to every student in Bihar. "
                    "Our team of experienced educators has helped more than 2,000 students secure seats in top medical colleges and IITs."
                ),
                enrollment_instructions=(
                    "1. Fill in the enrollment form with accurate details.\n"
                    "2. You will receive a unique reference number.\n"
                    "3. Pay the fees via UPI using the QR code on the payment page.\n"
                    "4. Submit the UPI transaction reference number.\n"
                    "5. Wait for admin verification — your enrollment will be confirmed within 24 hours."
                ),
                upi_id="brightfuture@upi",
                upi_name="Bright Future Coaching",
                payment_instructions=(
                    "Scan the QR code with any UPI app (PhonePe, Google Pay, Paytm, BHIM).\n"
                    "Enter the exact fee amount shown on your enrollment confirmation.\n"
                    "Copy the 12-digit UPI transaction reference from your payment app.\n"
                    "Paste it in the field below and upload a screenshot of the payment confirmation."
                ),
                why_choose_us_json='[{"icon":"BookOpen","title":"Expert Faculty","description":"IIT/AIIMS alumni with 10+ years of teaching experience"},{"icon":"Target","title":"Result-Oriented","description":"95% of our students clear NEET/JEE on their first attempt"},{"icon":"Users","title":"Small Batch Size","description":"Maximum 40 students per batch for personalised attention"},{"icon":"Clock","title":"Flexible Schedule","description":"Morning and evening batches to suit every student"}]',
                faq_json='[{"question":"What is the fee structure?","answer":"The fee varies by batch and is displayed on the Courses page. All fees are collected via UPI and manually verified by our team."},{"question":"Can I pay in installments?","answer":"Yes, installment options are available. Please contact us directly to discuss your requirements."},{"question":"How do I track my enrollment status?","answer":"After submitting your enrollment form, use your reference number on the Enrollment Status page to check for updates."},{"question":"What documents do I need?","answer":"You need a 10th marksheet, recent passport-size photo, and Aadhaar card copy for the first class. No documents are required for online enrollment."}]',
            )
            session.add(settings)

        # Create a sample batch
        result = await session.execute(select(Batch).limit(1))
        batch = result.scalar_one_or_none()
        if not batch:
            batch = Batch(
                id=uuid.uuid4(),
                name="NEET 2027 Batch — Morning",
                exam_type=ExamType.NEET,
                academic_year="2026-27",
                description=(
                    "Comprehensive NEET preparation covering Physics, Chemistry, and Biology. "
                    "Classes are held six days a week with weekly tests and monthly mock exams."
                ),
                start_date=date(2027, 1, 6),
                end_date=date(2027, 11, 30),
                enrollment_start_date=date(2026, 11, 15),
                enrollment_end_date=date(2026, 12, 31),
                class_days=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
                class_start_time=time(7, 0),
                class_end_time=time(10, 0),
                subjects=["Physics", "Chemistry", "Biology"],
                syllabus=(
                    "Class XI & XII NCERT syllabus (Physics, Chemistry, Biology) as per NTA NEET pattern. "
                    "Weekly tests after each chapter. Full-length mock tests every month."
                ),
                eligibility="Students currently in Class XI or XII, or droppers preparing for NEET 2027.",
                fee_amount=28000,
                total_seats=40,
                status=BatchStatus.ENROLLMENT_OPEN,
                is_published=True,
            )
            session.add(batch)

        await session.commit()
        print("Seed complete.")
        print(f"  Batch: NEET 2027 Batch — Morning (status: enrollment_open, published: True)")
        print(f"  Admin: check .env for ADMIN_EMAIL / ADMIN_PASSWORD")


if __name__ == "__main__":
    asyncio.run(seed())

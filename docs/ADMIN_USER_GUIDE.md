# Admin User Guide — NEET/JEE Coaching Website

This guide explains how to operate the admin dashboard for day-to-day tasks:
changing fees, updating the schedule, verifying payments, and editing website content.
No code changes are required for any of these tasks.

---

## Logging in

1. Go to `https://your-domain.com/admin/login`
2. Enter your admin email and password (set in `.env` as `ADMIN_EMAIL` / `ADMIN_PASSWORD`)
3. You will be redirected to the Dashboard

---

## Dashboard

The Dashboard shows:
- **Total Enrollments** — all enrollment forms submitted
- **Confirmed** — students whose payment has been verified
- **Pending Payment** — enrolled but no payment submitted yet
- **Awaiting Verification** — payment submitted, needs your review

The amber alert box appears when payments need review. Click **Review Now** to go to the
Payment Reviews page.

---

## Managing Batches

Go to **Admin → Batches**.

### Create a new batch
1. Click **New Batch**
2. Enter batch name, exam type, academic year, and fee
3. Click **Create Batch** — the batch starts in **Draft** status (not visible to students)

### Edit batch details
1. Click **Edit** on a batch card to open the Batch Detail page
2. Update: name, dates, fee, seats, description, eligibility, class times
3. Click **Save Changes**
4. Toggle **Published** to `Yes` to make the batch visible on the website

### Change batch status
Use the **Change status…** dropdown on a batch card:

| From | Allowed transitions |
|---|---|
| Draft | → Upcoming, Archived |
| Upcoming | → Enrollment Open, Archived |
| Enrollment Open | → Running, Archived |
| Running | → Completed, Archived |
| Completed | → Archived |

**To open enrollment for a new batch**: set status to `Enrollment Open` and ensure the
`Enrollment Opens` and `Enrollment Closes` dates are set correctly.

### Change the fee

1. Open the Batch Detail page
2. Update **Fee Amount (₹)**
3. Click **Save Changes**

The new fee is immediately shown to students. It does NOT retroactively change any existing
enrollment's payment amount.

---

## Managing the Schedule

Inside a Batch Detail page, scroll to **Schedule Override**.

Use this to:
- Mark a class day as **Cancelled** (e.g., for a holiday)
- Add a notice (e.g., "Venue changed to Room 2")
- Note a subject for a specific day

Steps:
1. Pick the date
2. Enter subject (optional)
3. Set Status to `Cancelled` if needed
4. Add a Notice message
5. Click **Save Session Override**

Students see these overrides on the Schedule page of the website.

---

## Reviewing Payments

Go to **Admin → Payments**.

This page shows all payments submitted by students with status **submitted** (not yet reviewed).

### How to verify a payment (IMPORTANT)
1. Click **Review** on a payment submission
2. Note the **Transaction Reference** and **Amount Claimed**
3. **Open your bank or UPI app** (PhonePe, Google Pay, Paytm, or bank statement)
4. Search for the transaction reference in your received payments
5. Confirm the amount matches what was claimed

If payment is confirmed:
- Click **Verify Payment**
- Click **Confirm Decision**
- The student's enrollment automatically moves to **Confirmed**

If payment is not found or amount is wrong:
- Click **Reject**
- Enter a clear rejection reason (e.g., "Transaction reference not found in our UPI statement")
- Click **Confirm Decision**

**Never verify a payment based solely on the screenshot.** Screenshots can be edited.

The student's email shows their enrollment status. You can contact them via their submitted
email/phone to resolve payment disputes.

---

## Managing Students

Go to **Admin → Students**.

- Use the **search box** to find a student by name, email, or reference number
- Filter by **status** (pending payment / confirmed / cancelled)
- Click **Export CSV** to download the full enrollment list

Manual status overrides:
- **Confirm** button: appears on `pending_payment` enrollments — use only if payment was
  confirmed through the Payment Reviews page or via direct bank confirmation
- **Cancel** button: cancels a confirmed enrollment (e.g., student withdrew)

---

## Editing Website Content

Go to **Admin → Settings**.

### Institute tab
- Institute name, tagline, contact email/phone/address
- Logo upload (PNG or SVG, recommended 300×100 px)

### UPI / Payment tab
- **UPI ID** — your UPI address (e.g., `yourname@upi`)
- **UPI Account Name** — appears next to QR code
- **Payment Instructions** — step-by-step text shown to students
- **UPI QR Code** — upload a QR image exported from your UPI app (PNG, min 400×400 px)

### Website Content tab
- Hero section heading and subheading
- About section text
- Enrollment instructions (shown at top of enrollment form)
- JSON fields for "Why Choose Us", FAQs, and Faculty (see format below)

### Social & Links tab
- Facebook, Instagram, YouTube, Twitter URLs

Click **Save Changes** after editing any tab.

---

## JSON Content Format

### Why Choose Us (`why_choose_us_json`)
```json
[
  {
    "icon": "BookOpen",
    "title": "Expert Faculty",
    "description": "IIT/AIIMS alumni with 10+ years of teaching experience"
  }
]
```
Icon names come from [lucide.dev](https://lucide.dev).

### FAQs (`faq_json`)
```json
[
  {
    "question": "What is the fee?",
    "answer": "The fee is displayed on the Courses page and varies by batch."
  }
]
```

### Faculty (`faculty_json`)
```json
[
  {
    "name": "Dr. Anjali Singh",
    "qualification": "MBBS, MD — AIIMS Delhi",
    "subject": "Biology",
    "photo_url": "/uploads/public/faculty-anjali.jpg"
  }
]
```

---

## Changing the Admin Password

The admin password is set in the `.env` file as `ADMIN_PASSWORD`. To change it:
1. Update `ADMIN_PASSWORD` in `.env`
2. Restart the backend (`docker compose restart backend`)
3. The bootstrap script runs on startup — if no admin user exists it creates one,
   but if the admin already exists, the password is **not** reset automatically

To force a password reset, ask your developer to run:
```bash
docker compose exec backend python -m app.db.reset_admin_password
```
(This script is not included by default; your developer will need to create it.)

---

## Security Reminders

- Never share your admin login credentials
- After logging out, the JWT expires in 1 hour — sessions are not persistent
- Payment verification **must always** be backed by your actual bank statement
- The audit log records every payment decision — it cannot be edited or deleted

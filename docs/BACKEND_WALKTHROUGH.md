# Backend Execution Flow — NEET/JEE Coaching Website

This document traces the full life of two key requests end-to-end so you can see how all the
layers fit together: **student enrollment** and **admin payment verification**.

---

## Layer responsibilities (quick reminder)

| Layer | File location | Does what |
|---|---|---|
| **Route** | `app/api/routes/` | Parses HTTP, validates with Pydantic, calls service, returns response |
| **Service** | `app/services/` | Business logic, state machines, duplicate detection |
| **Repository** (implicit in services) | SQLAlchemy queries inside services | All DB reads/writes |
| **Model** | `app/models/` | SQLAlchemy ORM table definitions |
| **Schema** | `app/schemas/` | Pydantic request/response shapes |
| **Core** | `app/core/` | Config, security helpers, DI dependencies |

---

## Flow 1 — Student submits an enrollment form

```
Browser (React)
  → POST /api/enrollment/
  → enrollment.py route
  → EnrollmentService.create_enrollment()
  → DB INSERT enrollments
  → 201 JSON {reference, status: "pending_payment"}
```

### Step-by-step

**1. Request arrives at the route** (`app/api/routes/enrollment.py`)

```python
@router.post("/", status_code=201, response_model=EnrollmentResponse)
async def create_enrollment(data: EnrollmentCreate, db: AsyncSession = Depends(get_db_session)):
    return await EnrollmentService.create_enrollment(db, data)
```

FastAPI automatically:
- Parses the JSON body into `EnrollmentCreate` (a Pydantic model)
- Validates that `exam_preference` is `"neet"` or `"jee"`, `phone` has ≥10 digits, and
  `privacy_acknowledged` is literally `True` — if any check fails, FastAPI returns HTTP 422
- Injects an `AsyncSession` via `Depends(get_db_session)`

**2. Service enforces business rules** (`app/services/enrollment_service.py`)

```python
# 1. Batch must exist
batch = await BatchService.get_batch(db, data.batch_id)       # raises 404 if missing
# 2. Batch must be published and in enrollment_open status
if not batch.is_published or batch.status != BatchStatus.ENROLLMENT_OPEN:
    raise HTTPException(400, "Enrollment is not open for this batch")
# 3. Enrollment window dates
if batch.enrollment_start_date > today or batch.enrollment_end_date < today:
    raise HTTPException(400, "Enrollment window has closed")
# 4. Seat capacity
confirmed = await BatchService.get_confirmed_enrollment_count(db, batch.id)
if batch.total_seats and confirmed >= batch.total_seats:
    raise HTTPException(400, "Batch is full")
# 5. Generate reference  NJ-2026-0042
reference = _generate_reference(sequence, year)
# 6. INSERT
enrollment = Enrollment(... status="pending_payment" ...)
db.add(enrollment)
await db.commit()          # ← raises IntegrityError if (email, batch_id) already exists
```

**3. Duplicate detection**

The `enrollments` table has a **database-level** UNIQUE constraint on `(email, batch_id)`.
If a student tries to enroll twice, `db.commit()` raises `IntegrityError`, which the service
catches and converts to `HTTP 409 Conflict`. This is atomic — no race condition.

**4. Response**

The route returns `EnrollmentResponse` (Pydantic) with the `reference` number.
The frontend shows this reference and directs the student to `/payment?ref=...`.

---

## Flow 2 — Student submits a payment receipt

```
Browser (React)
  → POST /api/enrollment/payment  (multipart/form-data)
  → enrollment.py route
  → PaymentService.submit_payment()
  → DB INSERT payment_submissions  (status = "submitted")
  → Enrollment status UNCHANGED (still "pending_payment")
  → 201 JSON
```

### Why the enrollment stays "pending_payment"

This is a **critical security rule** — the enrollment can only move to `"confirmed"` through
admin action (see Flow 3). A student submitting a screenshot proves nothing; the admin must
check the actual bank statement.

```python
# PaymentService.submit_payment() — simplified
submission = PaymentSubmission(
    enrollment_id=enrollment.id,
    transaction_ref=data.transaction_ref.strip(),
    status=PaymentStatus.SUBMITTED,
    # ...
)
db.add(submission)
# Enrollment.status is NOT touched here
await db.commit()
```

---

## Flow 3 — Admin verifies a payment

```
Admin browser
  → POST /api/admin/payments/{id}/review  (requires JWT + role=admin)
  → admin.py route
  → Depends(require_admin) checks JWT
  → PaymentService.verify_payment()
  → DB UPDATE payment_submissions.status = "verified"
  → DB UPDATE enrollments.status = "confirmed"
  → DB INSERT audit_logs
  → 200 JSON
```

### Dependency chain: require_admin

```python
# app/core/dependencies.py
async def get_current_user(token = Depends(bearer), db = Depends(get_db_session)):
    payload = decode_access_token(token.credentials)   # raises JWTError → 401
    user = await db.get(User, payload["sub"])
    if not user or not user.is_active: raise HTTPException(401)
    return user

async def require_admin(user = Depends(get_current_user)):
    if user.role != "admin": raise HTTPException(403, "Admin only")
    return user
```

Every admin route declares `Depends(require_admin)`. FastAPI evaluates this on **every request**
— there is no caching or session bypass.

### Service — state machine

```python
async def verify_payment(db, submission_id, action, admin, rejection_reason):
    submission = await db.get(PaymentSubmission, submission_id)
    # Idempotency guard
    if submission.status != PaymentStatus.SUBMITTED:
        raise HTTPException(400, "Payment already reviewed")

    if action == "verify":
        submission.status = PaymentStatus.VERIFIED
        submission.enrollment.status = EnrollmentStatus.CONFIRMED
    elif action == "reject":
        if not rejection_reason:
            raise HTTPException(422, "rejection_reason required")
        submission.status = PaymentStatus.REJECTED

    submission.reviewed_by_id = admin.id
    submission.reviewed_at = datetime.utcnow()

    # Immutable audit record
    db.add(AuditLog(
        actor_id=admin.id,
        actor_email=admin.email,
        action=f"payment_{action}",
        target_type="payment_submission",
        target_id=str(submission_id),
        details=json.dumps({"rejection_reason": rejection_reason}),
    ))
    await db.commit()
```

The `AuditLog` table is **insert-only** — no UPDATE or DELETE is ever run on it.
This creates an immutable record of every admin payment decision.

---

## Database session lifecycle

```
get_db_session() yields session
  route handler runs
    service does db.add(...) / await db.execute(...)
    service calls await db.commit()   ← flushes + commits
  if any exception:
    get_db_session rollbacks automatically
  finally: session.close()
```

`expire_on_commit=False` means ORM objects remain usable after commit without an extra SELECT.

---

## JWT authentication flow

1. Admin POSTs credentials to `POST /api/auth/login`
2. `AuthService.authenticate()` verifies bcrypt hash — always runs `verify_password` even if
   user not found (prevents timing attacks)
3. Returns JWT: `{sub: user_id, role: "admin", exp: now+3600}`
4. Frontend stores JWT in `localStorage["admin_token"]`
5. Axios interceptor injects `Authorization: Bearer <token>` on every request
6. `get_current_user` dependency decodes and verifies the JWT server-side on every request

---

## Key concepts to explore further

- **FastAPI Depends()** — `fastapi.tiangolo.com/tutorial/dependencies/`
- **SQLAlchemy 2.x async** — `docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html`
- **Alembic** — `alembic.sqlalchemy.org/en/latest/tutorial.html`
- **Pydantic v2 validators** — `docs.pydantic.dev/latest/concepts/validators/`
- **bcrypt timing-safe comparisons** — `passlib.readthedocs.io/en/stable/lib/passlib.hash.bcrypt.html`
- **JWT (python-jose)** — `python-jose.readthedocs.io/en/latest/`

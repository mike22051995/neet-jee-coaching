# NEET/JEE Coaching Website — Project Guide for Claude Code

## Project Overview
A full-stack online coaching website for NEET and JEE exam preparation. Built with:
- **Backend**: Python 3 · FastAPI · PostgreSQL · SQLAlchemy 2.x · Alembic · Pydantic · JWT auth
- **Frontend**: React 18 · TypeScript · Tailwind CSS · React Query · React Router v6
- **Dev environment**: Docker Compose (postgres + backend + frontend + nginx)

## Architecture Decisions

### Backend
- **Modular monolith** — single FastAPI app, feature-grouped routers (not microservices)
- **Layered architecture**: routes → services → repositories → models
  - Routes: validate input, call service, return response (no business logic here)
  - Services: enforce business rules, state transitions, duplicate detection
  - Repositories: all database queries (SQLAlchemy sessions never leak into routes)
- **Dependency injection** via FastAPI `Depends()` for DB sessions, current-user, settings
- **SQLAlchemy 2.x async** with `AsyncSession` for all DB operations
- **Alembic** for all schema changes — never alter tables manually
- **Pydantic v2** for request/response validation and settings management

### Database
- Primary key: UUID (uuid4) on all tables — never sequential int PKs
- Soft-delete pattern for enrollments (`deleted_at` column, never hard-delete)
- Optimistic locking via `version` column on `enrollments` and `payment_submissions`
- Timezone: all datetimes stored as UTC, displayed as Asia/Kolkata (IST) in UI

### Frontend
- **React Query** (`@tanstack/react-query`) for all API calls — no raw axios in components
- **React Router v6** with file-based route organization under `src/pages/`
- Admin routes wrapped in `<ProtectedRoute>` — redirect to `/admin/login` if no JWT
- **Tailwind CSS** — no inline styles; use utility classes; design tokens in `tailwind.config.js`
- Forms: React Hook Form + Zod validation

### Security
- Passwords: bcrypt (never store plain-text, never log)
- JWT: HS256, 1-hour access tokens, stored in `httpOnly` cookies (not localStorage)
- Admin endpoints: require `role=admin` claim in JWT — checked server-side on every request
- Payment verification: **only** admins can transition payment status to `verified`
- File uploads: validated MIME type + size limit (5 MB), stored outside web root
- Rate limiting: on login endpoint (5 attempts / 15 min per IP) using slowapi

## Coding Conventions

### Python / FastAPI
- Type hints on every function signature
- Use `async def` for all route handlers and service methods
- Error responses: raise `HTTPException` with appropriate status codes
- Never put business logic in Pydantic schemas
- Module docstrings explain "why" and "which layer" — not "what"
- Keep route handlers under ~20 lines; extract logic to services
- Use `logging.getLogger(__name__)` — never `print()`

### TypeScript / React
- Strict TypeScript (`"strict": true` in tsconfig)
- Component files: PascalCase (`EnrollmentForm.tsx`)
- Hooks: `use` prefix (`useEnrollment.ts`)
- API types auto-generated from OpenAPI spec (run `npm run generate-types`)
- No `any` types — use `unknown` and narrow
- Prefer named exports over default exports

## Testing
- **Backend**: pytest + pytest-asyncio + httpx AsyncClient
  - Each feature gets tests in `backend/app/tests/test_<feature>.py`
  - Use test database (separate `TEST_DATABASE_URL` in `.env.test`)
  - Fixtures: async DB session, authenticated admin client, sample batch
- **Frontend**: Vitest + React Testing Library
  - Test important user flows, not implementation details
  - Mock API calls with MSW (Mock Service Worker)
- **E2E**: Playwright covering enrollment → payment submission flow

## Run Tests
```bash
# Backend
cd backend && pytest -v

# Frontend unit
cd frontend && npm test

# E2E
cd frontend && npx playwright test
```

## Important Requirements — Never Break
1. A student submitting a UPI transaction reference **must never** auto-confirm payment
2. Payment verification **requires** admin action — always server-side check
3. Never expose one student's data to another student
4. Admin routes must check JWT + admin role on **every** request (no frontend-only guards)
5. Duplicate enrollment detection must be atomic (use DB unique constraint)
6. All business-configurable data (fees, UPI ID, batch dates) lives in DB, never in source code

## Educational Documentation
Since the owner is learning backend engineering, all significant backend files must include:
- Module-level docstring explaining the layer's responsibility
- Method docstrings explaining what, why, and which concepts are used
- Inline comments for non-obvious decisions (state machine transitions, locking, etc.)
See `docs/BACKEND_WALKTHROUGH.md` for complete execution flow documentation.

## Progress Checklist
- [x] Project directory structure created
- [x] CLAUDE.md written
- [x] Docker Compose configured
- [x] Backend: environment config
- [x] Backend: database models
- [x] Backend: Alembic migrations
- [x] Backend: auth service (JWT + bcrypt)
- [x] Backend: batch service + API
- [x] Backend: enrollment service + API
- [x] Backend: payment service + API
- [x] Backend: site settings service + API
- [x] Backend: schedule service + API
- [x] Backend: admin dashboard API
- [x] Backend: tests written
- [x] Frontend: Tailwind + project setup
- [x] Frontend: layout components (Header, Footer, Nav)
- [x] Frontend: Home page
- [x] Frontend: Courses / Batch page
- [x] Frontend: Schedule page
- [x] Frontend: Enrollment form
- [x] Frontend: Payment page (UPI QR + reference submit)
- [x] Frontend: Admin login
- [x] Frontend: Admin dashboard overview
- [x] Frontend: Admin batch management
- [x] Frontend: Admin student management
- [x] Frontend: Admin payment review
- [x] Frontend: Admin site settings
- [x] Docs: BACKEND_WALKTHROUGH.md
- [x] Docs: ADMIN_USER_GUIDE.md
- [x] Docs: DEVELOPER_GUIDE.md
- [x] Seed data + admin bootstrap
- [ ] E2E test passing (Playwright — run after `docker compose up`)

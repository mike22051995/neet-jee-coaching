# Developer Guide — NEET/JEE Coaching Website

## Prerequisites

- Docker Desktop (with Compose v2)
- Node.js 20+ (for running frontend outside Docker)
- Python 3.11+ (for running backend outside Docker)
- Git

---

## Quick Start (Docker — recommended)

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd Neet-Jee-coaching

# 2. Copy and edit environment variables
cp .env.example .env
# Edit .env — set SECRET_KEY, ADMIN_EMAIL, ADMIN_PASSWORD

# 3. Start all services
docker compose up --build

# 4. Seed sample data (first run only)
docker compose exec backend python -m app.db.seed
```

The app is now available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Admin panel: http://localhost:3000/admin/login

---

## Project Structure

```
Neet-Jee-coaching/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # HTTP route handlers (thin — business logic lives in services)
│   │   ├── core/            # Config, JWT helpers, DI dependencies
│   │   ├── db/              # Engine, session factory, seed
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # Business logic layer
│   │   ├── tests/           # pytest test suite
│   │   └── main.py          # FastAPI app factory + lifespan
│   ├── alembic/             # Database migrations
│   │   └── versions/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # Reusable UI (layout, admin shell, common)
│   │   ├── hooks/           # React Query hooks + auth
│   │   ├── pages/           # Route-level page components
│   │   │   ├── public/      # Student-facing pages
│   │   │   └── admin/       # Admin-only pages
│   │   ├── services/        # Axios API client + TypeScript types
│   │   └── styles/          # Tailwind CSS + component utility classes
│   ├── index.html
│   ├── tailwind.config.js
│   └── vite.config.ts
├── docs/                    # Documentation
├── docker-compose.yml
└── .env.example
```

---

## Running without Docker

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp ../.env.example .env
# Edit .env — set DATABASE_URL to your local PostgreSQL

# Run migrations
alembic upgrade head

# Seed data
python -m app.db.seed

# Start dev server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev    # starts at http://localhost:5173
```

The Vite dev server proxies `/api` to `http://localhost:8000` via `vite.config.ts`.

---

## Running Tests

```bash
# Backend (requires test DB — set TEST_DATABASE_URL in .env.test)
cd backend
pytest -v

# Frontend unit tests
cd frontend
npm test

# E2E tests (requires both servers running)
cd frontend
npx playwright test
```

---

## Adding a New Feature

Follow the layered architecture:

### 1. Add a database model (`app/models/`)

```python
# app/models/announcement.py
class Announcement(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "announcements"
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
```

### 2. Create an Alembic migration

```bash
cd backend
alembic revision --autogenerate -m "add announcements table"
# Review the generated file in alembic/versions/
alembic upgrade head
```

### 3. Add Pydantic schemas (`app/schemas/`)

```python
class AnnouncementCreate(BaseModel):
    title: str
    body: str

class AnnouncementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    body: str
    is_published: bool
    created_at: datetime
```

### 4. Add a service (`app/services/`)

```python
class AnnouncementService:
    @staticmethod
    async def list_published(db: AsyncSession) -> list[Announcement]:
        result = await db.execute(
            select(Announcement)
            .where(Announcement.is_published == True)
            .order_by(Announcement.created_at.desc())
        )
        return result.scalars().all()
```

### 5. Add routes (`app/api/routes/`)

```python
router = APIRouter(prefix="/api/announcements", tags=["announcements"])

@router.get("/", response_model=list[AnnouncementResponse])
async def list_announcements(db: AsyncSession = Depends(get_db_session)):
    return await AnnouncementService.list_published(db)
```

### 6. Register the router (`app/main.py`)

```python
from app.api.routes.announcements import router as announcements_router
app.include_router(announcements_router)
```

### 7. Add a React Query hook (`frontend/src/hooks/`)

```typescript
export function useAnnouncements() {
  return useQuery({
    queryKey: ['announcements'],
    queryFn: () => publicApi.getAnnouncements(),
  })
}
```

### 8. Write tests

```python
# backend/app/tests/test_announcements.py
async def test_list_announcements(client, db_session):
    # create test data, hit GET /api/announcements/, assert response
    ...
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL async URL: `postgresql+asyncpg://user:pass@host/db` |
| `SECRET_KEY` | Yes | Random 32+ char string for JWT signing |
| `ADMIN_EMAIL` | Yes | Bootstrap admin email |
| `ADMIN_PASSWORD` | Yes | Bootstrap admin password (bcrypt-hashed on first run) |
| `UPLOAD_DIR` | No | Defaults to `/app/uploads` |
| `MAX_UPLOAD_SIZE_MB` | No | Defaults to 5 |
| `ALLOWED_ORIGINS` | No | Comma-separated CORS origins |
| `TEST_DATABASE_URL` | Test only | Separate database for pytest |

---

## Deployment Notes

- Run `alembic upgrade head` before starting the backend (done automatically in Docker)
- The backend serves `/uploads/public/` as static files (logos, QR codes)
- Payment receipt uploads are stored in `/uploads/private/` and are **not** served statically
- Set `ENVIRONMENT=production` to disable debug output
- Use a secrets manager (e.g., AWS Secrets Manager) for `SECRET_KEY` and DB credentials in production
- Set up PostgreSQL backups — the `audit_logs` table is immutable and legally significant

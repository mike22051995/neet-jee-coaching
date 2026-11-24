# NEET/JEE Coaching Website

Full-stack online coaching platform for NEET and JEE exam preparation.

**Stack:** FastAPI · PostgreSQL · React 18 · TypeScript · Tailwind CSS · Docker Compose

---

## Quick Start

```bash
# 1. Copy environment variables
cp .env.example .env
```

Edit `.env` and set at minimum:
- `SECRET_KEY` — a random 32+ character string
- `ADMIN_EMAIL` — your admin login email
- `ADMIN_PASSWORD` — your admin login password

```bash
# 2. Start all services
docker compose up --build

# 3. Seed sample batch and site settings (first run only)
docker compose exec backend python -m app.db.seed
```

The site is now running:
| URL | What |
|---|---|
| http://localhost:3000 | Student-facing website |
| http://localhost:3000/admin | Admin dashboard |
| http://localhost:8000/docs | API documentation (Swagger UI) |

---

## Admin Bootstrap

The first admin account is created automatically from `.env` on backend startup.
Log in at http://localhost:3000/admin/login with `ADMIN_EMAIL` / `ADMIN_PASSWORD`.

---

## Running Tests

```bash
# Backend tests
docker compose exec backend pytest -v

# Frontend unit tests
docker compose exec frontend npm test
```

---

## Documentation

| Document | Description |
|---|---|
| [docs/BACKEND_WALKTHROUGH.md](docs/BACKEND_WALKTHROUGH.md) | Execution flow — enrollment, payment, JWT auth |
| [docs/ADMIN_USER_GUIDE.md](docs/ADMIN_USER_GUIDE.md) | How to use the admin dashboard |
| [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) | Setup, project structure, adding features |
| [CLAUDE.md](CLAUDE.md) | Architecture decisions and coding conventions |

---

## Security

- Student UPI submissions **never** auto-confirm payment — admin review is required
- Payment verification decisions are logged in an immutable audit table
- Passwords are bcrypt-hashed; JWTs use HS256 with 1-hour expiry
- Payment receipts are stored outside the web root (not publicly accessible)
- Admin endpoints check JWT + `role=admin` on every request server-side

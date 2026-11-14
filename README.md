# InvoiceFlow

> Lets freelancers create, send, and track invoices in under a minute.

The MVP is built one module at a time following [`PRPs/invoiceflow-mvp-plan.md`](PRPs/invoiceflow-mvp-plan.md).
The long-term SaaS specification is [`PRPs/invoiceflow-prp.md`](PRPs/invoiceflow-prp.md).

## Prerequisites

- Docker Desktop (runs PostgreSQL 16)
- Python 3.11+
- Node.js 24 LTS + npm

## Setup

```bash
# 1. Database (creates `invoiceflow` and `invoiceflow_test`)
docker compose up -d

# 2. Backend
cd backend
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
copy ..\.env.example .env         # macOS/Linux: cp ../.env.example .env
#    then set SECRET_KEY in backend/.env:
#    python -c "import secrets; print(secrets.token_urlsafe(48))"
alembic upgrade head
uvicorn app.main:app --reload     # http://localhost:8000/health, /docs

# 3. Frontend (new terminal)
cd frontend
npm install
copy .env.example .env            # macOS/Linux: cp .env.example .env
npm run dev                       # http://localhost:5173
```

## Checks

```bash
# Backend (from backend/, venv active)
ruff check . && ruff format --check . && mypy
pytest --cov=app                  # uses TEST_DATABASE_URL, never the dev database

# Frontend (from frontend/)
npm run lint && npm run type-check && npm test && npm run build
```

---

# MicroSaaS Template

> **Clone. Define. Build.** Full-stack SaaS in minutes.

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/manojkanur/MicroSaaS-Template-Private.git my-saas
cd my-saas

# 2. Define your product
# Edit INITIAL.md with your product details

# 3. Generate blueprint
/generate-prp INITIAL.md

# 4. Build with parallel agents
/execute-prp PRPs/[name]-prp.md
```

---

## What You Get

- FastAPI backend with JWT + Google OAuth
- React frontend with modern UI (Framer Motion)
- PostgreSQL database with migrations
- Docker + CI/CD ready
- 80%+ test coverage

---

## How It Works

```
INITIAL.md → /generate-prp → PRP blueprint → /execute-prp → Full App

Phase 1 (Parallel):
├─ DATABASE-AGENT  → Models + migrations
├─ BACKEND-AGENT   → API structure
├─ FRONTEND-AGENT  → React setup
└─ DEVOPS-AGENT    → Docker + CI

Phase 2 (Per Module):
├─ Backend endpoints
└─ Frontend pages

Phase 3 (Parallel):
├─ TEST-AGENT      → 80%+ coverage
└─ REVIEW-AGENT    → Security audit
```

---

## Files

| File | Purpose |
|------|---------|
| `INITIAL.md` | Define your product |
| `CLAUDE.md` | Project rules |
| `skills/*.md` | Code patterns (5 files) |
| `agents/*.md` | Agent definitions |
| `.claude/commands/` | Custom commands |

---

## Skills (5 files)

| Skill | Contains |
|-------|----------|
| `BACKEND.md` | FastAPI + JWT + OAuth + Errors |
| `FRONTEND.md` | React + UI Kit + API integration |
| `DATABASE.md` | SQLAlchemy + Alembic |
| `TESTING.md` | pytest + Vitest |
| `DEPLOYMENT.md` | Docker + GitHub Actions |

---

## Commands

| Command | Description |
|---------|-------------|
| `/setup-project` | Interactive wizard |
| `/generate-prp` | Create implementation blueprint |
| `/execute-prp` | Build with parallel agents |

---

## Tech Stack

- **Backend:** FastAPI + Python 3.11+
- **Frontend:** React + TypeScript + Vite
- **Database:** PostgreSQL + SQLAlchemy
- **Auth:** JWT + Google OAuth
- **UI:** Chakra UI or Tailwind + Framer Motion
- **Deploy:** Docker + GitHub Actions

---

## Example

```bash
# Define an invoice SaaS in INITIAL.md:
# - Module: Invoices (CRUD)
# - Module: Clients (CRUD)
# - Module: Dashboard

/generate-prp INITIAL.md
# Creates PRPs/invoice-saas-prp.md

/execute-prp PRPs/invoice-saas-prp.md
# 4 agents build in parallel
# ~20-30 minutes for complete app
```

---

## Output Structure

```
my-saas/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models/
│   │   ├── routers/
│   │   ├── services/
│   │   └── auth/
│   ├── alembic/
│   └── tests/
├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── hooks/
│       └── services/
├── docker-compose.yml
└── .github/workflows/
```

---

## Run Locally

```bash
# Backend
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Docker
docker-compose up -d
```

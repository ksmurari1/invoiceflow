# CLAUDE.md - InvoiceFlow Project Rules

> Project-specific rules for Claude Code. This file is read automatically.

---

## Project Overview

**Project Name:** InvoiceFlow
**Description:** Lets freelancers create, send, and track invoices in under a minute.
**Target User:** Freelancers and small agencies who bill clients monthly.
**Tech Stack:**
- Backend: FastAPI + Python 3.11+
- Frontend: React + Vite + TypeScript
- Database: PostgreSQL + SQLAlchemy + Alembic
- Auth: Email/Password + Google OAuth (JWT)
- UI: Tailwind CSS + shadcn/ui (+ Framer Motion)
- Payments: none (payments are recorded manually)

---

## Project Structure

```
invoiceflow/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── refresh_token.py
│   │   │   ├── client.py
│   │   │   ├── invoice.py          # Invoice + InvoiceItem
│   │   │   ├── payment.py
│   │   │   └── attachment.py
│   │   ├── schemas/
│   │   ├── routers/                # auth, clients, invoices, payments, dashboard, admin, uploads
│   │   ├── services/               # invoice_calc, pdf, email, storage, numbering
│   │   ├── templates/              # invoice PDF + email HTML templates
│   │   └── auth/
│   ├── alembic/
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── ui/                 # shadcn/ui generated components
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── context/
│   │   ├── lib/                    # utils (cn, money formatting)
│   │   └── types/
│   └── package.json
├── .claude/
│   └── commands/                   # /setup-project, /generate-prp, /execute-prp
├── skills/
├── agents/
└── PRPs/
```

---

## Code Standards

### Python (Backend)
```python
# ALWAYS use type hints
def get_invoice(db: Session, invoice_id: int, user_id: int) -> Invoice:
    pass

# ALWAYS add docstrings for public functions
def create_invoice(db: Session, user_id: int, data: InvoiceCreate) -> Invoice:
    """
    Create a new draft invoice with line items.

    Args:
        db: Database session
        user_id: Owner of the invoice
        data: Invoice creation data (client, items, tax, due date)

    Returns:
        Created Invoice object with computed totals
    """
    pass

# Async endpoints
@router.get("/invoices/{id}")
async def read_invoice(id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    pass
```

### TypeScript (Frontend)
```typescript
// ALWAYS define interfaces for props and data
type InvoiceStatus = "draft" | "sent" | "paid" | "overdue" | "void";

interface InvoiceItem {
  id: number;
  description: string;
  quantity: string;   // decimal strings from API
  unitPrice: string;
  amount: string;
}

interface Invoice {
  id: number;
  invoiceNumber: string;
  clientId: number;
  status: InvoiceStatus;
  issueDate: string;
  dueDate: string;
  currency: string;
  subtotal: string;
  taxRate: string;
  taxAmount: string;
  total: string;
  amountPaid: string;
  items: InvoiceItem[];
}

// NO any types allowed
const fetchInvoice = async (id: number): Promise<Invoice> => {
  // ...
};
```

---

## Forbidden Patterns

### Backend
- ❌ Never use `print()`. Use the `logging` module.
- ❌ Never store passwords in plain text. Use bcrypt.
- ❌ Never hardcode secrets. Use environment variables.
- ❌ Never use `SELECT *`. Specify columns.
- ❌ Never skip input validation.
- ❌ Never use `float` for money. Use `Decimal` / `Numeric(12, 2)`.
- ❌ Never query user-owned data without filtering by `user_id`.

### Frontend
- ❌ Never use the `any` type.
- ❌ Never leave console.log in production.
- ❌ Never skip error handling in async operations.
- ❌ Never use inline styles. Use Tailwind classes and shadcn/ui components.
- ❌ Never do money math with JS floats. The server is the source of truth for totals; the client only previews them.

---

## Module-Specific Rules

### Clients Module
- Every client belongs to a user (`user_id` foreign key); cross-user access returns 404.
- Client email must be a valid email address.
- A client with non-draft invoices cannot be deleted.

### Invoices Module
- Every invoice belongs to a user and to one of that user's clients.
- Status must be one of: `draft`, `sent`, `paid`, `overdue`, `void`.
- Allowed transitions: draft → sent → paid; sent → overdue (automatic, past due_date and unpaid); overdue → paid; any non-paid → void.
- Only `draft` invoices can be edited or deleted; others can only be voided.
- `invoice_number` is sequential and unique per user (e.g. `INV-0001`). Generate it in a transaction.
- Subtotal, tax, discount, and total are always computed server-side and rounded with ROUND_HALF_UP to 2 decimals.
- An invoice needs at least one line item; quantity must be > 0 and unit_price ≥ 0.
- `due_date` must be on or after `issue_date`.
- PDF output must escape all user-supplied text.

### Payments Module
- Payments are manual records. No card processing.
- The sum of payments cannot exceed the invoice total.
- Recording or deleting a payment recalculates `amount_paid` and status (paid when fully covered).

### File Uploads
- Logos: PNG/JPG/SVG, max 2 MB. Attachments: max 10 MB.
- Validate MIME type and store under randomized keys; never trust client filenames for paths.

### Admin
- Admin endpoints require `is_admin = true` (403 otherwise).

---

## API Conventions

- All endpoints are prefixed with `/api/v1/`.
- Use plural nouns for resources: `/invoices`, `/clients`, `/payments`.
- Actions on a resource use sub-paths: `/invoices/{id}/send`, `/invoices/{id}/pdf`.
- Money is serialized as decimal strings (e.g. `"1250.00"`).
- Return appropriate HTTP status codes:
  - 200: Success
  - 201: Created
  - 400: Bad Request
  - 401: Unauthorized
  - 403: Forbidden
  - 404: Not Found
  - 409: Conflict (e.g. editing a non-draft invoice)
  - 422: Validation Error

---

## Authentication

Email/password plus Google OAuth.

### JWT Configuration
- Access token expires: 30 minutes
- Refresh token expires: 7 days (stored in DB, revocable)
- Algorithm: HS256

### OAuth Providers
- Google OAuth 2.0 enabled
- Always verify the state parameter for CSRF protection
- Link Google accounts to existing users by verified email

---

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/invoiceflow

# Auth
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback

# Email
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=xxx
SMTP_PASSWORD=xxx
EMAIL_FROM=invoices@yourdomain.com

# File storage
STORAGE_BACKEND=local            # local | s3
UPLOAD_DIR=./uploads
S3_BUCKET=
S3_ENDPOINT_URL=
S3_ACCESS_KEY_ID=
S3_SECRET_ACCESS_KEY=

# Frontend
FRONTEND_URL=http://localhost:5173
VITE_API_URL=http://localhost:8000
```

---

## Development Commands

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

# Tests
pytest backend/tests -v
cd frontend && npm test

# Linting / validation
ruff check backend/ && pytest
cd frontend && npm run lint && npm run type-check
docker-compose build
```

---

## Commit Message Format

```
feat([module]): add [feature]
fix([module]): fix [bug]
refactor([module]): refactor [component]
test([module]): add tests for [feature]
docs: update [documentation]
```

Modules: `auth`, `clients`, `invoices`, `payments`, `dashboard`, `admin`, `email`, `uploads`.

---

## Skills Reference

| Task | Skill to Read |
|------|---------------|
| Database models | skills/DATABASE.md |
| API + Auth | skills/BACKEND.md |
| React + UI | skills/FRONTEND.md |
| Testing | skills/TESTING.md |
| Deployment | skills/DEPLOYMENT.md |

> Note: skills/FRONTEND.md may reference Chakra UI. This project uses **Tailwind + shadcn/ui** instead.

---

## Agent Coordination

For complex tasks, the ORCHESTRATOR coordinates:
- DATABASE-AGENT → Backend models
- BACKEND-AGENT → API development
- FRONTEND-AGENT → UI components
- TEST-AGENT → Testing
- REVIEW-AGENT → Code review
- DEVOPS-AGENT → Deployment

Read agent definitions in the `/agents/` folder.

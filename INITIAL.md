# INITIAL.md - InvoiceFlow Product Definition

> Lets freelancers create, send, and track invoices in under a minute.

---

## PRODUCT

### Name
InvoiceFlow

### Description
InvoiceFlow is a lightweight invoicing tool for freelancers and small agencies. Users keep a list of
their clients and create professional invoices with line items, tax, and a due date, then download
them as PDFs. Later versions add emailing invoices, tracking status (draft → sent → paid / overdue),
recording payments, and a dashboard with outstanding and paid totals.

### Target User
Freelancers and small agencies who bill clients monthly.

### Type
- [x] SaaS (Software as a Service)

---

## TECH STACK

### Backend
- [x] FastAPI + Python 3.11+

### Frontend
- [x] React + Vite + TypeScript

### Database
- [x] PostgreSQL + SQLAlchemy + Alembic

### Authentication
- [x] Email/Password + Google OAuth (JWT access + refresh tokens)

### UI Framework
- [x] Tailwind CSS + shadcn/ui (+ Framer Motion for animation)

### Payments
- [ ] None (no payment provider for now; payments are recorded manually)

---

## MODULES

### Module 1: Authentication (Required)

**Description:** User authentication and authorization.

**Models:**
- User: id, email, hashed_password (nullable for OAuth-only users), full_name, business_name, business_address, logo_url, default_currency, is_active, is_verified, is_admin, oauth_provider, oauth_id, created_at, updated_at
- RefreshToken: id, user_id, token, expires_at, revoked, created_at

**API Endpoints:**
- POST /api/v1/auth/register - Create new account
- POST /api/v1/auth/login - Login with email/password
- POST /api/v1/auth/refresh - Refresh access token
- POST /api/v1/auth/logout - Revoke refresh token
- GET /api/v1/auth/me - Get current user profile
- PUT /api/v1/auth/me - Update profile (incl. business details used on invoices)
- GET /api/v1/auth/google/login - Start Google OAuth flow
- GET /api/v1/auth/google/callback - Google OAuth callback
- POST /api/v1/auth/forgot-password - Send password reset email
- POST /api/v1/auth/reset-password - Reset password with token

**Frontend Pages:**
- /login - Login page (email/password + "Continue with Google")
- /register - Registration page
- /forgot-password - Forgot password page
- /reset-password - Reset password page
- /profile - User profile and business details (protected)

---

### Module 2: Clients

**Description:** Manage the people and companies the user bills.

**Models:**
- Client: id, user_id (FK), name, email, company, address, tax_id, default_currency (ISO 4217, e.g. "USD"), notes, created_at, updated_at

**API Endpoints:**
- GET /api/v1/clients - List clients (search, pagination)
- POST /api/v1/clients - Create client
- GET /api/v1/clients/{id} - Get client (with invoice summary)
- PUT /api/v1/clients/{id} - Update client
- DELETE /api/v1/clients/{id} - Delete client (blocked if the client has non-draft invoices)

**Frontend Pages:**
- /clients - Client list with search
- /clients/new - Create client form
- /clients/{id} - Client detail (info + their invoices)
- /clients/{id}/edit - Edit client form

---

### Module 3: Invoices

**Description:** Create, edit, send, and track invoices, and download them as PDFs.

**Models:**
- Invoice: id, user_id (FK), client_id (FK), invoice_number (unique per user, e.g. INV-0001), status (draft | sent | paid | overdue | void), issue_date, due_date, currency, subtotal, tax_rate, tax_amount, discount_amount, total, amount_paid, notes, terms, sent_at, paid_at, created_at, updated_at
- InvoiceItem: id, invoice_id (FK), description, quantity, unit_price, amount, position

> All money values use `Numeric(12, 2)`, never float. Totals are computed server-side.

**API Endpoints:**
- GET /api/v1/invoices - List invoices (filter by status, client, date range; pagination)
- POST /api/v1/invoices - Create invoice with line items (status = draft)
- GET /api/v1/invoices/{id} - Get invoice with items
- PUT /api/v1/invoices/{id} - Update invoice and items (draft only)
- DELETE /api/v1/invoices/{id} - Delete invoice (draft only; otherwise void)
- GET /api/v1/invoices/{id}/pdf - Download invoice PDF
- POST /api/v1/invoices/{id}/send - Email the invoice (PDF attached) to the client; status → sent
- POST /api/v1/invoices/{id}/mark-paid - Mark as paid
- POST /api/v1/invoices/{id}/void - Void the invoice

**Frontend Pages:**
- /invoices - Invoice list with status filters
- /invoices/new - Create invoice form (client picker, dynamic line items, tax, discount, due date, live totals)
- /invoices/{id} - Invoice detail / preview with actions (Download PDF, Send, Mark paid, Void)
- /invoices/{id}/edit - Edit draft invoice

---

### Module 4: Payments

**Description:** Record full or partial payments made against an invoice. No payment processing; this is manual bookkeeping.

**Models:**
- Payment: id, invoice_id (FK), user_id (FK), amount, method (bank_transfer | card | cash | check | paypal | other), paid_on, reference, notes, created_at

**API Endpoints:**
- GET /api/v1/invoices/{id}/payments - List payments for an invoice
- POST /api/v1/invoices/{id}/payments - Record payment (updates invoice.amount_paid; status → paid when fully paid)
- DELETE /api/v1/payments/{id} - Delete payment (recalculates invoice balance/status)

**Frontend Pages:**
- Payments panel on /invoices/{id} (list + "Record payment" dialog)

---

### Module 5: Dashboard & Analytics

**Description:** Overview of the user's invoicing health.

**API Endpoints:**
- GET /api/v1/dashboard/summary - Outstanding total, paid total (this month / all time), overdue count & amount, draft count
- GET /api/v1/dashboard/revenue?months=12 - Paid revenue by month
- GET /api/v1/dashboard/overdue - List of overdue invoices

**Frontend Pages:**
- /dashboard - Stat cards, revenue-by-month chart, overdue invoices list, recent invoices
- /settings - User settings (business details, logo, invoice numbering prefix, default terms, default tax rate)

---

### Module 6: Admin Panel

**Description:** Admin-only management interface.

**API Endpoints:**
- GET /api/v1/admin/users - List all users
- PUT /api/v1/admin/users/{id} - Update user status (activate/deactivate, admin flag)
- GET /api/v1/admin/stats - Platform statistics (users, invoices created, total invoiced)

**Frontend Pages:**
- /admin - Admin dashboard (protected, admin only)
- /admin/users - User management

---

### Module 7: Email Notifications

**Description:** Transactional email via an SMTP / email-service provider.

**Emails:**
- Welcome email on registration
- Password reset
- Invoice sent to client (PDF attached)
- Overdue reminder to client (scheduled daily job)
- Payment received confirmation (to the user)

---

### Module 8: File Uploads

**Description:** Uploads stored on local disk in development and S3-compatible storage in production.

**API Endpoints:**
- POST /api/v1/uploads/logo - Upload business logo (PNG/JPG/SVG, max 2 MB), shown on invoice PDFs
- POST /api/v1/invoices/{id}/attachments - Attach files (receipts, timesheets; max 10 MB)
- GET /api/v1/invoices/{id}/attachments - List attachments
- DELETE /api/v1/attachments/{id} - Delete attachment

**Models:**
- Attachment: id, user_id (FK), invoice_id (FK, nullable), filename, content_type, size_bytes, storage_key, created_at

---

## MVP SCOPE

### Must Have (MVP)
- [x] User registration and login (email/password + Google OAuth)
- [x] Basic client management (create / list / edit, needed to bill someone)
- [x] Create invoices with line items, tax, and due date
- [x] Download invoices as PDF

### Nice to Have (Post-MVP)
- [ ] Email invoices to clients
- [ ] Invoice status tracking (sent / paid / overdue / void) and mark as paid
- [ ] Payments module (full and partial payments)
- [ ] Dashboard & analytics (stats, revenue chart)
- [ ] Admin panel
- [ ] Email notifications (welcome, reset, reminders)
- [ ] File uploads (logo on PDF, invoice attachments)
- [ ] Payment provider integration ("Pay now" links)

---

## ACCEPTANCE CRITERIA

### Authentication
- [ ] User can register with email/password
- [ ] User can login with email/password
- [ ] User can sign up / login with Google OAuth (state parameter verified)
- [ ] JWT tokens work correctly with refresh
- [ ] Protected routes redirect to login

### Clients
- [ ] User can create, list, search, edit, and delete their own clients
- [ ] Users cannot see or modify other users' clients (404 on cross-tenant access)
- [ ] Client email is validated

### Invoices
- [ ] User can create an invoice for a client with 1+ line items, tax rate, optional discount, and due date
- [ ] Subtotal, tax, and total are calculated server-side with Decimal precision
- [ ] Invoice numbers are sequential and unique per user
- [ ] Due date cannot be before the issue date
- [ ] Only draft invoices can be edited or deleted
- [ ] User can download a correctly formatted PDF (business details, client, items, totals, due date)
- [ ] (Post-MVP) Sending an invoice emails the client with the PDF attached and sets status to sent
- [ ] (Post-MVP) Unpaid invoices past due date show as overdue

### Payments (Post-MVP)
- [ ] Recording payments updates amount_paid and the balance due
- [ ] Invoice becomes paid when payments cover the total
- [ ] Overpayment is rejected

### Dashboard (Post-MVP)
- [ ] Dashboard shows outstanding, paid, and overdue totals that match the underlying invoices
- [ ] Revenue chart shows paid revenue by month

### Admin (Post-MVP)
- [ ] Only admin users can access /admin endpoints and pages (403 otherwise)

### Quality
- [ ] All API endpoints documented in OpenAPI
- [ ] Backend test coverage 80%+
- [ ] Frontend TypeScript strict mode passes
- [ ] Docker builds and runs successfully

---

## SPECIAL REQUIREMENTS

### Security
- [x] Rate limiting on auth endpoints
- [x] Input validation on all endpoints (Pydantic)
- [x] SQL injection prevention (SQLAlchemy ORM only)
- [x] XSS prevention (escape user content in PDFs and emails)
- [x] CSRF protection for OAuth (state parameter)
- [x] Multi-tenant isolation: every query is scoped by user_id
- [x] Upload validation (MIME type, size limits, randomized storage keys)

### Integrations
- [x] Email service for notifications (SMTP / Resend / SendGrid via env config)
- [ ] Payment provider (none for now)
- [x] File upload storage (local in dev, S3-compatible in prod)
- [x] PDF generation (WeasyPrint or ReportLab)

---

## AGENTS

> These 6 agents will build your product in parallel:

| Agent | Role | Works On |
|-------|------|----------|
| DATABASE-AGENT | Creates all models and migrations | User, RefreshToken, Client, Invoice, InvoiceItem, Payment, Attachment |
| BACKEND-AGENT | Builds API endpoints and services | Auth, clients, invoices, PDF, email, uploads, dashboard, admin |
| FRONTEND-AGENT | Creates UI pages and components | All pages (Tailwind + shadcn/ui) |
| DEVOPS-AGENT | Sets up Docker, CI/CD, environments | Infrastructure |
| TEST-AGENT | Writes unit and integration tests | All code |
| REVIEW-AGENT | Security and code quality audit | All code |

---

# READY?

```bash
/generate-prp INITIAL.md
```

Then:

```bash
/execute-prp PRPs/invoiceflow-prp.md
```

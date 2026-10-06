# 2. Architecture

## 2.1 Style
A classic three-tier web application: **Next.js (TypeScript)** for the UI, **FastAPI** for a stateless JSON API, **PostgreSQL** for data. The API is the only component that touches the database. As built, the browser never calls the API directly: it talks to a **Next.js backend-for-frontend (BFF)** on the same origin, which holds the tokens in httpOnly cookies and forwards calls with `Authorization: Bearer <access token>`.

```mermaid
flowchart LR
  subgraph Browser
    UI[React pages<br/>Buyer / Seller / Admin / Research]
  end
  subgraph Web["Next.js server (:3000)"]
    GUARD[proxy.ts route guard]
    BFF["BFF route handlers<br/>/api/auth/login, /api/auth/logout,<br/>/api/proxy/* (attaches token, refreshes on 401)"]
  end
  subgraph Api["FastAPI (:8000)"]
    MW[Middleware: request-id, JSON access log,<br/>security headers, CORS]
    R[routers -> services -> models]
    AN[research: aggregates, Wilson CI, chi-square]
  end
  DB[(PostgreSQL 16)]
  UI -- same-origin fetch, httpOnly cookies --> GUARD --> BFF
  BFF -- JSON + Bearer JWT --> MW --> R
  R --> AN
  R -- SQLAlchemy 2 / psycopg --> DB
  R -. JSON logs .-> LOG[(stdout)]
  OPS[Alembic migrations + seed CLI] --> DB
```

## 2.2 Backend layers
| Layer | Responsibility | Must not |
|---|---|---|
| `routers/` | HTTP: parse, call service, return schema, declare required role | contain business rules or SQL |
| `schemas/` | Pydantic v2 request/response models and validation | touch the DB |
| `services/` | Business rules, transactions, audit events, authorisation of *objects* | know about HTTP |
| `models/` | SQLAlchemy 2 ORM models, constraints, indexes | contain logic |
| `core/` | settings, security (hashing, JWT), logging, errors, pagination, deps | import routers |

**Authorisation is two-step.** (1) A router dependency `require_role(...)` checks the *role*. (2) The service checks *ownership* (e.g. `product.seller_id == current_user.seller_profile.id`). Both are covered by tests, because a missing ownership check is the most common marketplace flaw.

## 2.3 Authentication flow
```mermaid
sequenceDiagram
  participant U as Browser
  participant A as FastAPI
  participant D as PostgreSQL
  U->>A: POST /auth/login {email, password}
  A->>D: load user, check lockout
  A->>A: bcrypt verify
  A->>D: store refresh token hash (rotating family)
  A-->>U: access JWT (15 min) + refresh token (7 days)
  U->>A: GET /orders (Bearer access)
  A->>A: verify signature, exp, role
  U->>A: POST /auth/refresh {refresh}
  A->>D: mark old refresh used, insert new
  A-->>U: new access + new refresh
  Note over A,D: reuse of a used refresh token revokes the whole family
```
Both tokens live in **httpOnly, SameSite=Lax cookies** (`Secure` over HTTPS) set by the Next.js BFF, so page JavaScript can never read them (XSS-resistant; asserted by an E2E test). The refresh cookie is scoped to `/api`. The BFF refreshes transparently on a 401 and never exposes the login/refresh/logout endpoints through its generic proxy. Mutating proxy calls also reject cross-origin `Origin` headers.

## 2.4 Order flow (simulated payment)
```mermaid
stateDiagram-v2
  [*] --> pending: buyer places order<br/>(stock reserved)
  pending --> confirmed: seller confirms
  pending --> cancelled: buyer or seller cancels<br/>(stock restored)
  confirmed --> ready: seller marks ready
  confirmed --> cancelled: seller cancels (reason)
  ready --> completed: seller marks handed over
  completed --> [*]
  cancelled --> [*]
```
`payment_preference` (`cash` | `mobile_money`) and `mobile_money_provider` are **labels the seller sees**; `payment_status` is the constant `not_processed`. No amount is ever sent anywhere.

## 2.5 Cross-cutting concerns
- **Errors**: every failure returns `{"error": {"code", "message", "details?", "request_id"}}` with a correct status (400/401/403/404/409/422/429/500). Unhandled exceptions are logged with a stack trace and returned as a generic 500.
- **Logging**: JSON lines (`ts, level, request_id, method, path, status, ms, user_id`); passwords, tokens and Authorization headers are never logged.
- **Pagination**: `?page=1&page_size=20` → `{items, page, page_size, total, pages}`; whitelisted `sort` fields.
- **Audit**: `created_at`/`updated_at` (timezone-aware UTC) on every table; `audit_log` rows for login success/failure, role-relevant changes, seller approval, order status changes and deletions.
- **Config**: 12-factor, environment variables only (`.env.example` documents them; `.env` is git-ignored).

## 2.6 Deployment view
```mermaid
flowchart TB
  subgraph docker-compose
    W[web: Next.js :3000] --> A[api: uvicorn :8000]
    A --> P[(db: postgres:16 :5432, volume)]
    M[migrate: alembic upgrade head] --> P
  end
  Dev[Developer / CI] -->|docker compose up| docker-compose
```
Production adds a TLS-terminating reverse proxy (Caddy/Nginx), managed PostgreSQL backups and secrets from the platform's secret store.

## 2.7 Key decisions (ADR summary)
| Decision | Why | Alternative rejected |
|---|---|---|
| JWT access + rotating refresh in httpOnly cookie | Stateless API, XSS-safe refresh token | Long-lived JWT in localStorage |
| SQLAlchemy 2 + Alembic | Typed models, reviewable migrations | Raw SQL / `create_all` |
| Single-seller orders | Simple fulfilment and permissions | Multi-vendor cart |
| Soft delete for products | Order history keeps referencing them | Hard delete |
| Price/name snapshot in `order_items` | Later price edits must not change past orders | Join to live product |
| Numeric money, integer stock | No float rounding | Float prices |

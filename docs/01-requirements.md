# 1. Requirements analysis

## 1.1 Problem and context
Micro and small enterprises (MSEs) in Kabul — bakeries, tailors, grocers, phone repair, carpentry, home kitchens — mostly sell face to face or through informal chat groups. They have no shared catalogue, no order record and no simple view of what customers want. Customers cannot easily discover nearby businesses or tell the seller in advance how they intend to pay. Cash dominates, and mobile money (M-Paisa, HesabPay and similar) is growing but not universal.

**Bazar.af** is a small marketplace where Sellers list products, Buyers place orders, and each order records the buyer's **simulated payment preference** (Cash or Mobile Money). The platform never moves money.

## 1.2 Hard constraints (from the brief)
| # | Constraint | Consequence |
|---|---|---|
| C1 | Roles: Buyer, Seller, Administrator | RBAC enforced on the server for every route |
| C2 | No real financial transactions | No payment gateway, card data, wallet numbers or balances. `payment_status` is always `not_processed`. Only a preference (`cash` / `mobile_money` + optional provider name) is stored |
| C3 | Stack: PostgreSQL, FastAPI, Next.js + TypeScript | Python 3.11 API, SQLAlchemy 2 + Alembic, Next.js App Router |
| C4 | Secure authentication, RBAC, server-side validation | Hashed passwords, short-lived JWT + rotating refresh tokens, Pydantic validation, lockout and rate limiting |
| C5 | Pagination, audit timestamps, logging, error handling | Shared page envelope; `created_at/updated_at` on every table; structured JSON logs with request IDs; one error format |
| C6 | Seed data, unit / API / integration / E2E tests | Realistic Kabul seed; pytest (unit, API, integration); Playwright E2E |
| C7 | Docker, docs, Git/GitHub discipline, no secrets in Git | `docker-compose`, `.env.example`, feature branches, tests before push |

## 1.3 Functional requirements
**Everyone (anonymous)** — FR1 browse and search approved sellers and active products (filter by category, district, price, text); FR2 view a product and a seller page.

**Buyer** — FR3 register / sign in / sign out; FR4 manage own profile (name, phone, district, address note); FR5 place an order with one or more items from **one seller**; FR6 choose a payment preference (Cash or Mobile Money + provider); FR7 see own orders and their status; FR8 cancel an order while it is still `pending`.

**Seller** — FR9 register as seller (starts `pending`); FR10 maintain a business profile (name, category, district, description, phone, opening hours); FR11 create / edit / hide / delete own products with price (AFN), stock and unit; FR12 see incoming orders, including the buyer's payment preference; FR13 move orders through `pending → confirmed → ready → completed`, or `cancelled` with a reason; FR14 see a small dashboard (orders today, open orders, top products).

**Administrator** — FR15 approve / reject / suspend sellers; FR16 list and deactivate users; FR17 manage categories; FR18 moderate products (hide); FR19 view all orders (read only); FR20 view the audit log; FR21 see platform statistics.

**Research module (public + Administrator)** — FR22 anyone can open a Research page with anonymous adoption figures computed from the Cash / Mobile Money choice at checkout (share of orders and buyers, provider, week, district, category, 95% confidence intervals, chi-square tests); FR23 groups with fewer than 5 orders are hidden publicly; FR24 admin sees every group; FR25 admin downloads an anonymised one-row-per-order CSV for the paper; FR26 sellers get live new-order alerts that stay until they act.

## 1.4 Non-functional requirements
- **Security**: bcrypt password hashing (cost 12), password policy, account lockout (5 failures → 15 min), login rate limit, JWT with `exp`, refresh-token rotation and revocation, object-level authorisation (a seller cannot touch another seller's products or orders), CORS allow-list, security headers, no secrets in Git, generic login errors (no user enumeration).
- **Correctness**: prices stored as `NUMERIC(12,2)`; order totals computed on the server from current prices, snapshotted into order items; stock decremented atomically in the same transaction as order creation (row lock) and restored on cancellation.
- **Observability**: JSON logs, `X-Request-ID`, access log, error log; audit log for security- and business-relevant events.
- **Maintainability**: layered modules (router → service → repository/models), one error type, typed schemas, migrations only (no `create_all` outside tests).
- **Performance targets (demo scale)**: list endpoints paginated (default 20, max 100) with indexes on all filter/sort columns; p95 < 300 ms on the seed data set.
- **Research ethics**: only stated Cash/Mobile Money preferences are analysed, no personal identifiers are shown or exported, results are aggregate-only (minimum group size 5 on the public page).
- **Usability**: responsive, loading / error / empty states on every data view, WCAG 2.1 AA targets (contrast, labels, focus, keyboard), usability test with >= 10 users (see docs/10-research-module.md);, keyboard accessible, English UI with Dari (RTL) planned as a later phase (see roadmap).

## 1.5 Out of scope
Real payments or wallet integration, delivery/courier logistics, reviews and ratings, chat, multi-seller carts, email/SMS delivery (verification codes can reuse the approach from the earlier *Pol connector* project), native mobile apps.

## 1.6 Assumptions to confirm
1. One order belongs to exactly one seller (simple, avoids split fulfilment). 2. Currency is AFN only. 3. Districts are a fixed list of Kabul's police districts (PD1–PD22) plus "Other". 4. Email is the login identifier; phone is required for contact. 5. Administrators are created by seed/CLI only, never by public sign-up.

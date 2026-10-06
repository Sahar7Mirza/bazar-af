# Bazar.af

A marketplace for micro and small enterprises (MSEs) in Kabul, combined with a **mobile-money adoption research module**. Built as a Bachelor of Computer Science capstone.

> **No real financial transactions are processed.** Buyers only record a *simulated* payment preference (Cash or Mobile Money + provider). The database itself forbids a paid order (`payment_status` is constrained to `not_processed`).

| | |
|---|---|
| Live demo | **https://bazar-af-eta.vercel.app** (API: https://bazar-af-api.vercel.app/api/v1/health) · demo logins in [docs/14-demo-accounts.md](docs/14-demo-accounts.md) |
| Roles | **Buyer**, **Seller** (needs admin approval), **Administrator** |
| Stack | PostgreSQL 16 · FastAPI (Python 3.11, SQLAlchemy 2, Alembic, Pydantic v2) · Next.js 16 + React 19 (TypeScript) · Docker |
| UI | Apple.com-inspired design, responsive, dark mode, WCAG-minded (axe-checked), loading / error / empty states |
| Research | Mobile-money adoption measured from the Cash / Mobile Money choice at checkout: share of orders and buyers, by provider, week, district and category |

> Deploying online: see [docs/13-deployment.md](docs/13-deployment.md) (Docker, or Vercel + Neon).

## Screenshots

Captured from the running app with the seeded demo data (all data is synthetic).

| | |
|---|---|
| ![Home](docs/img/01-home.png) | ![Shop](docs/img/02-products.png) |
| Landing page: marketplace for Kabul's small businesses | Shop with search, category, district and price filters |
| ![Product](docs/img/03-product.png) | ![Sign in](docs/img/04-signin.png) |
| Product page; payment is only a recorded preference | Sign in (JWT in httpOnly cookies) |
| ![Buyer orders](docs/img/05-buyer-orders.png) | ![Seller dashboard](docs/img/06-seller-dashboard.png) |
| Buyer: order history with Cash / Mobile Money preference | Seller: overview of orders, sales and top products |
| ![Seller products](docs/img/07-seller-products.png) | ![Seller orders](docs/img/08-seller-orders.png) |
| Seller: product management (edit, hide, delete) | Seller: incoming orders and status workflow |
| ![Admin dashboard](docs/img/09-admin-dashboard.png) | ![Seller approval](docs/img/10-admin-sellers.png) |
| Administrator: platform totals and payment-preference split | Administrator: seller approval queue |
| ![Audit log](docs/img/12-admin-audit.png) | |
| Audit log of logins and admin actions | |
| ![Recommended](docs/img/16-recommended.png) | ![Interests](docs/img/17-interests.png) |
| Buyer home: recommendations based on interests and past orders | Buyers choose the categories they care about |
| ![Notifications](docs/img/18-notifications.png) | |
| Alerts for order updates and new products in followed categories | |
| ![Order status chips](docs/img/19-order-status-chips.png) | ![Match strength](docs/img/20-match-strength.png) |
| Orders filter as status chips with live counts | Each recommendation shows a match-strength bar |
| ![Mobile](docs/img/14-mobile-home.png) | ![Dark mode](docs/img/15-dark-products.png) |
| Responsive layout on a phone | Dark mode follows the system setting |

Research page (mobile-money adoption from real orders, with plain-language insight cards):

![Research dashboard](docs/img/11-admin-research.png)

## Quick start (Docker)
```bash
git clone <this repo> && cd bazar-af
cp .env.example .env         # set POSTGRES_PASSWORD, JWT_SECRET (openssl rand -hex 32), SEED_PASSWORD
docker compose up -d --build
docker compose --profile seed run --rm seed     # demo data: 40 sellers, 172 products, 150 orders, 165 survey responses
```
Open http://localhost:3000. Demo accounts (password = your `SEED_PASSWORD`): `admin@demo.bazar.af`, `seller01@demo.bazar.af` ... `seller40`, `buyer01@demo.bazar.af` ... `buyer30`.
Swagger UI is at http://localhost:8000/docs when `ENVIRONMENT=development`.

More: [local install without Docker](docs/13-deployment.md) · [testing](docs/12-testing.md) · [deployment checklist](docs/13-deployment.md)

## What you can do
- **Anyone:** browse, search, filter (category, district, price) and sort products; see popular products.
- **Buyer:** register, cart (one seller per order), checkout with a Cash / Mobile Money preference, track and cancel pending orders.
- **Seller:** shop profile, product CRUD (soft delete, stock), incoming orders through `pending -> confirmed -> ready -> completed` or cancel (stock restored), dashboard.
- **Administrator:** approve / reject / suspend sellers, deactivate users, moderate products, manage categories, read every order, view the audit log, research dashboard and marketplace analytics.

## Security and engineering highlights
- bcrypt (cost 12), password policy, lockout after 5 failures, identical errors for unknown email / wrong password (no user enumeration, timing equalised).
- Short-lived JWT access tokens + **rotating refresh tokens stored only as hashes**; replaying a used token revokes the whole family.
- Tokens are **httpOnly cookies** held by the Next.js BFF; page JavaScript never sees them.
- **RBAC in two steps:** role dependency on the route, then object-level ownership check in the service (other users' resources return 404).
- Server-side validation everywhere (Pydantic); prices and totals computed on the server; row locks prevent overselling (tested with concurrent requests).
- Pagination on every list, `created_at`/`updated_at` on every table, append-only `audit_log`, JSON logs with request IDs, one error format, security headers, CORS allow-list.
- The anonymous survey API (no user id / IP / phone stored) still exists in the backend but has no page in the web app; adoption is measured from checkout preferences instead.
- Secrets only via environment variables; `.env` is git-ignored; `.env.example` documents everything; production refuses weak secrets and refuses to seed.

## Documentation
| Doc | |
|---|---|
| [01 Requirements](docs/01-requirements.md) | scope, constraints, functional / non-functional |
| [02 Architecture](docs/02-architecture.md) | architecture diagram, auth flow, order state machine |
| [03 Use cases](docs/03-use-cases.md) | actors and use cases |
| [04 ER diagram](docs/04-er-diagram.md) | Mermaid ER diagrams (marketplace + survey) |
| [05 Database schema](docs/05-database-schema.md) | SQL, constraints, indexes |
| [06 API structure](docs/06-api.md) · [OpenAPI JSON](docs/api/openapi.json) | endpoints, roles, error and page formats (regenerate: `python -m app.export_openapi`) |
| [07 UI plan](docs/07-ui-plan.md) · [08 Folder structure](docs/08-folder-structure.md) · [09 Roadmap](docs/09-roadmap.md) | |
| [10 Research module](docs/10-research-module.md) | instrument, statistics, dashboard |
| [11 v1 gap analysis](docs/11-v1-gap-analysis.md) | what the live v1 lacked and how this rebuild answers it |
| [12 Testing](docs/12-testing.md) · [13 Deployment](docs/13-deployment.md) · [14 Demo accounts](docs/14-demo-accounts.md) · [Usability plan](docs/usability/01-test-plan.md) | |

## Tests
Backend **108** (unit, API, integration incl. concurrency) at **96 %** coverage · frontend **8** unit · **20** Playwright E2E incl. axe accessibility scan. CI (`.github/workflows/ci.yml`) runs all of them on every push and pull request.

## Development workflow
Feature branches (`feature/...`) merged with `--no-ff` into `main`; tests run before each merge; commits are feature-based. No secrets are committed.

## Known limitations
- Dari (RTL) interface is planned; the questionnaire already carries Dari text (please proofread before real use).
- No email/SMS verification, password reset or image uploads yet.
- Demo orders and the dormant survey data are **synthetic**.
- Docker images are not yet built/verified (see [deployment notes](docs/13-deployment.md#verification-status)).

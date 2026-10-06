# 12 · Testing

| Layer | Tool | Location | What it proves |
|---|---|---|---|
| Unit (backend) | pytest | `backend/tests/unit` | password hashing, JWT rules, validation, config safety, **statistics vs known values** (Wilson interval, chi-square p-value) |
| API (backend) | pytest + FastAPI TestClient | `backend/tests/api` | every endpoint: success, validation errors, 401/403/404/409, RBAC matrix, ownership, pagination, lockout, refresh rotation/reuse |
| Integration | pytest + real PostgreSQL | `backend/tests/integration` | DB-enforced rules (no "paid" orders), seed data validity, **concurrent orders cannot oversell** (threads racing for the last item) |
| Unit (frontend) | Vitest | `frontend/tests` | API client error parsing, cart rules, formatting |
| E2E | Playwright (+ axe-core) | `frontend/e2e` | register, login, search/filter/paginate, cart, checkout with payment preference, cancel, seller product CRUD, order status flow, admin approval, public research page, live seller alert, RBAC redirects, httpOnly cookies, mobile layout, WCAG A/AA scan |

Backend tests run against the `TEST_DATABASE_URL` database (default `bazaraf_test`), which is wiped and rebuilt from the Alembic migrations at the start of each run, so the migrations themselves are exercised.

```bash
# backend
cd backend && pytest --cov=app --cov-report=term-missing
# frontend
cd frontend && npm run typecheck && npm run lint && npm test
# E2E (API seeded and running on :8000, web on :3000)
E2E_PASSWORD=<the SEED_PASSWORD you seeded with> npm run e2e
```
The E2E suite changes data (registers users, places orders, hides products). Re-seed with `python -m app.seed --reset` for a clean run. The "admin approves a pending seller" test skips itself once no pending sellers are left.

Latest results (30 Sep 2026): backend **108 passed, 96 % coverage**; frontend unit **8 passed**; E2E **20 passed**; ruff, tsc and ESLint clean.

# 09 · Phased roadmap

Each phase: feature branch → tests green → PR/merge (`--no-ff`) into `main` → pull/rebase → summary + `git status`.

| Phase | Branch | Deliverable | Exit check |
|---|---|---|---|
| 0 | `main` | Analysis, architecture, use cases, ER, schema, API, UI plan, roadmap | Docs reviewed |
| 1 | `feature/backend-foundation` | FastAPI skeleton, settings, PostgreSQL, Alembic migrations, logging, error handling, health | migrations apply; health test |
| 2 | `feature/auth-rbac` | Register/login/refresh/logout, bcrypt, JWT, lockout, RBAC deps, audit log | unit + API tests |
| 3 | `feature/catalog-orders` | Seller profile, categories, products, orders, admin, pagination, seed data | API + integration tests |
| 4 | `feature/frontend` | Next.js TS UI for all three roles | typecheck, lint, build |
| 5 | `feature/tests-docker-docs` | Playwright E2E, Dockerfiles, compose, CI, README, deployment guide | full suite green |

GitHub: remote added when the owner creates the repo; nothing with secrets is committed (`.env` ignored, `.env.example` tracked).

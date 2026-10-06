# 09 · Phased roadmap

Each phase: feature branch → tests green → PR/merge (`--no-ff`) into `main` → pull/rebase → summary + `git status`.

| Phase | Branch | Deliverable | Exit check |
|---|---|---|---|
| 0 | `main` | Analysis, architecture, use cases, ER, schema, API, UI plan, roadmap | Docs reviewed |
| 1 | `feature/backend-foundation` | FastAPI skeleton, settings, PostgreSQL, Alembic migrations, logging, error handling, health | migrations apply; health test |
| 2 | `feature/auth-rbac` | Register/login/refresh/logout, bcrypt, JWT, lockout, RBAC deps, audit log | unit + API tests |
| 3 | `feature/catalog-orders` | Seller profile, categories, products, orders, admin, pagination, seed data | API + integration tests |
| 3b | `feature/research-module` | Original survey module (later removed; adoption is now measured from checkout choices) | stats verified against known values |
| 4 | `feature/frontend` | Next.js TS UI for all three roles, research pages, all UI states | typecheck, lint, build |
| 5 | `feature/tests-docker-docs` | Playwright E2E, usability test kit, Dockerfiles, compose, CI, README, deployment guide | full suite green |

GitHub: remote added when the owner creates the repo; nothing with secrets is committed (`.env` ignored, `.env.example` tracked).

## Status
| Phase | Status | Tests at completion |
|---|---|---|
| 0 Design docs | done | - |
| 1 Backend foundation | done | 16 |
| 2 Auth + RBAC | done | 44 |
| 3 Catalog, orders, admin | done | 80 |
| 3b Research + seed | done | 108 (96% coverage) |
| 4 Frontend | done | + 8 unit, 20 E2E |
| 5 Docker, CI, docs | done (Docker images not built in the authoring sandbox - see README) | |

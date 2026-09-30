# 13 · Deployment

## Docker Compose (single host)
```bash
cp .env.example .env            # then edit: strong POSTGRES_PASSWORD, JWT_SECRET (openssl rand -hex 32)
docker compose up -d --build    # db -> api (runs migrations) -> web
docker compose --profile seed run --rm seed   # optional demo data (needs SEED_PASSWORD)
```
Web: http://localhost:3000 · API: http://localhost:8000 (Swagger at `/docs` only when `ENVIRONMENT=development`).

## Production checklist
- Put the stack behind HTTPS (Caddy, Nginx or a cloud load balancer) and set `COOKIE_SECURE=true`, `CORS_ORIGINS=https://your-domain`.
- `ENVIRONMENT=production`: the API refuses to start without a 32+ character `JWT_SECRET`, hides Swagger, and **refuses to seed demo data**.
- Do not expose port 8000 or 5432 publicly; only the web container needs to reach the API.
- Create the first administrator from the database or a one-off script (admins cannot self-register). Do not use the demo seed in production.
- Back up the `pgdata` volume (`pg_dump`). Migrations run automatically on API start (`alembic upgrade head`); they are forward-only in production.
- The in-memory survey rate limiter is per process; run one API replica or move limiting to the gateway/Redis before scaling out.
- Logs are JSON on stdout with `request_id`; collect them with your platform's log driver.

## Without Docker
```bash
# PostgreSQL 16 running; create role and database, then:
cd backend && python -m venv .venv && . .venv/bin/activate && pip install -r requirements-dev.txt
export DATABASE_URL=postgresql+psycopg://bazaraf:<pw>@localhost:5432/bazaraf ENVIRONMENT=development
alembic upgrade head && SEED_PASSWORD=<demo-pw> python -m app.seed
uvicorn app.main:app --reload --port 8000
cd ../frontend && npm ci && API_URL=http://localhost:8000/api/v1 npm run dev
```

## Verification status
The compose file, Dockerfiles and CI workflow were written and syntax-checked, and the same steps were executed natively (migrations, production-mode API start, standalone Next.js server). The authoring sandbox had no Docker daemon, so **the images themselves have not been built yet** - run `docker compose up --build` once and the CI workflow on first push to confirm.

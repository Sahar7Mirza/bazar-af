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

## Deploying on Vercel (frontend + API + Neon PostgreSQL)

Two Vercel projects are created from this one repository, plus a Neon database.

| Part | Vercel project root | Environment variables |
|---|---|---|
| API (FastAPI, Python runtime) | `backend` | `ENVIRONMENT=production`, `DATABASE_URL` (Neon, `postgresql+psycopg://...?sslmode=require`), `JWT_SECRET` (32+ chars), `CORS_ORIGINS` (the frontend URL), `APP_URL` (the frontend URL, for links in emails), `RESEND_API_KEY`, `EMAIL_FROM` |
| Web (Next.js) | `frontend` | `API_URL=https://<api-project>.vercel.app/api/v1` |

- The API entrypoint is `backend/index.py`. `backend/scripts/vercel_build.py` applies Alembic migrations at build time (skipped when `DATABASE_URL` is not set).
- Create the API project first, then the web project (it needs the API URL). Add the web URL to `CORS_ORIGINS` and redeploy the API.
- Demo data: `python -m app.seed --reset` refuses `ENVIRONMENT=production`. Run it once from a developer machine with `ENVIRONMENT=development`, `SEED_PASSWORD` and `DATABASE_URL` pointing at the Neon database.
- Limits to know: the Python bundle limit is 500 MB (the API is now small: the heavy statistics libraries were removed with the survey); account lockout is stored in the database, so it works across serverless instances.
- Vercel Deployment Protection must not block the API's production URL, or the web project's server-side calls will receive 401.


## Email (Resend)
Password-reset and email-confirmation links are sent through [Resend](https://resend.com). Add `RESEND_API_KEY` (secret), `EMAIL_FROM` and `APP_URL` to the API project's environment variables and redeploy. Without a key the app still works; emails are simply not sent.

- **Testing:** with the default sender `onboarding@resend.dev`, Resend only delivers to the email address of the Resend account owner. Use that address for a test account.
- **Real users:** verify a domain you own in Resend, then set `EMAIL_FROM` to an address on it (for example `Bazar.af <hello@yourdomain>`).
- Reset links work once and expire after 60 minutes; confirmation links expire after 48 hours. Resetting a password signs the account out everywhere.

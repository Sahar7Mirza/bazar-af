# 08 · Folder structure

```
bazar-af/
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
├── docs/                      # 01..09 design docs, diagrams, API notes
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml / requirements.txt
│   ├── alembic.ini
│   ├── alembic/versions/
│   ├── app/
│   │   ├── main.py            # app factory, middleware, routers
│   │   ├── core/              # config, security, logging, errors, deps
│   │   ├── db/                # engine, session, base
│   │   ├── models/            # SQLAlchemy
│   │   ├── schemas/           # Pydantic
│   │   ├── analytics/         # descriptives, reliability, correlation, regression
│   │   ├── services/          # business rules + ownership checks
│   │   ├── routers/           # auth, categories, sellers, products, orders, admin
│   │   └── seed.py
│   └── tests/
│       ├── unit/  api/  integration/
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── src/app/ (routes)  src/components/  src/lib/ (api client, zod)
│   └── e2e/                   # Playwright
└── .github/workflows/ci.yml
```

## As built
```
backend/app/{core,db,models,schemas,services,routers,analytics}  seed.py  seed_data.py  export_openapi.py
backend/alembic/versions/0001_initial_schema.py  0002_widen_survey_gender.py
backend/tests/{unit,api,integration}
frontend/src/app/...            pages (App Router) + api/auth/*, api/proxy/[...path]
frontend/src/{components,lib}   UI, typed API client, cart, cookies
frontend/src/proxy.ts           route guard (Next 16 replacement for middleware)
frontend/{tests,e2e}            Vitest unit tests, Playwright E2E
.github/workflows/ci.yml        backend + frontend + e2e jobs
docker-compose.yml  backend/Dockerfile  frontend/Dockerfile
docs/api/openapi.json           generated API reference
```

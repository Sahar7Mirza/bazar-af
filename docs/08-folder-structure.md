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

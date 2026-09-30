import os

# Must be set before the app imports settings.
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "postgresql+psycopg://bazaraf:dev-only-pw@localhost:5432/bazaraf_test")
os.environ["LOG_LEVEL"] = "WARNING"

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text

from alembic import command
from app.db.session import SessionLocal, engine


@pytest.fixture(scope="session", autouse=True)
def migrated():
    cfg = Config("alembic.ini")
    with engine.begin() as c:  # start from an empty schema so the migration itself is what gets tested
        c.execute(text("DROP SCHEMA public CASCADE"))
        c.execute(text("CREATE SCHEMA public"))
    command.upgrade(cfg, "head")
    yield


@pytest.fixture(autouse=True)
def clean_db(migrated):
    yield
    with engine.begin() as c:
        names = [r[0] for r in c.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename <> 'alembic_version'"))]
        c.execute(text("TRUNCATE " + ",".join(names) + " RESTART IDENTITY CASCADE"))


@pytest.fixture()
def db():
    with SessionLocal() as s:
        yield s


@pytest.fixture()
def client():
    from app.main import app

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

import random

import pytest
from sqlalchemy import func, select

from app import seed as seed_mod
from app.models import Order, Product, Role, SellerProfile, SellerStatus, SurveyResponse, User


def token(client, email):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "Demo-Only-2026"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def seeded(db):
    return seed_mod.seed(db, random.Random(1), "Demo-Only-2026", n_buyers=8, n_orders=60, n_survey=60)


def test_seed_creates_realistic_data(db, seeded):
    assert seeded["sellers"] == 40
    assert db.scalar(select(func.count()).select_from(SellerProfile).where(SellerProfile.status == SellerStatus.approved)) == 34
    assert db.scalar(select(func.count()).select_from(Product)) > 150
    assert db.scalar(select(func.count()).select_from(Order)) == 60
    assert db.scalar(select(func.count()).select_from(User).where(User.role == Role.admin)) == 1
    assert db.scalar(select(func.count()).select_from(SurveyResponse).where(SurveyResponse.is_synthetic)) == 60


def test_seed_is_deterministic(db):
    a = seed_mod.seed(db, random.Random(7), "Demo-Only-2026", 5, 20, 40)
    names1 = [p.name for p in db.scalars(select(Product).order_by(Product.id))]
    seed_mod.reset(db)
    b = seed_mod.seed(db, random.Random(7), "Demo-Only-2026", 5, 20, 40)
    assert a == b and names1 == [p.name for p in db.scalars(select(Product).order_by(Product.id))]


def test_seeded_orders_respect_business_rules(db, seeded):
    for o in db.scalars(select(Order)):
        assert o.payment_status == "not_processed"
        assert o.total_afn == sum(i.line_total_afn for i in o.items)
        assert (o.mobile_money_provider is not None) == (o.payment_preference.value == "mobile_money")
        assert len({db.get(Product, i.product_id).seller_id for i in o.items}) == 1


def test_seeded_accounts_can_log_in_and_public_market_has_products(client, db, seeded):
    assert token(client, "admin@demo.bazar.af")
    assert token(client, "seller01@demo.bazar.af")
    assert token(client, "buyer01@demo.bazar.af")
    assert client.get("/api/v1/products").json()["total"] > 100
    assert len(client.get("/api/v1/survey").json()) == 22


def test_seeded_research_dashboard_is_meaningful(client, db, seeded):
    h = token(client, "admin@demo.bazar.af")
    reg = client.get("/api/v1/admin/research/regression", headers=h).json()
    assert reg["ready"] and reg["r2"] > 0.2 and any(c["significant"] for c in reg["coefficients"])
    rel = client.get("/api/v1/admin/research/reliability", headers=h).json()["items"]
    assert all(r["alpha"] and r["alpha"] > 0.6 for r in rel)


def test_seed_refuses_without_password_or_in_production(monkeypatch):
    monkeypatch.delenv("SEED_PASSWORD", raising=False)
    with pytest.raises(SystemExit):
        seed_mod._password()
    from app.core import config

    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET", "x" * 40)
    config.get_settings.cache_clear()
    try:
        with pytest.raises(SystemExit):
            seed_mod.main()
    finally:
        monkeypatch.setenv("ENVIRONMENT", "test")
        config.get_settings.cache_clear()

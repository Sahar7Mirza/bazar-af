import random

import pytest
from sqlalchemy import func, select

from app import seed as seed_mod
from app.models import Order, Product, Role, SellerProfile, SellerStatus, User


def token(client, email):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "Demo-Only-2026"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def seeded(db):
    return seed_mod.seed(db, random.Random(1), "Demo-Only-2026", n_buyers=8, n_orders=60)


def test_seed_creates_realistic_data(db, seeded):
    assert seeded["sellers"] == 40
    assert db.scalar(select(func.count()).select_from(SellerProfile).where(SellerProfile.status == SellerStatus.approved)) == 34
    assert db.scalar(select(func.count()).select_from(Product)) > 150
    assert db.scalar(select(func.count()).select_from(Order)) == 60
    assert db.scalar(select(func.count()).select_from(User).where(User.role == Role.admin)) == 1


def test_seed_is_deterministic(db):
    a = seed_mod.seed(db, random.Random(7), "Demo-Only-2026", 5, 20)
    names1 = [p.name for p in db.scalars(select(Product).order_by(Product.id))]
    seed_mod.reset(db)
    b = seed_mod.seed(db, random.Random(7), "Demo-Only-2026", 5, 20)
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


def test_seeded_public_research_page_has_real_signal(client, db, seeded):
    r = client.get("/api/v1/research/summary").json()
    assert r["orders"] > 40 and 0 < r["mobile_money_share_pct"] < 100
    assert r["ci_pct"][0] < r["mobile_money_share_pct"] < r["ci_pct"][1]
    assert r["providers"] and r["weekly"]


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

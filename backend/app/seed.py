"""Seed realistic, clearly synthetic demo data.   Usage:  python -m app.seed [--reset]

Passwords come from SEED_PASSWORD (demo data only). Refuses to run in production."""

import os
import random
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select, text

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal, engine
from app.models import (
    Category,
    Order,
    OrderItem,
    OrderStatus,
    PaymentPreference,
    Product,
    Role,
    SellerProfile,
    SellerStatus,
    User,
)
from app.schemas.catalog import PROVIDERS
from app.seed_data import CATEGORIES, DISTRICT_WEIGHTS, FIRST, LAST, PRODUCTS, SHOPS
from app.services.catalog import slugify

ADMIN_EMAIL = "admin@demo.bazar.af"


def _password() -> str:
    pw = os.environ.get("SEED_PASSWORD")
    if not pw:
        raise SystemExit("Set SEED_PASSWORD (min 10 chars, letters+digits) to choose the demo password. Nothing is hard-coded.")
    return pw


def reset(db):
    names = [r[0] for r in db.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename <> 'alembic_version'"))]
    db.execute(text("TRUNCATE " + ",".join(names) + " RESTART IDENTITY CASCADE"))
    db.commit()
    db.expunge_all()  # drop stale identities so re-seeding in the same session is clean


def seed(db, rng: random.Random, pw: str, n_buyers=30, n_orders=150):
    ph = hash_password(pw)  # one hash reused: demo accounts share the demo password
    now = datetime.now(UTC)
    cats = {}
    for name in CATEGORIES:
        c = Category(name=name, slug=slugify(name))
        db.add(c)
        cats[name] = c
    db.add(User(email=ADMIN_EMAIL, password_hash=ph, full_name="Platform Admin", role=Role.admin, phone="+93700000000"))
    db.flush()
    dist = [d for d, w in DISTRICT_WEIGHTS.items() for _ in range(w)]

    def person():
        return f"{rng.choice(FIRST)} {rng.choice(LAST)}"

    statuses = [SellerStatus.approved] * 34 + [SellerStatus.pending] * 4 + [SellerStatus.rejected, SellerStatus.suspended]
    sellers = []
    for i, ((shop, cat), st) in enumerate(zip(SHOPS, statuses, strict=True), 1):
        u = User(
            email=f"seller{i:02d}@demo.bazar.af",
            password_hash=ph,
            full_name=person(),
            role=Role.seller,
            phone=f"+9370{rng.randint(1000000, 9999999)}",
            district=rng.choice(dist),
        )
        db.add(u)
        db.flush()
        sp = SellerProfile(
            user_id=u.id,
            business_name=shop,
            category_id=cats[cat].id,
            district=u.district,
            phone=u.phone,
            status=st,
            description=f"{shop} - serving {u.district} and nearby neighbourhoods in Kabul.",
            opening_hours="Sat-Thu 08:00-18:00",
            address_note=f"Main road, {u.district}",
            created_at=now - timedelta(days=rng.randint(30, 120)),
        )
        if st != SellerStatus.pending:
            sp.reviewed_at, sp.review_note = (
                now - timedelta(days=rng.randint(5, 25)),
                "Seed data" if st == SellerStatus.approved else "Incomplete details",
            )
        db.add(sp)
        db.flush()
        sellers.append((sp, cat))
        pool = PRODUCTS[cat]
        for name, unit, lo, hi in rng.sample(pool, k=min(len(pool), rng.randint(4, 6))):
            price = Decimal(rng.randrange(lo, hi + 1, 5 if hi > 100 else 1))
            db.add(
                Product(
                    seller_id=sp.id,
                    category_id=cats[cat].id,
                    name=name,
                    unit=unit,
                    price_afn=price,
                    stock_qty=rng.randint(20, 300),
                    description=f"{name} from {shop}.",
                    created_at=now - timedelta(days=rng.randint(1, 60)),
                )
            )
    db.flush()

    buyers = []
    for i in range(1, n_buyers + 1):
        u = User(
            email=f"buyer{i:02d}@demo.bazar.af",
            password_hash=ph,
            full_name=person(),
            role=Role.buyer,
            phone=f"+9379{rng.randint(1000000, 9999999)}",
            district=rng.choice(dist),
        )
        db.add(u)
        buyers.append(u)
    db.flush()

    live = list(db.scalars(select(Product).join(SellerProfile).where(SellerProfile.status == SellerStatus.approved)))
    by_seller: dict[int, list[Product]] = {}
    for p in live:
        by_seller.setdefault(p.seller_id, []).append(p)
    sids = list(by_seller)
    mm_bias = 0.42
    for _ in range(n_orders):
        sid = rng.choice(sids)
        prods = rng.sample(by_seller[sid], k=rng.randint(1, min(3, len(by_seller[sid]))))
        pref = PaymentPreference.mobile_money if rng.random() < mm_bias else PaymentPreference.cash
        status = rng.choices(list(OrderStatus), weights=[10, 12, 8, 62, 8])[0]
        created = now - timedelta(days=rng.uniform(0, 60))
        o = Order(
            buyer_id=rng.choice(buyers).id,
            seller_id=sid,
            status=status,
            payment_preference=pref,
            total_afn=0,
            created_at=created,
            updated_at=created,
            mobile_money_provider=rng.choices(PROVIDERS[:4], weights=[5, 4, 2, 1])[0] if pref == PaymentPreference.mobile_money else None,
            cancel_reason="Changed mind" if status == OrderStatus.cancelled else None,
        )
        total = Decimal(0)
        for p in prods:
            q = rng.randint(1, 5)
            line = p.price_afn * q
            total += line
            o.items.append(
                OrderItem(product_id=p.id, product_name=p.name, unit_price_afn=p.price_afn, quantity=q, line_total_afn=line, created_at=created)
            )
            if status != OrderStatus.cancelled:
                p.stock_qty = max(0, p.stock_qty - q)
        o.total_afn = total
        db.add(o)
    db.flush()

    db.commit()
    return {"sellers": len(sellers), "buyers": n_buyers, "products": len(live), "orders": n_orders}


def main():
    if get_settings().environment == "production":
        raise SystemExit("Refusing to seed demo data in production.")
    pw = _password()
    with SessionLocal() as db:
        if "--reset" in sys.argv:
            reset(db)
        elif db.scalar(select(User.id).limit(1)):
            raise SystemExit("Database already has data. Use --reset to rebuild the demo data.")
        counts = seed(db, random.Random(20260930), pw)
    print("Seeded:", counts, f"| admin: {ADMIN_EMAIL} | sellers: seller01..40@demo.bazar.af | buyers: buyer01..30@demo.bazar.af")
    engine.dispose()


if __name__ == "__main__":
    main()

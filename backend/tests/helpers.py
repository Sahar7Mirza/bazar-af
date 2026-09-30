from sqlalchemy import select

from app.core.security import hash_password
from app.models import Category, Product, Role, SellerProfile, SellerStatus, User

PW = "Str0ngPassw0rd"


def make_user(db, email, role=Role.buyer, active=True):
    u = User(email=email, password_hash=hash_password(PW), full_name=email.split("@")[0].title(), role=role, is_active=active)
    db.add(u)
    db.commit()
    return u


def token(client, email):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": PW})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def make_seller(db, email, status=SellerStatus.approved, name="Shop"):
    u = make_user(db, email, Role.seller)
    sp = SellerProfile(user_id=u.id, business_name=name, status=status, district="PD4")
    db.add(sp)
    db.commit()
    return u, sp


def make_product(db, sp, name="Bread", price="25.00", stock=10, **kw):
    p = Product(seller_id=sp.id, name=name, price_afn=price, stock_qty=stock, **kw)
    db.add(p)
    db.commit()
    return p


def make_category(db, name="Food"):
    c = db.scalar(select(Category).where(Category.name == name))
    if not c:
        c = Category(name=name, slug=name.lower())
        db.add(c)
        db.commit()
    return c

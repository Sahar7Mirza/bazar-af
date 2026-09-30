from sqlalchemy import select

from app.models import Role, SellerProfile, SellerStatus
from tests.helpers import make_product, make_seller, make_user, token


def admin(client, db):
    make_user(db, "admin@x.af", Role.admin)
    return token(client, "admin@x.af")


def test_admin_endpoints_forbidden_for_others(client, db):
    make_user(db, "b@x.af", Role.buyer)
    make_seller(db, "s@x.af")
    for email in ("b@x.af", "s@x.af"):
        h = token(client, email)
        for path in ("/users", "/sellers", "/orders", "/stats", "/audit"):
            assert client.get(f"/api/v1/admin{path}", headers=h).status_code == 403, (email, path)
    assert client.get("/api/v1/admin/users").status_code == 401


def test_approve_seller_flow_makes_products_public(client, db):
    _, sp = make_seller(db, "s@x.af", SellerStatus.pending)
    h = admin(client, db)
    assert client.get("/api/v1/admin/sellers", params={"status": "pending"}, headers=h).json()["total"] == 1
    r = client.post(f"/api/v1/admin/sellers/{sp.id}/approve", json={"note": "Checked shop"}, headers=h)
    assert r.status_code == 200 and r.json()["status"] == "approved"
    assert client.post(f"/api/v1/admin/sellers/{sp.id}/approve", json={}, headers=h).status_code == 409
    hs = token(client, "s@x.af")
    assert client.post("/api/v1/products", json={"name": "Tea", "price_afn": 5}, headers=hs).status_code == 201
    assert client.get("/api/v1/products").json()["total"] == 1
    client.post(f"/api/v1/admin/sellers/{sp.id}/suspend", json={"note": "complaint"}, headers=h)
    assert client.get("/api/v1/products").json()["total"] == 0


def test_reject_seller(client, db):
    _, sp = make_seller(db, "s@x.af", SellerStatus.pending)
    h = admin(client, db)
    assert client.post(f"/api/v1/admin/sellers/{sp.id}/reject", json={"note": "Incomplete"}, headers=h).json()["status"] == "rejected"
    db.expire_all()
    assert db.scalar(select(SellerProfile).where(SellerProfile.id == sp.id)).reviewed_by


def test_deactivate_user_blocks_access_and_revokes_tokens(client, db):
    u = make_user(db, "b@x.af", Role.buyer)
    t = client.post("/api/v1/auth/login", json={"email": "b@x.af", "password": "Str0ngPassw0rd"}).json()
    h = admin(client, db)
    assert client.patch(f"/api/v1/admin/users/{u.id}", json={"is_active": False}, headers=h).status_code == 200
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {t['access_token']}"}).status_code == 401
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": t["refresh_token"]}).status_code == 401


def test_admin_cannot_deactivate_self(client, db):
    h = admin(client, db)
    me = client.get("/api/v1/auth/me", headers=h).json()
    assert client.patch(f"/api/v1/admin/users/{me['id']}", json={"is_active": False}, headers=h).status_code == 409


def test_hide_product_moderation(client, db):
    _, sp = make_seller(db, "s@x.af")
    p = make_product(db, sp)
    h = admin(client, db)
    client.post(f"/api/v1/admin/products/{p.id}/hide", headers=h)
    assert client.get("/api/v1/products").json()["total"] == 0
    client.post(f"/api/v1/admin/products/{p.id}/unhide", headers=h)
    assert client.get("/api/v1/products").json()["total"] == 1


def test_categories_admin_crud(client, db):
    h = admin(client, db)
    r = client.post("/api/v1/admin/categories", json={"name": "Dry Fruits"}, headers=h)
    assert r.status_code == 201 and r.json()["slug"] == "dry-fruits"
    assert client.post("/api/v1/admin/categories", json={"name": "Dry Fruits"}, headers=h).status_code == 409
    cid = r.json()["id"]
    assert client.patch(f"/api/v1/admin/categories/{cid}", json={"is_active": False}, headers=h).json()["is_active"] is False
    assert client.get("/api/v1/categories").json() == []


def test_stats_and_audit_and_user_list_filters(client, db):
    _, sp = make_seller(db, "s@x.af")
    make_user(db, "b@x.af", Role.buyer)
    p = make_product(db, sp)
    hb = token(client, "b@x.af")
    client.post(
        "/api/v1/orders",
        json={"items": [{"product_id": p.id, "quantity": 2}], "payment_preference": "mobile_money", "mobile_money_provider": "M-Paisa"},
        headers=hb,
    )
    client.post("/api/v1/orders", json={"items": [{"product_id": p.id, "quantity": 1}], "payment_preference": "cash"}, headers=hb)
    h = admin(client, db)
    s = client.get("/api/v1/admin/stats", headers=h).json()
    assert s["orders_total"] == 2 and s["payment_preference"] == {"cash": 1, "mobile_money": 1} and s["mobile_money_providers"] == {"M-Paisa": 1}
    assert s["total_value_afn"] == "75.00"
    a = client.get("/api/v1/admin/audit", params={"action": "order.create"}, headers=h).json()
    assert a["total"] == 2 and a["items"][0]["created_at"]
    assert client.get("/api/v1/admin/users", params={"role": "seller"}, headers=h).json()["total"] == 1
    assert client.get("/api/v1/admin/users", params={"q": "b@x"}, headers=h).json()["total"] == 1

from sqlalchemy import select

from app.models import Order, Product, Role
from tests.helpers import make_product, make_seller, make_user, token


def setup(db, stock=10):
    su, sp = make_seller(db, "s@x.af")
    make_user(db, "b@x.af", Role.buyer)
    p = make_product(db, sp, "Bread", "25.00", stock)
    return su, sp, p


def order(client, h, items, pref="cash", provider=None, **kw):
    body = {"items": items, "payment_preference": pref, **kw}
    if provider:
        body["mobile_money_provider"] = provider
    return client.post("/api/v1/orders", json=body, headers=h)


def test_create_order_computes_total_server_side_and_reduces_stock(client, db):
    _, _, p = setup(db)
    r = order(client, token(client, "b@x.af"), [{"product_id": p.id, "quantity": 3}])
    assert r.status_code == 201
    o = r.json()
    assert o["total_afn"] == "75.00" and o["status"] == "pending" and o["payment_status"] == "not_processed"
    assert o["items"][0]["unit_price_afn"] == "25.00"
    db.expire_all()
    assert db.get(Product, p.id).stock_qty == 7


def test_client_cannot_set_price_or_payment_status(client, db):
    _, _, p = setup(db)
    body = {
        "items": [{"product_id": p.id, "quantity": 1, "unit_price_afn": "0.01"}],
        "payment_preference": "cash",
        "payment_status": "paid",
        "total_afn": "0.01",
    }
    o = client.post("/api/v1/orders", json=body, headers=token(client, "b@x.af")).json()
    assert o["total_afn"] == "25.00" and o["payment_status"] == "not_processed"


def test_payment_preference_rules(client, db):
    _, _, p = setup(db)
    h = token(client, "b@x.af")
    item = [{"product_id": p.id, "quantity": 1}]
    assert order(client, h, item, "mobile_money").status_code == 422
    assert order(client, h, item, "cash", "M-Paisa").status_code == 422
    assert order(client, h, item, "mobile_money", "FakePay").status_code == 422
    assert order(client, h, item, "bitcoin").status_code == 422
    r = order(client, h, item, "mobile_money", "HesabPay")
    assert r.status_code == 201 and r.json()["mobile_money_provider"] == "HesabPay"


def test_insufficient_stock_conflict_and_nothing_changes(client, db):
    _, _, p = setup(db, stock=2)
    r = order(client, token(client, "b@x.af"), [{"product_id": p.id, "quantity": 3}])
    assert r.status_code == 409 and r.json()["error"]["code"] == "insufficient_stock"
    db.expire_all()
    assert db.get(Product, p.id).stock_qty == 2 and not db.scalars(select(Order)).all()


def test_single_seller_and_duplicate_items_rules(client, db):
    _, _, p = setup(db)
    _, sp2 = make_seller(db, "s2@x.af", name="Other")
    q = make_product(db, sp2, "Tea")
    h = token(client, "b@x.af")
    assert order(client, h, [{"product_id": p.id, "quantity": 1}, {"product_id": q.id, "quantity": 1}]).status_code == 422
    assert order(client, h, [{"product_id": p.id, "quantity": 1}, {"product_id": p.id, "quantity": 1}]).status_code == 422
    assert order(client, h, []).status_code == 422
    assert order(client, h, [{"product_id": p.id, "quantity": 0}]).status_code == 422


def test_unavailable_products_rejected(client, db):
    _, sp, p = setup(db)
    hidden = make_product(db, sp, "Hid", status="hidden")
    h = token(client, "b@x.af")
    assert order(client, h, [{"product_id": hidden.id, "quantity": 1}]).status_code == 404
    assert order(client, h, [{"product_id": 99999, "quantity": 1}]).status_code == 404


def test_only_buyers_can_order(client, db):
    _, _, p = setup(db)
    r = order(client, token(client, "s@x.af"), [{"product_id": p.id, "quantity": 1}])
    assert r.status_code == 403
    assert client.post("/api/v1/orders", json={}).status_code == 401


def test_order_visibility_is_object_level(client, db):
    _, _, p = setup(db)
    make_user(db, "b2@x.af", Role.buyer)
    make_seller(db, "s2@x.af", name="Other")
    make_user(db, "admin@x.af", Role.admin)
    oid = order(client, token(client, "b@x.af"), [{"product_id": p.id, "quantity": 1}]).json()["id"]
    assert client.get(f"/api/v1/orders/{oid}", headers=token(client, "b@x.af")).status_code == 200
    assert client.get(f"/api/v1/orders/{oid}", headers=token(client, "s@x.af")).status_code == 200
    assert client.get(f"/api/v1/orders/{oid}", headers=token(client, "admin@x.af")).status_code == 200
    assert client.get(f"/api/v1/orders/{oid}", headers=token(client, "b2@x.af")).status_code == 404
    assert client.get(f"/api/v1/orders/{oid}", headers=token(client, "s2@x.af")).status_code == 404
    assert client.get("/api/v1/orders", headers=token(client, "b2@x.af")).json()["total"] == 0
    assert client.get("/api/v1/orders", headers=token(client, "s2@x.af")).json()["total"] == 0
    assert client.get("/api/v1/orders", headers=token(client, "s@x.af")).json()["total"] == 1


def test_status_machine(client, db):
    _, _, p = setup(db)
    hb, hs = token(client, "b@x.af"), token(client, "s@x.af")
    oid = order(client, hb, [{"product_id": p.id, "quantity": 1}]).json()["id"]
    url = f"/api/v1/orders/{oid}/status"
    assert client.post(url, json={"status": "ready"}, headers=hs).status_code == 409  # cannot skip
    assert client.post(url, json={"status": "confirmed"}, headers=hb).status_code == 403  # buyers cannot
    for st in ("confirmed", "ready", "completed"):
        assert client.post(url, json={"status": st}, headers=hs).json()["status"] == st
    assert client.post(url, json={"status": "confirmed"}, headers=hs).status_code == 409
    assert client.post(f"/api/v1/orders/{oid}/cancel", json={}, headers=hs).status_code == 409  # completed is final


def test_other_seller_cannot_change_status(client, db):
    _, _, p = setup(db)
    make_seller(db, "s2@x.af", name="Other")
    oid = order(client, token(client, "b@x.af"), [{"product_id": p.id, "quantity": 1}]).json()["id"]
    assert client.post(f"/api/v1/orders/{oid}/status", json={"status": "confirmed"}, headers=token(client, "s2@x.af")).status_code == 404


def test_cancel_restores_stock_and_buyer_limited_to_pending(client, db):
    _, _, p = setup(db)
    hb, hs = token(client, "b@x.af"), token(client, "s@x.af")
    a = order(client, hb, [{"product_id": p.id, "quantity": 4}]).json()["id"]
    r = client.post(f"/api/v1/orders/{a}/cancel", json={"reason": "changed mind"}, headers=hb)
    assert r.status_code == 200 and r.json()["status"] == "cancelled"
    db.expire_all()
    assert db.get(Product, p.id).stock_qty == 10
    assert client.post(f"/api/v1/orders/{a}/cancel", json={}, headers=hb).status_code == 409  # double cancel
    b = order(client, hb, [{"product_id": p.id, "quantity": 2}]).json()["id"]
    client.post(f"/api/v1/orders/{b}/status", json={"status": "confirmed"}, headers=hs)
    assert client.post(f"/api/v1/orders/{b}/cancel", json={}, headers=hb).status_code == 409  # buyer too late
    assert client.post(f"/api/v1/orders/{b}/cancel", json={"reason": "no stock"}, headers=hs).status_code == 200
    db.expire_all()
    assert db.get(Product, p.id).stock_qty == 10


def test_order_keeps_price_snapshot_after_price_change_and_delete(client, db):
    _, _, p = setup(db)
    hb, hs = token(client, "b@x.af"), token(client, "s@x.af")
    oid = order(client, hb, [{"product_id": p.id, "quantity": 2}]).json()["id"]
    client.patch(f"/api/v1/products/{p.id}", json={"price_afn": "99.00", "name": "Renamed"}, headers=hs)
    client.delete(f"/api/v1/products/{p.id}", headers=hs)
    o = client.get(f"/api/v1/orders/{oid}", headers=hb).json()
    assert o["total_afn"] == "50.00" and o["items"][0]["unit_price_afn"] == "25.00" and o["items"][0]["product_name"] == "Bread"


def test_order_list_pagination_and_filter(client, db):
    _, _, p = setup(db, stock=100)
    hb = token(client, "b@x.af")
    for _ in range(7):
        order(client, hb, [{"product_id": p.id, "quantity": 1}])
    r = client.get("/api/v1/orders", params={"page_size": 5}, headers=hb).json()
    assert r["total"] == 7 and r["pages"] == 2 and len(r["items"]) == 5
    assert client.get("/api/v1/orders", params={"status": "completed"}, headers=hb).json()["total"] == 0
    # chip counts ignore the status filter and always cover the whole list
    counts = client.get("/api/v1/orders", params={"status": "completed"}, headers=hb).json()["counts"]
    assert counts == {"pending": 7, "confirmed": 0, "ready": 0, "completed": 0, "cancelled": 0}
    make_user(db, "admin@x.af", Role.admin)
    assert client.get("/api/v1/admin/orders", headers=token(client, "admin@x.af")).json()["counts"]["pending"] == 7
    assert client.get("/api/v1/orders", params={"status": "bogus"}, headers=hb).status_code == 422


def test_audit_written_for_order_events(client, db):
    from app.models import AuditLog

    _, _, p = setup(db)
    hb, hs = token(client, "b@x.af"), token(client, "s@x.af")
    oid = order(client, hb, [{"product_id": p.id, "quantity": 1}]).json()["id"]
    client.post(f"/api/v1/orders/{oid}/status", json={"status": "confirmed"}, headers=hs)
    acts = [a.action for a in db.scalars(select(AuditLog).where(AuditLog.entity_type == "order").order_by(AuditLog.id))]
    assert acts == ["order.create", "order.status"]

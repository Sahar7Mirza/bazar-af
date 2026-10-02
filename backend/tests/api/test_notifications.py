from datetime import UTC, datetime

from app.models import Notification, Role
from tests.helpers import make_product, make_seller, make_user, token


def placed(client, db):
    su, sp = make_seller(db, "s@x.af", name="Qargha Bakery")
    make_user(db, "b@x.af", Role.buyer)
    make_user(db, "b2@x.af", Role.buyer)
    p = make_product(db, sp, "Bread", "25.00", 10)
    bh, sh = token(client, "b@x.af"), token(client, "s@x.af")
    oid = client.post("/api/v1/orders", json={"items": [{"product_id": p.id, "quantity": 1}], "payment_preference": "cash"}, headers=bh).json()["id"]
    return oid, bh, sh


def test_confirm_notifies_buyer_with_pickup_estimate(client, db):
    oid, bh, sh = placed(client, db)
    assert client.get("/api/v1/notifications/unread-count", headers=bh).json() == {"unread": 0}
    r = client.post(f"/api/v1/orders/{oid}/status", json={"status": "confirmed", "pickup_in_minutes": 90}, headers=sh)
    assert r.status_code == 200
    est = datetime.fromisoformat(r.json()["estimated_pickup_at"])
    assert 80 * 60 < (est - datetime.now(UTC)).total_seconds() < 100 * 60
    items = client.get("/api/v1/notifications", headers=bh).json()["items"]
    assert len(items) == 1 and items[0]["kind"] == "order_confirmed"
    assert f"#{oid}" in items[0]["message"] and "1 hour 30 minutes" in items[0]["message"] and "Qargha Bakery" in items[0]["message"]
    assert client.get("/api/v1/notifications/unread-count", headers=bh).json() == {"unread": 1}


def test_confirm_defaults_to_sixty_minutes(client, db):
    oid, bh, sh = placed(client, db)
    r = client.post(f"/api/v1/orders/{oid}/status", json={"status": "confirmed"}, headers=sh)
    est = datetime.fromisoformat(r.json()["estimated_pickup_at"])
    assert 55 * 60 < (est - datetime.now(UTC)).total_seconds() < 65 * 60
    assert "1 hour" in client.get("/api/v1/notifications", headers=bh).json()["items"][0]["message"]


def test_ready_notifies_buyer_with_order_number(client, db):
    oid, bh, sh = placed(client, db)
    client.post(f"/api/v1/orders/{oid}/status", json={"status": "confirmed"}, headers=sh)
    client.post(f"/api/v1/orders/{oid}/status", json={"status": "ready"}, headers=sh)
    items = client.get("/api/v1/notifications", headers=bh).json()["items"]
    assert [i["kind"] for i in items] == ["order_ready", "order_confirmed"]
    assert items[0]["message"] == f"Your order #{oid} is ready for pick up at Qargha Bakery."


def test_seller_cancel_notifies_buyer_but_buyer_cancel_does_not(client, db):
    oid, bh, sh = placed(client, db)
    client.post(f"/api/v1/orders/{oid}/cancel", json={"reason": "Out of flour"}, headers=sh)
    items = client.get("/api/v1/notifications", headers=bh).json()["items"]
    assert items[0]["kind"] == "order_cancelled" and "Out of flour" in items[0]["message"]


def test_buyer_cancelling_own_order_creates_no_notification(client, db):
    oid, bh, _ = placed(client, db)
    client.post(f"/api/v1/orders/{oid}/cancel", json={}, headers=bh)
    assert client.get("/api/v1/notifications/unread-count", headers=bh).json() == {"unread": 0}


def test_invalid_pickup_minutes_rejected(client, db):
    oid, _, sh = placed(client, db)
    for bad in (0, 4, 10081):
        assert client.post(f"/api/v1/orders/{oid}/status", json={"status": "confirmed", "pickup_in_minutes": bad}, headers=sh).status_code == 422


def test_mark_read_and_read_all(client, db):
    oid, bh, sh = placed(client, db)
    client.post(f"/api/v1/orders/{oid}/status", json={"status": "confirmed"}, headers=sh)
    client.post(f"/api/v1/orders/{oid}/status", json={"status": "ready"}, headers=sh)
    nid = client.get("/api/v1/notifications", headers=bh).json()["items"][0]["id"]
    r = client.post(f"/api/v1/notifications/{nid}/read", headers=bh)
    assert r.status_code == 200 and r.json()["read_at"]
    assert client.get("/api/v1/notifications/unread-count", headers=bh).json() == {"unread": 1}
    assert len(client.get("/api/v1/notifications?unread=true", headers=bh).json()["items"]) == 1
    assert client.post("/api/v1/notifications/read-all", headers=bh).json() == {"marked": 1}
    assert client.get("/api/v1/notifications/unread-count", headers=bh).json() == {"unread": 0}


def test_notifications_are_private_and_need_login(client, db):
    oid, bh, sh = placed(client, db)
    client.post(f"/api/v1/orders/{oid}/status", json={"status": "confirmed"}, headers=sh)
    other = token(client, "b2@x.af")
    assert client.get("/api/v1/notifications", headers=other).json()["items"] == []
    nid = db.query(Notification).one().id
    assert client.post(f"/api/v1/notifications/{nid}/read", headers=other).status_code == 404
    assert client.get("/api/v1/notifications").status_code == 401
    assert client.get("/api/v1/notifications/unread-count").status_code == 401

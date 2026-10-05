from app.models import Category, Role
from tests.helpers import make_product, make_seller, make_user, token


def cats(db):
    a, b = Category(name="Food & Bakery", slug="food"), Category(name="Electronics", slug="elec")
    db.add_all([a, b])
    db.commit()
    return a, b


def shop(db):
    food, elec = cats(db)
    su, sp = make_seller(db, "s@x.af", name="Qargha Shop")
    bread = make_product(db, sp, "Bread", "25.00", 20, category_id=food.id)
    cake = make_product(db, sp, "Cake", "120.00", 20, category_id=food.id)
    phone = make_product(db, sp, "Charger", "300.00", 20, category_id=elec.id)
    make_user(db, "b@x.af", Role.buyer)
    return food, elec, bread, cake, phone


def test_interests_roundtrip_validation_and_role(client, db):
    food, elec, *_ = shop(db)
    h = token(client, "b@x.af")
    assert client.get("/api/v1/me/interests", headers=h).json() == {"category_ids": []}
    r = client.put("/api/v1/me/interests", json={"category_ids": [elec.id, food.id, food.id]}, headers=h)
    assert r.status_code == 200 and r.json() == {"category_ids": sorted([food.id, elec.id])}
    assert client.put("/api/v1/me/interests", json={"category_ids": [food.id]}, headers=h).json() == {"category_ids": [food.id]}
    assert client.put("/api/v1/me/interests", json={"category_ids": [9999]}, headers=h).status_code == 422
    assert client.put("/api/v1/me/interests", json={"category_ids": list(range(1, 10))}, headers=h).status_code == 422
    assert client.get("/api/v1/me/interests").status_code == 401
    assert client.get("/api/v1/me/interests", headers=token(client, "s@x.af")).status_code == 403


def test_recommendations_follow_interests(client, db):
    food, elec, bread, cake, phone = shop(db)
    h = token(client, "b@x.af")
    client.put("/api/v1/me/interests", json={"category_ids": [elec.id]}, headers=h)
    items = client.get("/api/v1/recommendations?limit=3", headers=h).json()
    assert items[0]["id"] == phone.id and items[0]["reason"] == "Matches your interest in Electronics"
    assert {i["id"] for i in items} == {bread.id, cake.id, phone.id} and items[1]["reason"] == "Popular in Kabul"


def test_recommendations_use_order_history_and_demote_already_bought(client, db):
    food, elec, bread, cake, phone = shop(db)
    h = token(client, "b@x.af")
    client.post("/api/v1/orders", json={"items": [{"product_id": bread.id, "quantity": 1}], "payment_preference": "cash"}, headers=h)
    items = client.get("/api/v1/recommendations?limit=3", headers=h).json()
    assert items[0]["id"] == cake.id and "ordered Food & Bakery before" in items[0]["reason"]
    assert items[-1]["id"] == bread.id or items[-1]["id"] == phone.id


def test_recommendations_for_anonymous_and_empty_catalog(client, db):
    assert client.get("/api/v1/recommendations").json() == []
    shop(db)
    r = client.get("/api/v1/recommendations?limit=2")
    assert r.status_code == 200 and len(r.json()) == 2 and all(i["reason"] == "Popular in Kabul" for i in r.json())
    assert client.get("/api/v1/recommendations", headers={"Authorization": "Bearer junk"}).status_code == 200
    assert client.get("/api/v1/recommendations?limit=0").status_code == 422


def test_similar_products_same_category_first_and_excludes_self(client, db):
    food, elec, bread, cake, phone = shop(db)
    ids = [i["id"] for i in client.get(f"/api/v1/products/{bread.id}/similar?limit=3").json()]
    assert ids[0] == cake.id and bread.id not in ids and phone.id in ids
    assert client.get("/api/v1/products/9999/similar").status_code == 404


def test_new_product_notifies_only_interested_buyers(client, db):
    food, elec, *_ = shop(db)
    make_user(db, "b2@x.af", Role.buyer)
    make_user(db, "b3@x.af", Role.buyer)
    client.put("/api/v1/me/interests", json={"category_ids": [food.id]}, headers=token(client, "b@x.af"))
    client.put("/api/v1/me/interests", json={"category_ids": [elec.id]}, headers=token(client, "b2@x.af"))
    sh = token(client, "s@x.af")
    r = client.post(
        "/api/v1/products", json={"name": "Naan", "price_afn": "10.00", "unit": "piece", "stock_qty": 50, "category_id": food.id}, headers=sh
    )
    assert r.status_code == 201
    got = client.get("/api/v1/notifications", headers=token(client, "b@x.af")).json()["items"]
    assert len(got) == 1 and got[0]["kind"] == "new_product" and got[0]["product_id"] == r.json()["id"]
    assert got[0]["title"] == "New in Food & Bakery" and "Qargha Shop just listed Naan for 10 AFN / piece" in got[0]["message"]
    for who in ("b2@x.af", "b3@x.af"):
        assert client.get("/api/v1/notifications", headers=token(client, who)).json()["items"] == []


def test_hidden_product_notifies_only_when_published(client, db):
    food, *_ = shop(db)
    client.put("/api/v1/me/interests", json={"category_ids": [food.id]}, headers=token(client, "b@x.af"))
    sh = token(client, "s@x.af")
    body = {"name": "Pie", "price_afn": "50.00", "unit": "piece", "stock_qty": 5, "category_id": food.id, "status": "hidden"}
    pid = client.post("/api/v1/products", json=body, headers=sh).json()["id"]
    assert client.get("/api/v1/notifications/unread-count", headers=token(client, "b@x.af")).json() == {"unread": 0}
    client.patch(f"/api/v1/products/{pid}", json={"status": "active"}, headers=sh)
    assert client.get("/api/v1/notifications/unread-count", headers=token(client, "b@x.af")).json() == {"unread": 1}
    client.patch(f"/api/v1/products/{pid}", json={"price_afn": "55.00"}, headers=sh)
    assert client.get("/api/v1/notifications/unread-count", headers=token(client, "b@x.af")).json() == {"unread": 1}
